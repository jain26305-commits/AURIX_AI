"""Master synchronization orchestration manager for Phase 12 & Phase 19 Enterprise Data Fabric."""

import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from aurix_core.config.settings import settings
from aurix_core.data_fabric.checkpointing import CheckpointManager
from aurix_core.data_fabric.idempotency import IdempotencyEngine
from aurix_core.data_fabric.retry_policy import RetryPolicyEngine
from aurix_core.integrations.base import BaseConnector, ConnectorException
from aurix_core.integrations.contracts import (
    ConnectorHealthState,
    SyncMode,
    SyncRunRecord,
    SyncStatus,
)
from aurix_core.integrations.lineage import SourceLineageTracker
from aurix_core.intelligence.discovery import CapabilityDiscoveryEngine
from aurix_core.intelligence.incremental import IncrementalMergeEngine, MergeResult
from aurix_core.intelligence.readiness import DataReadinessEngine
from aurix_core.onboarding.quality_validator import OnboardingQualityEngine

logger = logging.getLogger("aurix.integrations.sync_manager")


class SyncManager:
    """Orchestrates external data synchronization, retries, checkpointing, and capability recomputation."""

    _sync_runs_store: Dict[str, List[SyncRunRecord]] = {}
    _checkpoint_mgr = CheckpointManager()
    _idempotency_engine = IdempotencyEngine()

    @classmethod
    def clear_test_store(cls) -> None:
        """Clears in-memory sync run store for testing."""
        cls._sync_runs_store.clear()

    @classmethod
    def get_sync_run(cls, tenant_id: str, sync_run_id: str) -> Optional[SyncRunRecord]:
        """Retrieves a specific sync run record ensuring tenant isolation."""
        tenant_runs = cls._sync_runs_store.get(tenant_id, [])
        for r in tenant_runs:
            if r.sync_run_id == sync_run_id:
                return r
        return None

    @classmethod
    def list_sync_runs(
        cls,
        tenant_id: str,
        connector_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[SyncRunRecord]:
        """Lists historical synchronization executions for a tenant or specific connector."""
        tenant_runs = cls._sync_runs_store.get(tenant_id, [])
        if connector_id:
            filtered = [r for r in tenant_runs if r.connector_id == connector_id]
            return filtered[-limit:]
        return tenant_runs[-limit:]

    @classmethod
    def _record_sync_run(cls, record: SyncRunRecord) -> None:
        """Appends a sync run record to the tenant store."""
        cls._sync_runs_store.setdefault(record.tenant_id, []).append(record)

    @classmethod
    def execute_with_retry(
        cls,
        connector: BaseConnector,
        mode: SyncMode,
        cursor: Optional[Dict[str, Any]],
        batch_size: int = 1000,
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Executes connector sync with exponential backoff for transient failures.
        """
        max_attempts = connector.max_retries
        last_exception: Optional[Exception] = None

        for attempt in range(1, max_attempts + 1):
            try:
                return connector.execute_sync(mode=mode, cursor=cursor, batch_size=batch_size)
            except Exception as exc:
                last_exception = exc
                decision = RetryPolicyEngine.evaluate(exc, attempt=attempt)
                if not decision.should_retry:
                    raise exc

                logger.warning(
                    "Sync attempt %d/%d failed for connector [%s]. %s",
                    attempt,
                    max_attempts,
                    connector.connector_id,
                    decision.reason,
                )
                time.sleep(decision.delay_seconds)

        if last_exception:
            raise last_exception
        raise ConnectorException("Sync failed after exhausting max retries.", connector_id=connector.connector_id)

    @classmethod
    def run_sync(
        cls,
        connector: BaseConnector,
        mode: SyncMode = SyncMode.INCREMENTAL,
        existing_canonical_records: Optional[List[Dict[str, Any]]] = None,
        entity_name: str = "demand_history",
        key_field: str = "sku_id",
        source_id_field: str = "id",
        batch_size: int = 1000,
    ) -> SyncRunRecord:
        """
        Executes end-to-end synchronization pipeline, data validation, lineage, and selective recomputation.
        """
        sync_run_id = f"SYNC-{uuid.uuid4().hex[:10].upper()}"
        tenant_id = connector.tenant_id
        connector_id = connector.connector_id
        cursor_before = connector.config.cursor

        run_record = SyncRunRecord(
            sync_run_id=sync_run_id,
            tenant_id=tenant_id,
            connector_id=connector_id,
            sync_mode=mode,
            status=SyncStatus.RUNNING,
            cursor_before=cursor_before,
        )

        try:
            # 1. Execute Extraction with Bounded Retry
            raw_records, cursor_after = cls.execute_with_retry(
                connector=connector,
                mode=mode,
                cursor=cursor_before,
                batch_size=batch_size,
            )

            run_record.records_received = len(raw_records)
            payload_str = json.dumps(raw_records, default=str)
            run_record.input_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

            if not raw_records:
                run_record.status = SyncStatus.COMPLETED
                run_record.completed_at = datetime.now(timezone.utc).isoformat()
                run_record.cursor_after = cursor_after or cursor_before
                cls._record_sync_run(run_record)
                return run_record

            # 2. Validate Data Hygiene via Phase 11 Quality Engine
            canonical_fields = set(raw_records[0].keys()) if raw_records else set()
            accepted, rejected, quality, _, _ = OnboardingQualityEngine.evaluate(
                records=raw_records,
                entity_name=entity_name,
                mapped_fields=canonical_fields,
            )

            run_record.records_accepted = len(accepted)
            run_record.records_rejected = len(rejected)
            if rejected:
                run_record.warnings.append(f"{len(rejected)} records rejected during quality validation.")

            # 3. Track End-to-End Lineage
            SourceLineageTracker.track_batch(
                tenant_id=tenant_id,
                source_system=connector.config.family.value,
                connector_id=connector_id,
                canonical_entity=entity_name,
                sync_run_id=sync_run_id,
                records=accepted,
                source_id_field=source_id_field,
                canonical_id_field=key_field,
            )

            # 4. Incremental Merge & Deduplication via Phase 9
            merge_result: MergeResult = IncrementalMergeEngine.merge_dataset(
                existing_records=existing_canonical_records or [],
                new_records=accepted,
                entity_name=entity_name,
            )
            run_record.affected_capabilities = merge_result.affected_capabilities

            # 5. Refresh Capability Discovery
            readiness_map = {
                entity_name: DataReadinessEngine.evaluate_entity_readiness(
                    entity_name=entity_name,
                    records=merge_result.merged_records,
                    required_fields=[key_field],
                )
            }
            CapabilityDiscoveryEngine.discover(readiness_map=readiness_map)

            # 6. Advance Checkpoint Cursor in Fabric Manager
            cls._checkpoint_mgr.commit_checkpoint(
                tenant_id=tenant_id,
                connector_id=connector_id,
                stream_name=entity_name,
                rows_processed=len(accepted),
            )

            connector.config.cursor = cursor_after
            connector.config.last_sync_timestamp = datetime.now(timezone.utc).isoformat()
            connector.config.last_sync_status = SyncStatus.COMPLETED
            connector.config.health_state = ConnectorHealthState.HEALTHY

            run_record.cursor_after = cursor_after
            run_record.status = (
                SyncStatus.COMPLETED if len(rejected) == 0 else SyncStatus.PARTIAL_SUCCESS
            )
            run_record.completed_at = datetime.now(timezone.utc).isoformat()

        except Exception as e:
            logger.error("Sync run [%s] failed for connector [%s]: %s", sync_run_id, connector_id, str(e))
            connector.config.last_sync_status = SyncStatus.FAILED
            connector.config.health_state = ConnectorHealthState.FAILED
            run_record.status = SyncStatus.FAILED
            run_record.completed_at = datetime.now(timezone.utc).isoformat()
            run_record.error_summary = str(e)

        finally:
            cls._record_sync_run(run_record)

        return run_record
