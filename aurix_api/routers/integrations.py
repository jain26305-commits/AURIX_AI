"""Universal Integration Hub API router for Phase 12."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_api.schemas.integrations import (
    ConnectorCreateRequest,
    ReconcileDatasetsRequest,
    ReconciliationSummaryResponse,
    TriggerSyncRequest,
)
from aurix_api.security.auth import get_current_tenant_context
from aurix_api.security.rate_limit import rate_limit_standard
from aurix_api.security.rbac import require_permission
from aurix_core.integrations.adapters.erp_odoo import OdooErpConnector
from aurix_core.integrations.adapters.generic_rest import GenericRestConnector
from aurix_core.integrations.adapters.generic_sftp import GenericSftpConnector
from aurix_core.integrations.adapters.generic_webhook import GenericWebhookAdapter
from aurix_core.integrations.adapters.test_mock import MockIntegrationConnector
from aurix_core.integrations.adapters.wms_generic import GenericWmsConnector
from aurix_core.integrations.base import BaseConnector, ConnectorException
from aurix_core.integrations.contracts import (
    ConnectorConfig,
    IntegrationHealthReport,
    ReconciliationStatus,
    SourceLineageRecord,
    SyncRunRecord,
    WebhookEventPayload,
)
from aurix_core.integrations.lineage import SourceLineageTracker
from aurix_core.integrations.reconciliation import ReconciliationEngine
from aurix_core.integrations.sync_manager import SyncManager

logger = logging.getLogger("aurix_api.routers.integrations")

router = APIRouter(prefix="/api/v1/integrations", tags=["Universal Integration Hub"])

# Adapter registry mapping
ADAPTER_MAP: Dict[str, Type[BaseConnector]] = {
    "generic_rest": GenericRestConnector,
    "generic_webhook": GenericWebhookAdapter,
    "generic_sftp": GenericSftpConnector,
    "erp_odoo": OdooErpConnector,
    "wms_generic": GenericWmsConnector,
    "mock": MockIntegrationConnector,
}

# In-memory tenant connector registry
_connector_store: Dict[str, Dict[str, ConnectorConfig]] = {}


def _get_adapter_instance(config: ConnectorConfig) -> BaseConnector:
    """Instantiates the concrete adapter class for a connector config."""
    adapter_cls = ADAPTER_MAP.get(config.adapter_type.lower())
    if not adapter_cls:
        # Fallback to GenericRestConnector if unspecified
        adapter_cls = GenericRestConnector
    return adapter_cls(config)


@router.post(
    "/connectors",
    response_model=ApiResponse[ConnectorConfig],
    summary="Register Integration Connector",
)
async def create_connector(
    payload: ConnectorCreateRequest,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.MANAGE_CONNECTORS)),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[ConnectorConfig]:
    """Registers a new external connector instance for the authenticated tenant."""
    tenant_id = tenant_context.tenant_id
    connector_id = f"CONN-{uuid.uuid4().hex[:10].upper()}"

    config = ConnectorConfig(
        connector_id=connector_id,
        tenant_id=tenant_id,
        name=payload.name,
        family=payload.family,
        adapter_type=payload.adapter_type,
        base_url=payload.base_url,
        auth_config=payload.auth_config,
        schedule_cron=payload.schedule_cron,
        enabled=payload.enabled,
        custom_settings=payload.custom_settings,
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
    )

    _connector_store.setdefault(tenant_id, {})[connector_id] = config

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=config,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/connectors",
    response_model=ApiResponse[List[ConnectorConfig]],
    summary="List Integration Connectors",
)
async def list_connectors(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
) -> ApiResponse[List[ConnectorConfig]]:
    """Lists all registered connectors for the authenticated tenant."""
    tenant_id = tenant_context.tenant_id
    connectors = list(_connector_store.get(tenant_id, {}).values())

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=connectors,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/connectors/{connector_id}",
    response_model=ApiResponse[ConnectorConfig],
    summary="Get Connector Details",
)
async def get_connector(
    connector_id: str,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
) -> ApiResponse[ConnectorConfig]:
    """Retrieves configuration and state for a specific connector."""
    tenant_id = tenant_context.tenant_id
    config = _connector_store.get(tenant_id, {}).get(connector_id)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Connector '{connector_id}' not found.")

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=config,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.post(
    "/connectors/{connector_id}/sync",
    response_model=ApiResponse[SyncRunRecord],
    summary="Trigger Connector Synchronization",
)
async def trigger_sync(
    connector_id: str,
    payload: TriggerSyncRequest,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.TRIGGER_SYNC)),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[SyncRunRecord]:
    """Triggers an immediate synchronization run for the designated connector."""
    tenant_id = tenant_context.tenant_id
    config = _connector_store.get(tenant_id, {}).get(connector_id)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Connector '{connector_id}' not found.")

    if not config.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connector '{connector_id}' is currently disabled.",
        )

    adapter = _get_adapter_instance(config)
    run_record = SyncManager.run_sync(
        connector=adapter,
        mode=payload.mode,
        entity_name=payload.entity_name,
        key_field=payload.key_field,
        source_id_field=payload.source_id_field,
        batch_size=payload.batch_size,
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS if run_record.status.value == "COMPLETED" else ResponseStatus.PARTIAL_SUCCESS,
        data=run_record,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/connectors/{connector_id}/health",
    response_model=ApiResponse[IntegrationHealthReport],
    summary="Get Connector Health Report",
)
async def get_connector_health(
    connector_id: str,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.READ_DATA)),
) -> ApiResponse[IntegrationHealthReport]:
    """Executes a live health check and returns reliability metrics."""
    tenant_id = tenant_context.tenant_id
    config = _connector_store.get(tenant_id, {}).get(connector_id)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Connector '{connector_id}' not found.")

    adapter = _get_adapter_instance(config)
    report = adapter.get_health_report()

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=report,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.post(
    "/reconcile",
    response_model=ApiResponse[ReconciliationSummaryResponse],
    summary="Reconcile Multi-Source Datasets",
)
async def reconcile_datasets(
    payload: ReconcileDatasetsRequest,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.VIEW_RECONCILIATION)),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[ReconciliationSummaryResponse]:
    """Compares multi-source datasets, evaluates variances, and outputs canonical resolutions."""
    tenant_id = tenant_context.tenant_id

    reconciled_records, audit_trail = ReconciliationEngine.reconcile_datasets(
        tenant_id=tenant_id,
        entity_type=payload.entity_type,
        dataset_a=payload.dataset_a,
        source_a=payload.source_a,
        dataset_b=payload.dataset_b,
        source_b=payload.source_b,
        key_field=payload.key_field,
        metric_field=payload.metric_field,
        material_threshold_pct=payload.material_threshold_pct,
    )

    matched = sum(1 for r in audit_trail if r.reconciliation_status == ReconciliationStatus.MATCHED)
    minor = sum(1 for r in audit_trail if r.reconciliation_status == ReconciliationStatus.MINOR_VARIANCE)
    material = sum(1 for r in audit_trail if r.reconciliation_status == ReconciliationStatus.MATERIAL_VARIANCE)
    unresolved = sum(1 for r in audit_trail if r.reconciliation_status == ReconciliationStatus.UNRESOLVED)

    summary = ReconciliationSummaryResponse(
        total_entities_evaluated=len(audit_trail),
        matched_count=matched,
        minor_variance_count=minor,
        material_variance_count=material,
        unresolved_count=unresolved,
        audit_trail=audit_trail,
        reconciled_dataset_sample=reconciled_records[:20],
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=summary,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/lineage",
    response_model=ApiResponse[List[SourceLineageRecord]],
    summary="Query Source Lineage",
)
async def query_lineage(
    canonical_entity: Optional[str] = None,
    canonical_record_id: Optional[str] = None,
    sync_run_id: Optional[str] = None,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(require_permission(Permission.VIEW_LINEAGE)),
) -> ApiResponse[List[SourceLineageRecord]]:
    """Retrieves source-to-canonical data lineage records."""
    tenant_id = tenant_context.tenant_id

    if sync_run_id:
        records = SourceLineageTracker.get_lineage_by_sync_run(tenant_id, sync_run_id)
    elif canonical_entity and canonical_record_id:
        records = SourceLineageTracker.get_lineage_by_canonical_id(
            tenant_id, canonical_entity, canonical_record_id
        )
    else:
        records = SourceLineageTracker._in_memory_lineage_store.get(tenant_id, [])

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=records,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.post(
    "/webhooks/{connector_id}",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Ingest External Webhook Event",
)
async def ingest_webhook(
    connector_id: str,
    request: Request,
    x_signature_sha256: Optional[str] = Header(None, alias="X-Signature-SHA256"),
    x_timestamp: Optional[str] = Header(None, alias="X-Timestamp"),
) -> ApiResponse[Dict[str, Any]]:
    """Public webhook intake endpoint supporting cryptographic HMAC verification and replay checks."""
    # Find connector across tenants
    target_config: Optional[ConnectorConfig] = None
    for tenant_id, conns in _connector_store.items():
        if connector_id in conns:
            target_config = conns[connector_id]
            break

    if not target_config or not target_config.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Webhook endpoint '{connector_id}' not found.")

    try:
        raw_body = await request.body()
        payload_dict = await request.json() if raw_body else {}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Malformed JSON webhook payload: {str(e)}")

    event = WebhookEventPayload(
        event_id=str(payload_dict.get("event_id") or uuid.uuid4().hex),
        tenant_id=target_config.tenant_id,
        source_system=target_config.family.value,
        connector_id=connector_id,
        event_type=str(payload_dict.get("event_type", "GENERIC_EVENT")),
        entity_type=str(payload_dict.get("entity_type", "INVENTORY")),
        event_timestamp=str(x_timestamp or payload_dict.get("timestamp") or datetime.now(timezone.utc).isoformat()),
        payload=payload_dict,
        signature=x_signature_sha256,
        headers=dict(request.headers),
    )

    adapter = _get_adapter_instance(target_config)
    if isinstance(adapter, GenericWebhookAdapter):
        try:
            staged = adapter.ingest_event(event=event, raw_body=raw_body)
            return ApiResponse(
                status=ResponseStatus.SUCCESS,
                data={"staged": True, "event_id": event.event_id, "record": staged},
                meta=ResponseMetadata(tenant_id=target_config.tenant_id),
            )
        except ConnectorException as ce:
            if ce.code == "DUPLICATE_EVENT":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=ce.message)
            elif ce.code in ("INVALID_SIGNATURE", "TIMESTAMP_DRIFT_EXCEEDED"):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ce.message)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ce.message)

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data={"staged": True, "event_id": event.event_id},
        meta=ResponseMetadata(tenant_id=target_config.tenant_id),
    )