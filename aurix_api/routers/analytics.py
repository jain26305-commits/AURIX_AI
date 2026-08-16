"""Domain analytics read router for Phase 10 Application API."""

import json
import logging
from typing import Any, Dict, Generator, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from aurix_api.schemas.analytics import (
    DemandAnalyticsResponse,
    EconomicsAnalyticsResponse,
    ForecastAnalyticsResponse,
    InventoryAnalyticsResponse,
    LogisticsAnalyticsResponse,
    NetworkAnalyticsResponse,
    SupplyAnalyticsResponse,
)
from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_api.security.auth import get_current_tenant_context
from aurix_api.security.rate_limit import rate_limit_standard
from aurix_api.security.rbac import require_permission
from aurix_core.database.engine import SessionLocal
from aurix_core.database.repositories.intelligence import IntelligenceSnapshotRepository

logger = logging.getLogger("aurix_api.routers.analytics")

router = APIRouter(prefix="/api/v1", tags=["Domain Analytics"])


def get_db() -> Generator[Session, None, None]:
    """Database session dependency yielding a managed SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_latest_snapshot_data(db: Session, tenant_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves the latest persisted intelligence snapshot JSON for the tenant."""
    try:
        repo = IntelligenceSnapshotRepository(db, tenant_id)
        snap = repo.get_latest_snapshot()
        if snap and getattr(snap, "snapshot_json", None):
            raw_json = str(snap.snapshot_json)
            parsed: Dict[str, Any] = json.loads(raw_json) if raw_json else {}
            return parsed
    except Exception as e:
        logger.warning("Error fetching snapshot data for tenant [%s]: %s", tenant_id, str(e))
        return None
    return None


