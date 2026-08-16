"""Real-Time Event Operations, Quarantine Inspection, and Operational Alerts API Router for Phase 13."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from aurix_api.routers.health import get_db
from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_api.security.auth import get_current_tenant_context
from aurix_api.security.rate_limit import rate_limit_standard
from aurix_api.security.rbac import require_permission
from aurix_core.events.contracts import AlertContract, AlertStatus, EventStatus, InternalEvent
from aurix_core.events.processor import EventProcessor

logger = logging.getLogger("aurix_api.routers.events")

router = APIRouter(prefix="/api/v1", tags=["Real-Time Events & Alerts"])


@router.get(
    "/events/quarantine",
    response_model=ApiResponse[List[Dict[str, Any]]],
    summary="Inspect Quarantined / Dead-Letter Events",
    description="Returns all events that failed processing and were moved to the tenant quarantine store.",
)
async def list_quarantined_events(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[List[Dict[str, Any]]]:
    """Exposes dead-letter quarantined events for operational review within tenant boundaries."""
    tenant_id = tenant_context.tenant_id
    quarantined = EventProcessor._QUARANTINED_STORE.get(tenant_id, [])

    data = [
        {
            "event_id": ev.event_id,
            "event_type": ev.event_type.value,
            "entity_id": ev.entity_id,
            "source_system": ev.source_system,
            "attempt_count": ev.attempt_count,
            "last_error": ev.last_error,
            "event_timestamp": ev.event_timestamp,
        }
        for ev in quarantined
    ]

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=data,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.post(
    "/events/{event_id}/retry",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Retry Quarantined Event",
    description="Forces re-processing of a quarantined or failed operational event.",
)
async def retry_quarantined_event(
    event_id: str,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
    db: Session = Depends(get_db),
) -> ApiResponse[Dict[str, Any]]:
    """Retries processing a dead-letter event securely within tenant boundaries."""
    tenant_id = tenant_context.tenant_id
    quarantined = EventProcessor._QUARANTINED_STORE.get(tenant_id, [])

    target_event: Optional[InternalEvent] = None
    target_idx = -1

    for idx, ev in enumerate(quarantined):
        if ev.event_id == event_id:
            target_event = ev
            target_idx = idx
            break

    if not target_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quarantined event with ID '{event_id}' not found for tenant '{tenant_id}'.",
        )

    # Remove from quarantine before attempting retry
    quarantined.pop(target_idx)

    # Reset attempt count for safe recovery
    target_event.attempt_count = 0
    result = EventProcessor.process_event(db, target_event)

    return ApiResponse(
        status=ResponseStatus.SUCCESS if result.status == EventStatus.COMPLETED else ResponseStatus.FAILED,
        data={
            "event_id": result.event_id,
            "status": result.status.value,
            "dirty_capabilities": result.dirty_capabilities,
            "error_message": result.error_message,
        },
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/alerts",
    response_model=ApiResponse[List[AlertContract]],
    summary="List Operational Alerts",
    description="Returns active and historical operational alerts generated from real-time events.",
)
async def list_alerts(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[List[AlertContract]]:
    """Exposes tenant-scoped operational alerts."""
    tenant_id = tenant_context.tenant_id
    tenant_alerts = EventProcessor._ACTIVE_ALERTS.get(tenant_id, {})
    data = list(tenant_alerts.values())

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=data,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.post(
    "/alerts/{alert_id}/acknowledge",
    response_model=ApiResponse[AlertContract],
    summary="Acknowledge Operational Alert",
    description="Marks an active operational alert as acknowledged.",
)
async def acknowledge_alert(
    alert_id: str,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.WRITE_DATA)),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[AlertContract]:
    """Acknowledges an operational alert within tenant boundaries."""
    tenant_id = tenant_context.tenant_id
    tenant_alerts = EventProcessor._ACTIVE_ALERTS.get(tenant_id, {})

    target_alert: Optional[AlertContract] = None
    for alert in tenant_alerts.values():
        if alert.alert_id == alert_id:
            target_alert = alert
            break

    if not target_alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID '{alert_id}' not found for tenant '{tenant_id}'.",
        )

    target_alert.status = AlertStatus.ACKNOWLEDGED

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=target_alert,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )