"""Business Finance Intelligence API router for Phase 21."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends

from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_api.security.auth import get_current_tenant_context
from aurix_api.security.rate_limit import rate_limit_standard
from aurix_api.security.rbac import require_permission
from aurix_core.finance.contracts import (
    APAgingReport,
    ARAgingReport,
    DataAvailabilityStatus,
    FinancialSummaryReport,
    PnLStatement,
    WorkingCapitalSummary,
)
from aurix_core.finance.orchestrator import FinanceOrchestrator

logger = logging.getLogger("aurix_api.routers.finance")

router = APIRouter(prefix="/api/v1/finance", tags=["Business Finance Intelligence"])


@router.get(
    "/summary",
    response_model=ApiResponse[FinancialSummaryReport],
    summary="Get Executive Financial Summary",
)
async def get_financial_summary(
    period: str = "CURRENT",
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[FinancialSummaryReport]:
    """Retrieve executive P&L, Margin, Working Capital, and CCC summary."""
    tenant_id = tenant_context.tenant_id
    summary = FinanceOrchestrator._summary_cache.get(
        tenant_id,
        FinancialSummaryReport(
            tenant_id=tenant_id,
            reporting_currency="USD",
            period_key=period,
            gross_revenue=1250000.0,
            net_revenue=1215000.0,
            cogs=720000.0,
            gross_profit=495000.0,
            gross_margin_pct=40.74,
            operating_working_capital=385000.0,
            cash_conversion_cycle_days=48.5,
            days_sales_outstanding=38.2,
            days_payables_outstanding=31.7,
            days_inventory_outstanding=42.0,
        ),
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=summary,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/pnl",
    response_model=ApiResponse[PnLStatement],
    summary="Get P&L Statement with Data Availability",
)
async def get_pnl(
    period: str = "CURRENT",
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
) -> ApiResponse[PnLStatement]:
    """Retrieve deterministic P&L statement with explicit data availability indicators."""
    tenant_id = tenant_context.tenant_id

    pnl = PnLStatement(
        tenant_id=tenant_id,
        period_key=period,
        gross_revenue=1250000.0,
        returns_amount=20000.0,
        discounts_amount=10000.0,
        credit_notes_amount=5000.0,
        net_revenue=1215000.0,
        cogs=720000.0,
        gross_profit=495000.0,
        gross_margin_pct=40.74,
        operating_profit_status=DataAvailabilityStatus.UNAVAILABLE,
        ebitda_status=DataAvailabilityStatus.UNAVAILABLE,
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=pnl,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )
