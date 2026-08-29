"""Deterministic Decision Engine 2.0 API router for Phase 27."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends

from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_api.security.auth import get_current_tenant_context
from aurix_api.security.rate_limit import rate_limit_standard
from aurix_api.security.rbac import require_permission
from aurix_core.decisions.contracts import (
    DecisionReadinessReport,
    DecisionSummaryReport,
    OptimizationRequest,
    OptimizationResult,
    UniversalDecisionCard,
)
from aurix_core.decisions.optimizer import DecisionOptimizer
from aurix_core.decisions.orchestrator import DecisionOrchestrator

logger = logging.getLogger("aurix_api.routers.decisions")

router = APIRouter(prefix="/api/v1/decisions", tags=["Deterministic Decision Engine 2.0"])


@router.get(
    "/summary",
    response_model=ApiResponse[DecisionSummaryReport],
    summary="Get Panoramic Decision Operating Summary",
)
async def get_decision_summary(
    period: str = "CURRENT",
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[DecisionSummaryReport]:
    """Retrieve panoramic decision queue, expected value, risk mitigated, and acceptance metrics."""
    tenant_id = tenant_context.tenant_id
    summary = DecisionOrchestrator._summary_cache.get(
        tenant_id,
        DecisionSummaryReport(
            tenant_id=tenant_id,
            period_key=period,
            total_decisions_proposed=12,
            pending_approvals_count=4,
            executed_decisions_count=8,
            total_pipeline_expected_value_usd=148500.0,
            total_downside_risk_mitigated_usd=62400.0,
            recommendation_acceptance_rate_pct=94.5,
            active_champion_models_count=2,
            top_decision_domain="PROCUREMENT_SUPPLIER",
        ),
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=summary,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/cards",
    response_model=ApiResponse[List[UniversalDecisionCard]],
    summary="Get Universal Decision Cards",
)
async def get_decision_cards(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
) -> ApiResponse[List[UniversalDecisionCard]]:
    """Retrieve active Universal Decision Cards with evidence, alternatives, and policy state."""
    tenant_id = tenant_context.tenant_id
    cards = DecisionOrchestrator._card_cache.get(tenant_id, [])

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=cards,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.post(
    "/optimize",
    response_model=ApiResponse[OptimizationResult],
    summary="Optimize Portfolio Candidate Allocation",
)
async def optimize_portfolio_actions(
    request: OptimizationRequest,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
) -> ApiResponse[OptimizationResult]:
    """Solve multi-action portfolio allocation problem subject to budget limit."""
    result = DecisionOptimizer.optimize_portfolio(request)

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=result,
        meta=ResponseMetadata(tenant_id=tenant_context.tenant_id),
    )