@router.get(
    "/demand",
    response_model=ApiResponse[DemandAnalyticsResponse],
    summary="Get Demand Analytics",
    description="Returns demand classification, ADI/CV2 variance, and intermittency profiles.",
)
async def get_demand_analytics(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[DemandAnalyticsResponse]:
    """Exposes demand classification analytics for the tenant."""
    tenant_id = tenant_context.tenant_id
    snap_data = _get_latest_snapshot_data(db, tenant_id)

    classified_skus: Dict[str, Any] = {}
    if snap_data and "demand_classification" in snap_data:
        classified_skus = snap_data["demand_classification"].get("classified_skus", {})

    payload = DemandAnalyticsResponse(
        status="COMPUTED",
        classified_skus=classified_skus,
        total_skus=len(classified_skus),
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=payload,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/forecast",
    response_model=ApiResponse[ForecastAnalyticsResponse],
    summary="Get Demand Forecasts",
    description="Returns point forecasts, confidence intervals, and selected smoothing models.",
)
async def get_forecast_analytics(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[ForecastAnalyticsResponse]:
    """Exposes forecasting analytics for the tenant."""
    tenant_id = tenant_context.tenant_id
    snap_data = _get_latest_snapshot_data(db, tenant_id)

    forecasts: Dict[str, Any] = {}
    if snap_data and "demand_forecasting" in snap_data:
        forecasts = snap_data["demand_forecasting"].get("sku_forecasts", {})

    payload = ForecastAnalyticsResponse(
        status="COMPUTED",
        sku_forecasts=forecasts,
        total_forecasts=len(forecasts),
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=payload,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/inventory",
    response_model=ApiResponse[InventoryAnalyticsResponse],
    summary="Get Inventory Policies & Risk",
    description="Returns safety stock levels, reorder points, coverage days, and stockout risk evaluations.",
)
async def get_inventory_analytics(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[InventoryAnalyticsResponse]:
    """Exposes inventory policies and position risks for the tenant."""
    tenant_id = tenant_context.tenant_id
    snap_data = _get_latest_snapshot_data(db, tenant_id)

    policies: Dict[str, Any] = {}
    risks: Dict[str, Any] = {}
    high_risk_count = 0

    if snap_data:
        if "safety_stock_rop" in snap_data:
            policies = snap_data["safety_stock_rop"].get("inventory_policies", {})
        if "inventory_position_risk" in snap_data:
            risk_payload = snap_data["inventory_position_risk"]
            risks = risk_payload.get("risk_evaluations", {})
            high_risk_count = int(risk_payload.get("high_risk_skus_count", 0))

    payload = InventoryAnalyticsResponse(
        status="COMPUTED",
        inventory_policies=policies,
        risk_evaluations=risks,
        high_risk_skus_count=high_risk_count,
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=payload,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/supply",
    response_model=ApiResponse[SupplyAnalyticsResponse],
    summary="Get Supply & Vendor Analytics",
    description="Returns supplier OTD performance metrics, risk tiers, and supplier selection rankings.",
)
async def get_supply_analytics(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[SupplyAnalyticsResponse]:
    """Exposes supplier performance and selection rankings for the tenant."""
    tenant_id = tenant_context.tenant_id
    snap_data = _get_latest_snapshot_data(db, tenant_id)

    performance: Dict[str, Any] = {}
    rankings: Dict[str, Any] = {}
    high_risk_supp = 0

    if snap_data:
        if "supplier_performance_risk" in snap_data:
            sp_payload = snap_data["supplier_performance_risk"]
            performance = sp_payload.get("supplier_performance", {})
            high_risk_supp = int(sp_payload.get("high_risk_suppliers_count", 0))
        if "supplier_selection" in snap_data:
            rankings = snap_data["supplier_selection"].get("supplier_rankings", {})

    payload = SupplyAnalyticsResponse(
        status="COMPUTED",
        supplier_performance=performance,
        supplier_rankings=rankings,
        high_risk_suppliers_count=high_risk_supp,
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=payload,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/logistics",
    response_model=ApiResponse[LogisticsAnalyticsResponse],
    summary="Get Logistics & Shipment Tracking",
    description="Returns active shipment tracking statuses, dynamic ETAs, and delay metrics.",
)
async def get_logistics_analytics(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[LogisticsAnalyticsResponse]:
    """Exposes shipment tracking and logistics ETAs for the tenant."""
    tenant_id = tenant_context.tenant_id
    snap_data = _get_latest_snapshot_data(db, tenant_id)

    shipments: Dict[str, Any] = {}
    delayed_count = 0

    if snap_data and "shipment_tracking_eta" in snap_data:
        log_payload = snap_data["shipment_tracking_eta"]
        shipments = log_payload.get("shipments", {})
        delayed_count = int(log_payload.get("delayed_shipments_count", 0))

    payload = LogisticsAnalyticsResponse(
        status="COMPUTED",
        shipments=shipments,
        delayed_shipments_count=delayed_count,
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=payload,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/network",
    response_model=ApiResponse[NetworkAnalyticsResponse],
    summary="Get Network Topology & Rebalancing",
    description="Returns facility bottleneck analytics and lateral inventory rebalancing recommendations.",
)
async def get_network_analytics(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[NetworkAnalyticsResponse]:
    """Exposes network topology bottlenecks and rebalancing proposals for the tenant."""
    tenant_id = tenant_context.tenant_id
    snap_data = _get_latest_snapshot_data(db, tenant_id)

    nodes: Dict[str, Any] = {}
    bottlenecks = 0
    rebalancing: List[Dict[str, Any]] = []

    if snap_data:
        if "network_topology_bottleneck" in snap_data:
            net_payload = snap_data["network_topology_bottleneck"]
            nodes = net_payload.get("network_nodes", {})
            bottlenecks = int(net_payload.get("network_bottlenecks_count", 0))
        if "inventory_rebalancing" in snap_data:
            rebalancing = snap_data["inventory_rebalancing"].get("rebalancing_recommendations", [])

    payload = NetworkAnalyticsResponse(
        status="COMPUTED",
        network_nodes=nodes,
        network_bottlenecks_count=bottlenecks,
        rebalancing_recommendations=rebalancing,
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=payload,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/economics",
    response_model=ApiResponse[EconomicsAnalyticsResponse],
    summary="Get Working Capital & Economics",
    description="Returns total cost of ownership, portfolio working capital, holding costs, and scenario simulations.",
)
async def get_economics_analytics(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.VIEW_FINANCIALS)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[EconomicsAnalyticsResponse]:
    """Exposes financial working capital and economic analytics for the tenant."""
    tenant_id = tenant_context.tenant_id
    snap_data = _get_latest_snapshot_data(db, tenant_id)

    wc = 0.0
    holding = 0.0
    curr = "USD"
    sku_fin: Dict[str, Any] = {}
    scenarios: Dict[str, Any] = {}

    if snap_data:
        if "working_capital_tco" in snap_data:
            wc_payload = snap_data["working_capital_tco"]
            wc = float(wc_payload.get("portfolio_working_capital", 0.0))
            holding = float(wc_payload.get("portfolio_annual_holding_cost", 0.0))
            curr = str(wc_payload.get("currency", "USD"))
            sku_fin = wc_payload.get("sku_financials", {})
        if "scenario_simulation" in snap_data:
            scenarios = snap_data["scenario_simulation"].get("scenarios_evaluated", {})

    payload = EconomicsAnalyticsResponse(
        status="COMPUTED",
        portfolio_working_capital=wc,
        portfolio_annual_holding_cost=holding,
        currency=curr,
        sku_financials=sku_fin,
        scenarios_evaluated=scenarios,
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=payload,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )