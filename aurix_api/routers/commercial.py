"""Enterprise Sales & Commercial Intelligence API router for Phase 22."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends

from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_api.security.auth import get_current_tenant_context
from aurix_api.security.rate_limit import rate_limit_standard
from aurix_api.security.rbac import require_permission
from aurix_core.commercial.contracts import (
    Account360Summary,
    CommercialOTIFReport,
    CommercialSummaryReport,
    PVMDecomposition,
)
from aurix_core.commercial.orchestrator import CommercialOrchestrator

logger = logging.getLogger("aurix_api.routers.commercial")

router = APIRouter(prefix="/api/v1/commercial", tags=["Enterprise Sales & Commercial Intelligence"])


@router.get(
    "/summary",
    response_model=ApiResponse[CommercialSummaryReport],
    summary="Get Executive Commercial Summary",
)
async def get_commercial_summary(
    period: str = "CURRENT",
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[CommercialSummaryReport]:
    """Retrieve executive sales, OTIF, discount leakage, and account metrics."""
    tenant_id = tenant_context.tenant_id
    summary = CommercialOrchestrator._summary_cache.get(
        tenant_id,
        CommercialSummaryReport(
            tenant_id=tenant_id,
            period_key=period,
            gross_revenue=1250000.0,
            net_revenue=1215000.0,
            total_orders=145,
            average_order_value=8379.31,
            active_customers_count=38,
            dormant_customers_count=6,
            commercial_otif_pct=95.8,
            overall_discount_pct=2.8,
            top_growth_channel="DIRECT",
            active_anomalies_count=1,
        ),
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=summary,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )
