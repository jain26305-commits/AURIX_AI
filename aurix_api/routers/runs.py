"""Run and job management router for Phase 10 Application API."""

import logging
from typing import Generator
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.runs import RunCreateRequest, RunListResponse, RunStatusResponse
from aurix_api.security.auth import get_current_tenant_context
from aurix_api.security.rbac import require_permission
from aurix_api.security.rate_limit import rate_limit_standard
from aurix_api.services.run_manager import RunManager
from aurix_core.database.engine import SessionLocal

logger = logging.getLogger("aurix_api.routers.runs")

router = APIRouter(prefix="/api/v1/runs", tags=["Runs & Job Management"])


def get_db() -> Generator[Session, None, None]:
    """Database session dependency yielding a managed SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "",
    response_model=ApiResponse[RunStatusResponse],
    summary="Submit Analytical Execution Run",
    description="Dispatches a synchronous or background intelligence run for the active tenant.",
)
async def create_run(
    payload: RunCreateRequest,
    background_tasks: BackgroundTasks,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.RUN_ANALYSIS)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[RunStatusResponse]:
    """Submits an execution run using RunManager."""
    tenant_id = tenant_context.tenant_id
    correlation_id = tenant_context.session_id or "REQ-UNKNOWN"

    run_response = RunManager.submit_run(
        db=db,
        tenant_id=tenant_id,
        request_data=payload,
        background_tasks=background_tasks,
        correlation_id=correlation_id,
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=run_response,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "",
    response_model=ApiResponse[RunListResponse],
    summary="List Execution Runs",
    description="Retrieves a paginated list of historical analytical execution runs.",
)
async def list_runs(
    limit: int = 50,
    offset: int = 0,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[RunListResponse]:
    """Lists historical runs for the active tenant."""
    tenant_id = tenant_context.tenant_id
    list_response = RunManager.list_runs(db=db, tenant_id=tenant_id, limit=limit, offset=offset)

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=list_response,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/{run_id}",
    response_model=ApiResponse[RunStatusResponse],
    summary="Get Run Status",
    description="Retrieves execution status and metadata for a specific run ID.",
)
async def get_run_status(
    run_id: str,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[RunStatusResponse]:
    """Retrieves specific run status, enforcing tenant isolation."""
    tenant_id = tenant_context.tenant_id
    run_status = RunManager.get_run_status(db=db, tenant_id=tenant_id, run_id=run_id)

    if not run_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run ID '{run_id}' not found for tenant '{tenant_id}'.",
        )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=run_status,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )