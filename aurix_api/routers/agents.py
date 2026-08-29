"""Governed Autonomous Agents API router for Phase 29."""

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
from aurix_core.agents.contracts import (
    AgentDefinition,
    AgentStatus,
    AgentSummaryReport,
    ApprovalRequest,
    ExecutionJournalRecord,
    ExecutionPlan,
    SkillDefinition,
    ToolDefinition,
    ValueNetworkRecord,
)
from aurix_core.agents.governance_gate import GovernanceGate
from aurix_core.agents.orchestrator import AgentOrchestrator
from aurix_core.agents.planning import AgentPlanner
from aurix_core.agents.runtime import AgentRuntime
from aurix_core.agents.skills import SkillRegistry
from aurix_core.agents.tools import ToolRegistry
from aurix_core.database.engine import get_db

logger = logging.getLogger("aurix_api.routers.agents")

router = APIRouter(prefix="/api/v1/agents", tags=["Governed Autonomous Agents"])


class ApprovalDecisionDTO(BaseModel):
    approved: bool
    approver_id: str
    reason: str = ""


class DispatchExecutionDTO(BaseModel):
    agent_id: str
    objective: str
    target_skill: str
    target_tool: str
    is_dry_run: bool = False


@router.get(
    "/summary",
    response_model=ApiResponse[AgentSummaryReport],
    summary="Get Panoramic Agent Operating Summary",
)
async def get_agent_summary(
    period: str = "CURRENT",
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[AgentSummaryReport]:
    """Retrieve panoramic agent runtime status, success rates, pending approvals, and value realization."""
    tenant_id = tenant_context.tenant_id
    summary = AgentOrchestrator.run_agent_sweep(tenant_id=tenant_id, period_key=period, db=db)

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=summary,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "",
    response_model=ApiResponse[List[AgentDefinition]],
    summary="List Registered Enterprise Agents",
)
async def list_agents(
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
) -> ApiResponse[List[AgentDefinition]]:
    """List all registered agent specifications."""
    agents = AgentRuntime.list_agents(db=db)
    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=agents,
        meta=ResponseMetadata(tenant_id=tenant_context.tenant_id),
    )


@router.post(
    "/{agent_id}/pause",
    response_model=ApiResponse[AgentDefinition],
    summary="Pause Autonomous Agent Execution",
)
async def pause_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
) -> ApiResponse[AgentDefinition]:
    """Pause an agent's autonomous execution capability."""
    agent = AgentRuntime.get_agent(agent_id, db=db)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.status = AgentStatus.PAUSED
    AgentRuntime.register_agent(agent, db=db)
    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=agent,
        meta=ResponseMetadata(tenant_id=tenant_context.tenant_id),
    )


@router.post(
    "/{agent_id}/resume",
    response_model=ApiResponse[AgentDefinition],
    summary="Resume Autonomous Agent Execution",
)
async def resume_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
) -> ApiResponse[AgentDefinition]:
    """Resume a paused agent."""
    agent = AgentRuntime.get_agent(agent_id, db=db)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.status = AgentStatus.ACTIVE
    AgentRuntime.register_agent(agent, db=db)
    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=agent,
        meta=ResponseMetadata(tenant_id=tenant_context.tenant_id),
    )


@router.get(
    "/skills",
    response_model=ApiResponse[List[SkillDefinition]],
    summary="List Governed Skill Registry",
)
async def list_skills(
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
) -> ApiResponse[List[SkillDefinition]]:
    """List all available enterprise skills."""
    skills = SkillRegistry.list_skills(db=db)
    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=skills,
        meta=ResponseMetadata(tenant_id=tenant_context.tenant_id),
    )


@router.post(
    "/executions/dispatch",
    response_model=ApiResponse[ExecutionJournalRecord],
    summary="Dispatch Governed Agent Execution",
)
async def dispatch_execution(
    payload: DispatchExecutionDTO,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.EXECUTE_ACTION)),
) -> ApiResponse[ExecutionJournalRecord]:
    """Dispatch an autonomous execution through all governance gates."""
    tenant_id = tenant_context.tenant_id
    agent = AgentRuntime.get_agent(payload.agent_id, db=db)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    plan = AgentPlanner.create_plan(
        tenant_id=tenant_id,
        agent=agent,
        objective=payload.objective,
        target_skill=payload.target_skill,
        target_tool=payload.target_tool,
        is_dry_run=payload.is_dry_run,
    )

    idem_key = GovernanceGate.generate_idempotency_key(tenant_id, agent.agent_id, plan.plan_id)
    record = AgentRuntime.execute_plan_sequential(tenant_id, agent, plan, idem_key, db=db)

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=record,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.post(
    "/approvals/{approval_id}/decision",
    response_model=ApiResponse[ApprovalRequest],
    summary="Submit Manager Approval Decision",
)
async def submit_approval_decision(
    approval_id: str,
    payload: ApprovalDecisionDTO,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.APPROVE_ACTION)),
) -> ApiResponse[ApprovalRequest]:
    """Process human manager approval or rejection."""
    req = AgentOrchestrator.process_approval(
        approval_id=approval_id,
        approved=payload.approved,
        approver_id=payload.approver_id,
        reason=payload.reason,
        db=db,
    )
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=req,
        meta=ResponseMetadata(tenant_id=tenant_context.tenant_id),
    )
