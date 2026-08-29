"""Universal Integration Hub API router for Phase 12 & Phase 19 Enterprise Data Fabric."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Type

from fastapi import APIRouter, Depends, HTTPException, status

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
from aurix_core.data_fabric.checkpointing import CheckpointManager
from aurix_core.data_fabric.freshness import FreshnessEngine, FreshnessReport
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
)
from aurix_core.integrations.lineage import SourceLineageTracker
from aurix_core.integrations.reconciliation import ReconciliationEngine
from aurix_core.integrations.sync_manager import SyncManager

logger = logging.getLogger("aurix_api.routers.integrations")

router = APIRouter(
    prefix="/api/v1/integrations",
    tags=["Universal Integration Hub"],
)

ADAPTER_MAP: Dict[str, Type[BaseConnector]] = {
    "generic_rest": GenericRestConnector,
    "generic_webhook": GenericWebhookAdapter,
    "generic_sftp": GenericSftpConnector,
    "erp_odoo": OdooErpConnector,
    "wms_generic": GenericWmsConnector,
    "mock": MockIntegrationConnector,
}

_connector_store: Dict[str, Dict[str, ConnectorConfig]] = {}
_checkpoint_mgr = CheckpointManager()


def _get_adapter_instance(config: ConnectorConfig) -> BaseConnector:
    """Instantiates the concrete adapter class for a connector config."""
    adapter_cls = ADAPTER_MAP.get(config.adapter_type.lower())

    if not adapter_cls:
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
    _: TenantContext = Depends(
        require_permission(Permission.MANAGE_CONNECTORS)
    ),
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
    _: TenantContext = Depends(
        require_permission(Permission.READ_DATA)
    ),
) -> ApiResponse[List[ConnectorConfig]]:
    """Lists all registered connectors for the authenticated tenant."""

    tenant_id = tenant_context.tenant_id
    connectors = list(
        _connector_store.get(tenant_id, {}).values()
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=connectors,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/connectors/{connector_id}",
    response_model=ApiResponse[ConnectorConfig],
    summary="Get Integration Connector",
)
async def get_connector(
    connector_id: str,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(
        require_permission(Permission.READ_DATA)
    ),
) -> ApiResponse[ConnectorConfig]:
    """Returns a single connector for the authenticated tenant."""

    tenant_id = tenant_context.tenant_id

    config = _connector_store.get(
        tenant_id,
        {},
    ).get(connector_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector '{connector_id}' not found.",
        )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=config,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/connectors/{connector_id}/freshness",
    response_model=ApiResponse[FreshnessReport],
    summary="Get Connector Data Freshness SLA",
)
async def get_connector_freshness(
    connector_id: str,
    stream_name: str = "demand_history",
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(
        require_permission(Permission.READ_DATA)
    ),
) -> ApiResponse[FreshnessReport]:
    """Calculates truthful data freshness telemetry from stream checkpoints."""

    tenant_id = tenant_context.tenant_id

    config = _connector_store.get(
        tenant_id,
        {},
    ).get(connector_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector '{connector_id}' not found.",
        )

    cp = _checkpoint_mgr.get_checkpoint(
        tenant_id,
        connector_id,
        stream_name,
    )

    report = FreshnessEngine.calculate_freshness(
        checkpoint=cp,
    )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=report,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )


@router.get(
    "/connectors/{connector_id}/health",
    response_model=ApiResponse[IntegrationHealthReport],
    summary="Get Connector Health",
)
async def get_connector_health(
    connector_id: str,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(
        require_permission(Permission.READ_DATA)
    ),
) -> ApiResponse[IntegrationHealthReport]:
    """
    Executes the connector's native health check and returns
    the standardized integration health report.
    """

    tenant_id = tenant_context.tenant_id

    config = _connector_store.get(
        tenant_id,
        {},
    ).get(connector_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector '{connector_id}' not found.",
        )

    try:
        adapter = _get_adapter_instance(config)

        health_report = adapter.get_health_report()

        # Keep the in-memory connector configuration synchronized
        # with the latest health state returned by the adapter.
        config.health_state = health_report.health_state
        config.updated_at = datetime.now(timezone.utc).isoformat()

        return ApiResponse(
            status=ResponseStatus.SUCCESS,
            data=health_report,
            meta=ResponseMetadata(tenant_id=tenant_id),
        )

    except ConnectorException as exc:
        logger.error(
            "Connector health check failed [%s]: %s",
            connector_id,
            exc.message,
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Health check failed for connector "
                f"'{connector_id}': {exc.message}"
            ),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Unexpected connector health check failure [%s]",
            connector_id,
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Unable to determine health for connector "
                f"'{connector_id}'."
            ),
        ) from exc


@router.post(
    "/connectors/{connector_id}/sync",
    response_model=ApiResponse[SyncRunRecord],
    summary="Trigger Connector Synchronization",
)
async def trigger_sync(
    connector_id: str,
    payload: TriggerSyncRequest,
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: TenantContext = Depends(
        require_permission(Permission.TRIGGER_SYNC)
    ),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[SyncRunRecord]:
    """Triggers an immediate synchronization run for the designated connector."""

    tenant_id = tenant_context.tenant_id

    config = _connector_store.get(
        tenant_id,
        {},
    ).get(connector_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector '{connector_id}' not found.",
        )

    if not config.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Connector '{connector_id}' is currently disabled."
            ),
        )

    adapter = _get_adapter_instance(config)

    try:
        run_record = SyncManager.run_sync(
            connector=adapter,
            mode=payload.mode,
            entity_name=payload.entity_name,
            key_field=payload.key_field,
            source_id_field=payload.source_id_field,
            batch_size=payload.batch_size,
        )

    except ConnectorException as exc:
        logger.error(
            "Connector synchronization failed [%s]: %s",
            connector_id,
            exc.message,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=exc.message,
        ) from exc

    return ApiResponse(
        status=(
            ResponseStatus.SUCCESS
            if run_record.status.value == "COMPLETED"
            else ResponseStatus.PARTIAL_SUCCESS
        ),
        data=run_record,
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
    _: TenantContext = Depends(
        require_permission(Permission.VIEW_RECONCILIATION)
    ),
    __: TenantContext = Depends(rate_limit_standard()),
) -> ApiResponse[ReconciliationSummaryResponse]:
    """Compares multi-source datasets, evaluates variances, and outputs canonical resolutions."""

    tenant_id = tenant_context.tenant_id

    reconciled_records, audit_trail = (
        ReconciliationEngine.reconcile_datasets(
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
    )

    matched = sum(
        1
        for r in audit_trail
        if r.reconciliation_status
        == ReconciliationStatus.MATCHED
    )

    minor = sum(
        1
        for r in audit_trail
        if r.reconciliation_status
        == ReconciliationStatus.MINOR_VARIANCE
    )

    material = sum(
        1
        for r in audit_trail
        if r.reconciliation_status
        == ReconciliationStatus.MATERIAL_VARIANCE
    )

    unresolved = sum(
        1
        for r in audit_trail
        if r.reconciliation_status
        == ReconciliationStatus.UNRESOLVED
    )

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
    _: TenantContext = Depends(
        require_permission(Permission.VIEW_LINEAGE)
    ),
) -> ApiResponse[List[SourceLineageRecord]]:
    """Retrieves source-to-canonical data lineage records."""

    tenant_id = tenant_context.tenant_id

    if sync_run_id:
        records = SourceLineageTracker.get_lineage_by_sync_run(
            tenant_id,
            sync_run_id,
        )

    elif canonical_entity and canonical_record_id:
        records = SourceLineageTracker.get_lineage_by_canonical_id(
            tenant_id,
            canonical_entity,
            canonical_record_id,
        )

    else:
        records = (
            SourceLineageTracker._in_memory_lineage_store.get(
                tenant_id,
                [],
            )
        )

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=records,
        meta=ResponseMetadata(tenant_id=tenant_id),
    )