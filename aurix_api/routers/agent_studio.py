"""Enterprise Agent Studio REST API Router for Phase 30."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_api.security.auth import get_current_tenant_context
from aurix_api.security.rate_limit import rate_limit_standard
from aurix_api.security.rbac import require_permission
from aurix_core.database.engine import get_db
from aurix_core.studio.agent_builder import AgentBuilder
from aurix_core.studio.contracts import (
    ChangeImpactReport,
    DependencyGraphReport,
    DeploymentRecord,
    EnvironmentTier,
    StudioAgentDraft,
    StudioAgentVersion,
    StudioSummaryReport,
    StudioTemplate,
    StudioWorkflowDefinition,
    ValidationReport,
)
from aurix_core.studio.deployment_manager import DeploymentManager
from aurix_core.studio.dry_run_engine import StudioDryRunEngine
from aurix_core.studio.import_export import StudioImportExport
from aurix_core.studio.orchestrator import StudioOrchestrator
from aurix_core.studio.templates import TemplateCatalog
from aurix_core.studio.validator import StudioValidator
from aurix_core.studio.workflow_builder import WorkflowBuilder

logger = logging.getLogger("aurix_api.routers.agent_studio")

router = APIRouter(prefix="/api/v1/agent-studio", tags=["Enterprise Agent Studio"])


class PublishAgentDTO(BaseModel):
    published_by: str
    change_summary: str = ""


class DeployAgentDTO(BaseModel):
    agent_id: str
    version_number: str
    environment: EnvironmentTier
    deployed_by: str


class RollbackAgentDTO(BaseModel):
    agent_id: str
    target_version_number: str
    rolled_back_by: str


@router.get(
    "/summary",
    response_model=ApiResponse[StudioSummaryReport],
    summary="Get Panoramic Agent Studio Control Plane Summary",
)
async def get_studio_summary(
    period: str = "CURRENT",
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[StudioSummaryReport]:
    """Retrieve master control plane status, agent drafts, active deployments, and template counts."""
    tenant_id = tenant_context.tenant_id
    summary = StudioOrchestrator.run_studio_sweep(tenant_id=tenant_id, period_key=period, db=db)
    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=summary,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/agents",
    response_model=ApiResponse[List[StudioAgentDraft]],
    summary="List Studio Agent Definitions",
)
async def list_studio_agents(
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
) -> ApiResponse[List[StudioAgentDraft]]:
    """List all agent builder drafts and configurations."""
    agents = AgentBuilder.list_agents(tenant_id=tenant_context.tenant_id, db=db)
    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=agents,
        meta=ResponseMetadata(tenant_id=tenant_context.tenant_id),
    )


@router.post(
    "/agents",
    response_model=ApiResponse[StudioAgentDraft],
    summary="Create or Save Studio Agent Draft",
)
async def save_agent_draft(
    draft: StudioAgentDraft,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
) -> ApiResponse[StudioAgentDraft]:
    """Save an agent configuration draft."""
    draft.tenant_id = tenant_context.tenant_id
    saved = AgentBuilder.create_agent_draft(draft, db=db)
    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=saved,
        meta=ResponseMetadata(tenant_id=tenant_context.tenant_id),
    )


@router.post(
    "/agents/{agent_id}/publish",
    response_model=ApiResponse[StudioAgentVersion],
    summary="Publish Immutable Agent Version",
)
async def publish_agent_version(
    agent_id: str,
    payload: PublishAgentDTO,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
) -> ApiResponse[StudioAgentVersion]:
    """Publish an immutable version snapshot of an agent draft."""
    version = AgentBuilder.publish_agent_version(
        agent_id=agent_id,
        published_by=payload.published_by,
        change_summary=payload.change_summary,
        db=db,
    )
    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=version,
        meta=ResponseMetadata(tenant_id=tenant_context.tenant_id),
    )


@router.post(
    "/validate",
    response_model=ApiResponse[ValidationReport],
    summary="Validate Agent Draft and Blast Radius",
)
async def validate_agent_draft(
    draft: StudioAgentDraft,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
) -> ApiResponse[ValidationReport]:
    """Execute pre-publication static analysis and linter checks."""
    report = StudioValidator.validate_agent_draft(draft)
    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=report,
        meta=ResponseMetadata(tenant_id=tenant_context.tenant_id),
    )


@router.post(
    "/deploy",
    response_model=ApiResponse[DeploymentRecord],
    summary="Deploy Agent Version to Environment",
)
async def deploy_agent(
    payload: DeployAgentDTO,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.EXECUTE_ACTION)),
) -> ApiResponse[DeploymentRecord]:
    """Deploy agent version to DEV/TEST/PROD and sync with Phase 29 runtime."""
    record = DeploymentManager.deploy_agent_version(
        tenant_id=tenant_context.tenant_id,
        agent_id=payload.agent_id,
        version_number=payload.version_number,
        environment=payload.environment,
        deployed_by=payload.deployed_by,
        db=db,
    )
    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=record,
        meta=ResponseMetadata(tenant_id=tenant_context.tenant_id),
    )


@router.post(
    "/rollback",
    response_model=ApiResponse[DeploymentRecord],
    summary="Rollback Production Deployment",
)
async def rollback_agent(
    payload: RollbackAgentDTO,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.EXECUTE_ACTION)),
) -> ApiResponse[DeploymentRecord]:
    """Roll back production deployment to a previous published version."""
    record = DeploymentManager.rollback_deployment(
        tenant_id=tenant_context.tenant_id,
        agent_id=payload.agent_id,
        target_version_number=payload.target_version_number,
        rolled_back_by=payload.rolled_back_by,
        db=db,
    )
    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=record,
        meta=ResponseMetadata(tenant_id=tenant_context.tenant_id),
    )


@router.post(
    "/dry-run",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Execute Sandbox Workflow Dry Run",
)
async def dry_run_workflow(
    workflow: StudioWorkflowDefinition,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
) -> ApiResponse[Dict[str, Any]]:
    """Execute non-mutating preview simulation of a workflow."""
    result = StudioDryRunEngine.execute_dry_run(tenant_id=tenant_context.tenant_id, workflow=workflow)
    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=result,
        meta=ResponseMetadata(tenant_id=tenant_context.tenant_id),
    )


@router.get(
    "/templates",
    response_model=ApiResponse[List[StudioTemplate]],
    summary="List Pre-Governed Templates",
)
async def list_templates(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
) -> ApiResponse[List[StudioTemplate]]:
    """List reusable pre-governed agent and workflow templates."""
    templates = TemplateCatalog.list_templates()
    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=templates,
        meta=ResponseMetadata(tenant_id=tenant_context.tenant_id),
    )
