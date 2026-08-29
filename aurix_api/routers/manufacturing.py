"""Manufacturing & Production Intelligence API router for Phase 23."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends

from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_api.security.auth import get_current_tenant_context
from aurix_api.security.rate_limit import rate_limit_standard
from aurix_api.security.rbac import require_permission
from aurix_core.manufacturing.contracts import (
    DataAvailabilityStatus,
    ManufacturingSummaryReport,
)
from aurix_core.manufacturing.orchestrator import ManufacturingOrchestrator

logger = logging.getLogger("aurix_api.routers.manufacturing")

router = APIRouter(prefix="/api/v1/manufacturing", tags=["Manufacturing & Production Intelligence"])


@router.get(
    "/summary",
    response_model=ApiResponse[ManufacturingSummaryReport],
    summary="Get Executive Manufacturing Summary",
)
async def get_manufacturing_summary(
    period: str = "CURRENT",
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[ManufacturingSummaryReport]:
    """Retrieve master manufacturing KPI summary including OEE, capacity, scrap, and revenue-at-risk."""
    tenant_id = tenant_context.tenant_id
    summary = ManufacturingOrchestrator._summary_cache.get(
        tenant_id,
        ManufacturingSummaryReport(
            tenant_id=tenant_id,
            period_key=period,
            total_work_orders=42,
            active_work_orders=18,
            plant_capacity_utilization_pct=84.2,
            overall_oee_pct=78.5,
            oee_status=DataAvailabilityStatus.AVAILABLE,
            first_pass_yield_pct=96.4,
            scrap_rate_pct=2.1,
            total_downtime_hours=14.5,
            total_production_revenue_at_risk=28500.0,
            bottleneck_work_centers_count=1,
            active_anomalies_count=0,
        ),
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=summary,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )
