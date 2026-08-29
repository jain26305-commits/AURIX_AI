"""Source-to-intelligence data lineage tracker for Phase 12 & Phase 19 Enterprise Data Fabric."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from aurix_core.integrations.contracts import SourceLineageRecord

logger = logging.getLogger("aurix.integrations.lineage")


class SourceLineageTracker:
    """Tracks and resolves provenance from external systems to canonical entities and downstream intelligence."""

    _in_memory_lineage_store: Dict[str, List[SourceLineageRecord]] = {}

    @classmethod
    def clear_test_store(cls) -> None:
        """Clears in-memory lineage store for unit tests."""
        cls._in_memory_lineage_store.clear()

    @classmethod
    def create_lineage_record(
        cls,
        tenant_id: str,
        source_system: str,
        connector_id: str,
        source_record_id: str,
        canonical_entity: str,
        canonical_record_id: str,
        sync_run_id: str,
        source_timestamp: Optional[str] = None,
        transformation_version: str = "1.0.0",
    ) -> SourceLineageRecord:
        """
        Creates and indexes an individual lineage tracking record.
        """
        record = SourceLineageRecord(
            lineage_id=f"LIN-{uuid.uuid4().hex[:10].upper()}",
            tenant_id=tenant_id,
            source_system=source_system,
            connector_id=connector_id,
            source_record_id=source_record_id or f"SRC-ANON-{uuid.uuid4().hex[:6].upper()}",
            source_timestamp=source_timestamp,
            canonical_entity=canonical_entity,
            canonical_record_id=canonical_record_id,
            sync_run_id=sync_run_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        cls._in_memory_lineage_store.setdefault(tenant_id, []).append(record)
        return record

    @classmethod
    def track_batch(
        cls,
        tenant_id: str,
        source_system: str,
        connector_id: str,
        canonical_entity: str,
        sync_run_id: str,
        records: List[Dict[str, Any]],
        source_id_field: str = "id",
        canonical_id_field: str = "sku_id",
        source_timestamp_field: Optional[str] = "timestamp",
        transformation_version: str = "1.0.0",
    ) -> List[SourceLineageRecord]:
        """
        Generates and stores lineage records for a batch of ingested records.
        """
        lineage_records: List[SourceLineageRecord] = []

        for row in records:
            src_id = str(row.get(source_id_field) or row.get("_source_record_id") or "")
            canon_id = str(row.get(canonical_id_field) or row.get("id") or "")
            src_ts = str(row.get(source_timestamp_field or "")) if source_timestamp_field else None

            if not src_id:
                src_id = f"SRC-{uuid.uuid4().hex[:8].upper()}"
            if not canon_id:
                canon_id = f"CANON-{uuid.uuid4().hex[:8].upper()}"

            record = cls.create_lineage_record(
                tenant_id=tenant_id,
                source_system=source_system,
                connector_id=connector_id,
                source_record_id=src_id,
                canonical_entity=canonical_entity,
                canonical_record_id=canon_id,
                sync_run_id=sync_run_id,
                source_timestamp=src_ts,
                transformation_version=transformation_version,
            )
            lineage_records.append(record)

        return lineage_records

    @classmethod
    def get_lineage_by_canonical_id(
        cls,
        tenant_id: str,
        canonical_entity: str,
        canonical_record_id: str,
    ) -> List[SourceLineageRecord]:
        """
        Retrieves lineage history for a specific canonical entity record.
        """
        tenant_records = cls._in_memory_lineage_store.get(tenant_id, [])
        return [
            r
            for r in tenant_records
            if r.canonical_entity == canonical_entity and r.canonical_record_id == canonical_record_id
        ]

    @classmethod
    def get_lineage_by_sync_run(
        cls,
        tenant_id: str,
        sync_run_id: str,
    ) -> List[SourceLineageRecord]:
        """
        Retrieves all lineage records produced during a specific synchronization run.
        """
        tenant_records = cls._in_memory_lineage_store.get(tenant_id, [])
        return [r for r in tenant_records if r.sync_run_id == sync_run_id]
