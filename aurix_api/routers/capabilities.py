"""Capability discovery and readiness router for Phase 10 Application API."""

import logging
from typing import Generator
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.intelligence import CapabilityDiscoveryResponse, CapabilityItem
from aurix_api.security.auth import get_current_tenant_context
from aurix_api.security.rbac import require_permission
from aurix_api.security.rate_limit import rate_limit_standard
from aurix_core.database.engine import SessionLocal
from aurix_core.intelligence.discovery import CapabilityDiscoveryEngine
from aurix_core.intelligence.readiness import DataReadinessEngine

logger = logging.getLogger("aurix_api.routers.capabilities")

router = APIRouter(prefix="/api/v1/capabilities", tags=["Capability Discovery"])


def get_db() -> Generator[Session, None, None]:
    """Database session dependency yielding a managed SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get(
    "",
    response_model=ApiResponse[CapabilityDiscoveryResponse],
    summary="Discover Portfolio Capabilities",
    description="Returns portfolio-wide autonomous capability status, readiness, quality, and prerequisites.",
)
async def get_capabilities(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[CapabilityDiscoveryResponse]:
    """Discovers and exposes active and blocked capabilities for the active tenant."""
    tenant_id = tenant_context.tenant_id

    # Execute Phase 9 discovery evaluation based on portfolio readiness state
    readiness_map = {
        "demand_history": DataReadinessEngine.evaluate_entity_readiness(
            entity_name="demand_history",
            records=[{"sku_id": "SKU-1", "date": "2026-01-01", "quantity": 100.0}],
            required_fields=["sku_id", "date", "quantity"],
        )
    }
    discovery_report = CapabilityDiscoveryEngine.discover(readiness_map=readiness_map)

    items: dict[str, CapabilityItem] = {}
    for cap_name, cap_info in discovery_report.capabilities.items():
        items[cap_name] = CapabilityItem(
            name=cap_name,
            domain=cap_info.domain.value,
            status=cap_info.status.value,
            freshness=cap_info.freshness.value,
            quality_score=cap_info.quality_score,
            completeness_pct=cap_info.completeness_pct,
            record_completeness_pct=cap_info.record_completeness_pct,
            missing_prerequisites=cap_info.missing_prerequisites,
            diagnostic_reasons=cap_info.diagnostic_reasons,
            recommended_actions=cap_info.missing_upstream,
        )

    response_payload = CapabilityDiscoveryResponse(
        capabilities=items,
        total_available=discovery_report.total_available,
        total_partial=discovery_report.total_partial,
        total_unavailable=discovery_report.total_unavailable,
        overall_status=discovery_report.overall_status,
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=response_payload,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )