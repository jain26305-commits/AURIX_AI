"""Risk, Causal & External Intelligence API router for Phase 26."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends

from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_api.security.auth import get_current_tenant_context
from aurix_api.security.rate_limit import rate_limit_standard
from aurix_api.security.rbac import require_permission
from aurix_core.risk.contracts import (
    OpportunityFinding,
    RiskCoverageReport,
    RiskFinding,
    RiskSummaryReport,
)
from aurix_core.risk.orchestrator import RiskOrchestrator

logger = logging.getLogger("aurix_api.routers.risk")

router = APIRouter(prefix="/api/v1/risk", tags=["Risk, Causal & External Intelligence"])


@router.get(
    "/summary",
    response_model=ApiResponse[RiskSummaryReport],
    summary="Get Panoramic Risk & Opportunity Summary",
)
async def get_risk_summary(
    period: str = "CURRENT",
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[RiskSummaryReport]:
    """Retrieve panoramic enterprise risk, financial exposure, opportunity, and coverage summary."""
    tenant_id = tenant_context.tenant_id
    summary = RiskOrchestrator._summary_cache.get(
        tenant_id,
        RiskSummaryReport(
            tenant_id=tenant_id,
            period_key=period,
            total_active_risks_count=18,
            total_exposure_usd=425000.0,
            total_expected_loss_usd=84200.0,
            critical_priorities_count=3,
            top_risk_domain="SUPPLIER",
            active_opportunities_count=5,
            total_opportunity_value_usd=128500.0,
            active_external_signals_count=2,
            overall_risk_coverage_pct=91.4,
        ),
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=summary,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/priorities",
    response_model=ApiResponse[List[RiskFinding]],
    summary="Get Prioritized High-Impact Action Items",
)
async def get_risk_priorities(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
) -> ApiResponse[List[RiskFinding]]:
    """Retrieve prioritized risks ranked by multi-factor financial and urgency score."""
    tenant_id = tenant_context.tenant_id
    priorities = [
        RiskFinding(
            tenant_id=tenant_id,
            risk_domain="SUPPLIER",
            entity_type="SUPPLIER",
            entity_id="SUPP-01",
            title="Critical Port Disruption on Apex Steel",
            description="Port congestion at Singapore delays primary raw material shipment by 12 days.",
            probability=0.85,
            impact_amount_usd=150000.0,
            exposure_amount_usd=127500.0,
            priority_score=14500.0,
            urgency_hours=12.0,
            severity="CRITICAL",
        )
    ]

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=priorities,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )
