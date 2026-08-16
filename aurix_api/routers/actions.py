"""Controlled Decision Execution and Action Lifecycle API Router for Phase 14."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from aurix_api.routers.health import get_db
from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_api.security.auth import get_current_tenant_context
from aurix_api.security.rate_limit import rate_limit_standard
from aurix_api.security.rbac import require_permission
from aurix_core.actions.contracts import ActionCategory, ActionContract, ActionType
from aurix_core.actions.executor import ActionExecutor

logger = logging.getLogger("aurix_api.routers.actions")

router = APIRouter(prefix="/api/v1", tags=["Controlled Decision Execution & Actions"])


class ActionCreationRequest(BaseModel):
    """Payload for creating a new operational action."""
    action_type: ActionType
    action_category: ActionCategory
    entity_type: str
    entity_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    recommendation_id: Optional[str] = None
    source_run_id: Optional[str] = None
    capability_name: Optional[str] = None


class ApprovalRequest(BaseModel):
    """Payload for approving or rejecting an action."""
    comments: Optional[str] = None


class ExecutionRequest(BaseModel):
    """Payload for executing an approved action."""
    dry_run: bool = Field(default=False, description="If true, executes preflight simulation without external writes.")


@router.post(
    "/actions",
    response_model=ApiResponse[ActionContract],
    summary="Create Operational Action",
    description="Creates a new operational action candidate from recommendations or manual input.",
)
async def create_action(
    req: ActionCreationRequest,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[ActionContract]:
    """Creates a new structured action contract within tenant boundaries."""
    tenant_id = tenant_context.tenant_id
    actor_id = tenant_context.user_id

    action = ActionExecutor.create_action(
        tenant_id=tenant_id,
        action_type=req.action_type,
        action_category=req.action_category,
        entity_type=req.entity_type,
        entity_id=req.entity_id,
        requested_by=actor_id,
        payload=req.payload,
        recommendation_id=req.recommendation_id,
        source_run_id=req.source_run_id,
        capability_name=req.capability_name,
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=action,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.post(
    "/actions/{action_id}/preflight",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Run Preflight Policy Check",
    description="Evaluates fresh data rules, financial limits, and policy compliance for an action.",
)
async def preflight_action(
    action_id: str,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.RUN_ANALYSIS)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[Dict[str, Any]]:
    """Executes preflight policy validation on an action."""
    tenant_id = tenant_context.tenant_id
    actor_id = tenant_context.user_id
    actor_roles = [r.value for r in tenant_context.roles]

    try:
        allowed, msg, policy_res = ActionExecutor.preflight_action(db, tenant_id, action_id, actor_id, actor_roles)
        action = ActionExecutor._get_action_or_raise(tenant_id, action_id)

        return ApiResponse(
            status=ResponseStatus.SUCCESS if allowed else ResponseStatus.FAILED,
            data={
                "action_id": action_id,
                "allowed": allowed,
                "message": msg,
                "execution_state": action.execution_state.value,
                "approval_state": action.approval_state.value,
                "policy_evaluation": policy_res.model_dump() if policy_res else {},
            },
            meta=ResponseMetadata(tenant_id=tenant_id),
        )
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action '{action_id}' not found.")


@router.post(
    "/actions/{action_id}/approve",
    response_model=ApiResponse[ActionContract],
    summary="Approve Operational Action",
    description="Grants human approval for an action pending review.",
)
async def approve_action(
    action_id: str,
    req: ApprovalRequest,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.APPROVE_ACTION)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[ActionContract]:
    """Approves an action securely within tenant boundaries."""
    tenant_id = tenant_context.tenant_id
    approver_id = tenant_context.user_id
    approver_role = tenant_context.roles[0].value if tenant_context.roles else "ADMIN"

    try:
        action = ActionExecutor.approve_action(db, tenant_id, action_id, approver_id, approver_role, req.comments)
        return ApiResponse(
            status=ResponseStatus.SUCCESS,
            data=action,
            meta=ResponseMetadata(tenant_id=tenant_id),
        )
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action '{action_id}' not found.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/actions/{action_id}/reject",
    response_model=ApiResponse[ActionContract],
    summary="Reject Operational Action",
    description="Rejects an action pending review.",
)
async def reject_action(
    action_id: str,
    req: ApprovalRequest,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.APPROVE_ACTION)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[ActionContract]:
    """Rejects an action securely within tenant boundaries."""
    tenant_id = tenant_context.tenant_id
    approver_id = tenant_context.user_id
    approver_role = tenant_context.roles[0].value if tenant_context.roles else "ADMIN"

    try:
        action = ActionExecutor.reject_action(db, tenant_id, action_id, approver_id, approver_role, req.comments)
        return ApiResponse(
            status=ResponseStatus.SUCCESS,
            data=action,
            meta=ResponseMetadata(tenant_id=tenant_id),
        )
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action '{action_id}' not found.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/actions/{action_id}/execute",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Execute Operational Action",
    description="Dispatches an approved action through Phase 12 execution adapters.",
)
async def execute_action(
    action_id: str,
    req: ExecutionRequest,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.EXECUTE_ACTION)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[Dict[str, Any]]:
    """Executes an operational action securely within tenant boundaries."""
    tenant_id = tenant_context.tenant_id
    executor_id = tenant_context.user_id
    executor_roles = [r.value for r in tenant_context.roles]

    try:
        res = ActionExecutor.execute_action(db, tenant_id, action_id, executor_id, executor_roles, dry_run=req.dry_run)
        return ApiResponse(
            status=ResponseStatus.SUCCESS if res.success else ResponseStatus.FAILED,
            data=res.model_dump(),
            meta=ResponseMetadata(tenant_id=tenant_id),
        )
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action '{action_id}' not found.")


@router.get(
    "/actions/{action_id}/audit",
    response_model=ApiResponse[List[Dict[str, Any]]],
    summary="Inspect Action Audit Trail",
    description="Returns the immutable state transition audit log for an action.",
)
async def get_action_audit(
    action_id: str,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.VIEW_ACTION_AUDIT)),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[List[Dict[str, Any]]]:
    """Exposes immutable action audit records within tenant boundaries."""
    tenant_id = tenant_context.tenant_id
    audit_records = ActionExecutor._AUDIT_STORE.get(tenant_id, [])
    filtered = [rec.model_dump() for rec in audit_records if rec.action_id == action_id]

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=filtered,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )