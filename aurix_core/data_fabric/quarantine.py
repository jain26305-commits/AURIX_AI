"""
AURIX Enterprise Data Fabric — Quarantine & Error Isolation Engine
Phase 19 Core Implementation.
Isolates defective records without aborting complete ingestion batches.
"""

from __future__ import annotations

import uuid
from typing import Any, Callable, Dict, List, Optional
from aurix_core.data_fabric.contracts import ErrorSeverity, QuarantineEnvelope


class QuarantineManager:
    """Manages isolation, categorization, and replay of defective payloads."""

    def __init__(self) -> None:
        # In-memory quarantine store: quarantine_id -> QuarantineEnvelope
        self._store: Dict[str, QuarantineEnvelope] = {}

    def quarantine_record(
        self,
        tenant_id: str,
        source_system: str,
        source_entity: str,
        raw_payload: Dict[str, Any],
        failure_stage: str,
        failure_reason: str,
        error_code: str,
        source_record_id: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        retryable: bool = False,
    ) -> QuarantineEnvelope:
        """Isolate a defective record with complete diagnostics."""
        q_id = str(uuid.uuid4())
        record = QuarantineEnvelope(
            quarantine_id=q_id,
            tenant_id=tenant_id,
            source_system=source_system,
            source_entity=source_entity,
            source_record_id=source_record_id,
            raw_payload=raw_payload,
            failure_stage=failure_stage,
            failure_reason=failure_reason,
            error_code=error_code,
            severity=severity,
            retryable=retryable,
        )
        self._store[q_id] = record
        return record

    def list_quarantined(
        self,
        tenant_id: str,
        resolved: Optional[bool] = False,
        severity: Optional[ErrorSeverity] = None,
    ) -> List[QuarantineEnvelope]:
        """List quarantined records filtered by resolution and severity."""
        results = []
        for r in self._store.values():
            if r.tenant_id != tenant_id:
                continue
            if resolved is not None and r.resolved != resolved:
                continue
            if severity is not None and r.severity != severity:
                continue
            results.append(r)
        return results

    def replay_record(
        self,
        quarantine_id: str,
        pipeline_handler: Callable[[Dict[str, Any]], bool],
        remediated_payload: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Replay a quarantined record through a transformation pipeline."""
        if quarantine_id not in self._store:
            return False

        record = self._store[quarantine_id]
        payload = remediated_payload or record.raw_payload

        record.retry_count += 1
        success = pipeline_handler(payload)

        if success:
            record.resolved = True
            record.resolution_notes = f"Successfully replayed on retry #{record.retry_count}"
        else:
            record.resolution_notes = f"Replay attempt #{record.retry_count} failed"

        return success
