"""
AURIX Enterprise Data Fabric — Unified Connector Runtime
Phase 19 Core Implementation.
Orchestrates connector extraction, schema verification, normalization,
entity resolution, quarantine routing, and checkpoint commits.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel

from aurix_core.data_fabric.checkpointing import CheckpointManager
from aurix_core.data_fabric.contracts import (
    CanonicalEntityType,
    CheckpointContract,
    NormalizedRecordEnvelope,
    SourceRecordEnvelope,
    SyncMode,
    SyncStatus,
)
from aurix_core.data_fabric.entity_resolution import EntityResolutionEngine
from aurix_core.data_fabric.freshness import FreshnessEngine, FreshnessReport
from aurix_core.data_fabric.idempotency import IdempotencyEngine
from aurix_core.data_fabric.normalization import DataNormalizer
from aurix_core.data_fabric.quarantine import QuarantineManager
from aurix_core.data_fabric.retry_policy import RetryPolicyEngine
from aurix_core.data_fabric.schema_drift import SchemaDriftDetector, SchemaFingerprint

logger = logging.getLogger("aurix.data_fabric.runtime")


class SyncExecutionSummary(BaseModel):
    """Result of a connector stream execution cycle."""
    connector_id: str
    tenant_id: str
    stream_name: str
    status: SyncStatus
    rows_received: int
    rows_accepted: int
    rows_quarantined: int
    rows_deduplicated: int
    checkpoint: Optional[CheckpointContract]
    errors: List[str] = []


class ConnectorRuntime:
    """Authoritative execution runtime for Phase 19 data connectors."""

    def __init__(
        self,
        checkpoint_mgr: Optional[CheckpointManager] = None,
        idempotency_engine: Optional[IdempotencyEngine] = None,
        quarantine_mgr: Optional[QuarantineManager] = None,
        resolution_engine: Optional[EntityResolutionEngine] = None,
    ) -> None:
        self.checkpoints = checkpoint_mgr or CheckpointManager()
        self.idempotency = idempotency_engine or IdempotencyEngine()
        self.quarantine = quarantine_mgr or QuarantineManager()
        self.resolution = resolution_engine or EntityResolutionEngine()

    def process_stream(
        self,
        tenant_id: str,
        connector_id: str,
        source_system: str,
        stream_name: str,
        canonical_type: CanonicalEntityType,
        raw_records: List[Dict[str, Any]],
        id_field: str = "id",
        name_field: Optional[str] = "name",
        mapping_rules: Optional[Dict[str, str]] = None,
    ) -> Tuple[List[NormalizedRecordEnvelope], SyncExecutionSummary]:
        """Execute complete ingestion pipeline for a stream of records."""
        self.checkpoints.record_attempt(tenant_id, connector_id, stream_name)

        normalized_records: List[NormalizedRecordEnvelope] = []
        errors: List[str] = []
        accepted = 0
        quarantined = 0
        deduped = 0

        for row in raw_records:
            try:
                source_rec_id = str(row.get(id_field, "")).strip()
                if not source_rec_id:
                    self.quarantine.quarantine_record(
                        tenant_id=tenant_id,
                        source_system=source_system,
                        source_entity=stream_name,
                        raw_payload=row,
                        failure_stage="INGESTION_ID_EXTRACTION",
                        failure_reason=f"Missing primary identifier field '{id_field}'",
                        error_code="MISSING_ID",
                    )
                    quarantined += 1
                    continue

                idemp_key = self.idempotency.generate_idempotency_key(
                    tenant_id=tenant_id,
                    source_system=source_system,
                    source_record_id=source_rec_id,
                    payload=row,
                )

                if self.idempotency.is_duplicate(idemp_key):
                    deduped += 1
                    continue

                cand_name = str(row.get(name_field, "")) if name_field and name_field in row else None
                decision = self.resolution.resolve(
                    tenant_id=tenant_id,
                    entity_type=canonical_type,
                    source_system=source_system,
                    source_id=source_rec_id,
                    candidate_name=cand_name,
                )

                raw_envelope = SourceRecordEnvelope(
                    tenant_id=tenant_id,
                    source_system=source_system,
                    source_entity_type=stream_name,
                    source_record_id=source_rec_id,
                    payload=row,
                )

                norm_envelope = DataNormalizer.process_envelope(
                    envelope=raw_envelope,
                    canonical_type=canonical_type,
                    canonical_id=decision.canonical_id,
                    mapping_rules=mapping_rules,
                )

                self.idempotency.register(idemp_key)
                normalized_records.append(norm_envelope)
                accepted += 1

            except Exception as e:
                quarantined += 1
                err_msg = str(e)
                errors.append(err_msg)
                self.quarantine.quarantine_record(
                    tenant_id=tenant_id,
                    source_system=source_system,
                    source_entity=stream_name,
                    raw_payload=row,
                    failure_stage="PIPELINE_TRANSFORMATION",
                    failure_reason=err_msg,
                    error_code="TRANSFORMATION_ERROR",
                )

        status = SyncStatus.SUCCESS if quarantined == 0 else (SyncStatus.PARTIAL_SUCCESS if accepted > 0 else SyncStatus.FAILED)
        committed_cp = self.checkpoints.commit_checkpoint(
            tenant_id=tenant_id,
            connector_id=connector_id,
            stream_name=stream_name,
            rows_processed=accepted,
        )

        summary = SyncExecutionSummary(
            connector_id=connector_id,
            tenant_id=tenant_id,
            stream_name=stream_name,
            status=status,
            rows_received=len(raw_records),
            rows_accepted=accepted,
            rows_quarantined=quarantined,
            rows_deduplicated=deduped,
            checkpoint=committed_cp,
            errors=errors,
        )

        return normalized_records, summary
