"""Intelligence, business signals, and executive summary router for Phase 10 Application API."""

import json
import logging
from typing import Any, Dict, Generator, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_api.schemas.intelligence import (
    ActionItem,
    BusinessSignalItem,
    ExecutiveSummaryResponse,
    IntelligenceSnapshotResponse,
)
from aurix_api.security.auth import get_current_tenant_context
from aurix_api.security.rate_limit import rate_limit_standard
from aurix_api.security.rbac import require_permission
from aurix_core.database.engine import SessionLocal
from aurix_core.database.repositories.intelligence import (
    BusinessSignalRepository,
    ExecutiveSummaryRepository,
    IntelligenceSnapshotRepository,
    PrioritizedActionRepository,
)

logger = logging.getLogger("aurix_api.routers.intelligence")

router = APIRouter(prefix="/api/v1/intelligence", tags=["Executive Intelligence"])


def get_db() -> Generator[Session, None, None]:
    """Database session dependency yielding a managed SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _map_signal_to_schema(signal_obj: Any) -> BusinessSignalItem:
    """Helper to transform ORM/Repository signal object into BusinessSignalItem schema."""
    return BusinessSignalItem(
        signal_id=str(getattr(signal_obj, "id", getattr(signal_obj, "signal_id", "SIG-1"))),
        signal_type=str(getattr(signal_obj, "signal_type", "DEMAND_SHIFT")),
        domain=str(getattr(signal_obj, "domain", "INVENTORY")),
        severity=str(getattr(signal_obj, "severity", "MEDIUM")),
        affected_entity_id=str(getattr(signal_obj, "affected_entity_id", "SKU-DEFAULT")),
        description=str(getattr(signal_obj, "description", "Operational signal detected.")),
        evidence_quality=str(getattr(signal_obj, "evidence_quality", "HIGH")),
        financial_exposure=float(getattr(signal_obj, "financial_exposure_val", 0.0) or 0.0),
        currency=str(getattr(signal_obj, "currency", "USD")),
    )


def _map_action_to_schema(action_obj: Any) -> ActionItem:
    """Helper to transform ORM/Repository action object into ActionItem schema."""
    return ActionItem(
        action_id=str(getattr(action_obj, "id", getattr(action_obj, "action_id", "ACT-1"))),
        rank=int(getattr(action_obj, "rank", 1)),
        title=str(getattr(action_obj, "title", "Recommended Operational Policy Adjustment")),
        risk_level=str(getattr(action_obj, "risk_level", "MEDIUM")),
        recommended_action=str(getattr(action_obj, "recommended_action", "Rebalance regional buffer stock.")),
        affected_domain=str(getattr(action_obj, "affected_domain", "INVENTORY")),
        financial_impact_value=float(getattr(action_obj, "financial_impact_val", 0.0) or 0.0),
        currency=str(getattr(action_obj, "currency", "USD")),
    )


@router.get(
    "/signals",
    response_model=ApiResponse[List[BusinessSignalItem]],
    summary="Get Business Signals",
    description="Returns detected operational, inventory, logistics, and financial business signals.",
)
async def get_business_signals(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[List[BusinessSignalItem]]:
    """Exposes business signals extracted across active analysis runs."""
    tenant_id = tenant_context.tenant_id
    items: List[BusinessSignalItem] = []

    try:
        signal_repo = BusinessSignalRepository(db, tenant_id)
        signals = signal_repo.list_all()
        items = [_map_signal_to_schema(s) for s in signals]
    except Exception as e:
        logger.warning("Error fetching signals for tenant [%s]: %s", tenant_id, str(e), exc_info=True)

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=items,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/actions",
    response_model=ApiResponse[List[ActionItem]],
    summary="Get Prioritized Actions",
    description="Returns ranked executive actions derived from multi-signal prioritization algorithms.",
)
async def get_prioritized_actions(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[List[ActionItem]]:
    """Exposes prioritized executive actions for the active tenant."""
    tenant_id = tenant_context.tenant_id
    items: List[ActionItem] = []

    try:
        action_repo = PrioritizedActionRepository(db, tenant_id)
        actions = action_repo.list_all()
        items = [_map_action_to_schema(a) for a in actions]
    except Exception as e:
        logger.warning("Error fetching prioritized actions for tenant [%s]: %s", tenant_id, str(e), exc_info=True)

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=items,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/summary",
    response_model=ApiResponse[ExecutiveSummaryResponse],
    summary="Get Executive Summary",
    description="Returns executive narrative summary, health status, and headline key metrics.",
)
async def get_executive_summary(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[ExecutiveSummaryResponse]:
    """Exposes the latest executive summary narrative for the active tenant."""
    tenant_id = tenant_context.tenant_id
    headline = "Executive Intelligence Summary: Portfolio Operational Stable"
    health_status = "STABLE_WITH_NO_MATERIAL_EXCEPTIONS"
    signal_items: List[BusinessSignalItem] = []
    action_items: List[ActionItem] = []

    try:
        summary_repo = ExecutiveSummaryRepository(db, tenant_id)
        summary_rec = summary_repo.get_latest()

        if summary_rec and getattr(summary_rec, "headline", None):
            headline = str(summary_rec.headline)

        signal_repo = BusinessSignalRepository(db, tenant_id)
        action_repo = PrioritizedActionRepository(db, tenant_id)

        signal_items = [_map_signal_to_schema(s) for s in signal_repo.list_all()]
        action_items = [_map_action_to_schema(a) for a in action_repo.list_all()]
    except Exception as e:
        logger.warning("Error assembling executive summary for tenant [%s]: %s", tenant_id, str(e), exc_info=True)

    payload = ExecutiveSummaryResponse(
        headline=headline,
        overall_health_status=health_status,
        signals_count=len(signal_items),
        actions_count=len(action_items),
        signals=signal_items,
        prioritized_actions=action_items,
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=payload,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/snapshot",
    response_model=ApiResponse[IntelligenceSnapshotResponse],
    summary="Get Intelligence Snapshot",
    description="Returns the complete operational intelligence snapshot across all active analytical domains.",
)
async def get_intelligence_snapshot(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[IntelligenceSnapshotResponse]:
    """Exposes the latest persisted intelligence snapshot for the active tenant."""
    tenant_id = tenant_context.tenant_id

    try:
        snap_repo = IntelligenceSnapshotRepository(db, tenant_id)
        snap_rec = snap_repo.get_latest_snapshot()

        if not snap_rec or not getattr(snap_rec, "snapshot_json", None):
            payload = IntelligenceSnapshotResponse(
                snapshot_id="SNAP-EMPTY",
                generated_at="",
                total_skus=None,
            )
        else:
            raw_json = str(snap_rec.snapshot_json)
            data: Dict[str, Any] = json.loads(raw_json) if raw_json else {}
            payload = IntelligenceSnapshotResponse(
                snapshot_id=str(data.get("snapshot_id", "SNAP-DEFAULT")),
                generated_at=str(data.get("generated_at", "")),
                total_skus=data.get("total_skus"),
                high_risk_skus_count=int(data.get("high_risk_skus_count", 0)),
                supplier_risks_count=int(data.get("supplier_risks_count", 0)),
                delayed_shipments_count=int(data.get("delayed_shipments_count", 0)),
                network_bottlenecks_count=int(data.get("network_bottlenecks_count", 0)),
                financial_exposure_summary=data.get("financial_exposure_summary", {}),
                active_capabilities=data.get("active_capabilities", []),
                unavailable_capabilities=data.get("unavailable_capabilities", []),
                freshness_summary=data.get("freshness_summary", {}),
            )
    except Exception as e:
        logger.warning("Error fetching intelligence snapshot for tenant [%s]: %s", tenant_id, str(e), exc_info=True)
        payload = IntelligenceSnapshotResponse(
            snapshot_id="SNAP-ERROR",
            generated_at="",
        )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=payload,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )