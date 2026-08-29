"""Continuous Assurance API router for Phase 20."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_api.security.auth import get_current_tenant_context
from aurix_api.security.rate_limit import rate_limit_standard
from aurix_api.security.rbac import require_permission
from aurix_core.assurance.contracts import (
    AssuranceFinding,
    AssuranceRunSummary,
    FindingStatus,
)
from aurix_core.assurance.leakage_quantifier import LeakageQuantifier
from aurix_core.assurance.orchestrator import AssuranceOrchestrator

logger = logging.getLogger("aurix_api.routers.assurance")

router = APIRouter(prefix="/api/v1/assurance", tags=["Continuous Assurance Engine"])


@router.get(
    "/findings",
    response_model=ApiResponse[List[AssuranceFinding]],
    summary="List Assurance Findings",
)
async def list_findings(
    domain: Optional[str] = None,
    severity: Optional[str] = None,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
) -> ApiResponse[List[AssuranceFinding]]:
    """Retrieve filtered assurance findings for the active tenant."""
    tenant_id = tenant_context.tenant_id
    findings = AssuranceOrchestrator.get_findings(tenant_id, domain=domain, severity=severity)

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=findings,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/metrics",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get Financial Leakage Metrics",
)
async def get_assurance_metrics(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
) -> ApiResponse[Dict[str, Any]]:
    """Return consolidated commercial leakage metrics for the active tenant."""
    tenant_id = tenant_context.tenant_id
    findings = AssuranceOrchestrator.get_findings(tenant_id)
    quant = LeakageQuantifier.quantify(tenant_id, findings)

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=quant,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )
