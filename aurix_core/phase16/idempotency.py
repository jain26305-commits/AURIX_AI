"""Durable, tenant-scoped idempotency helpers for Phase 16 writes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from aurix_core.phase16.contracts import MutationMetadata, Phase16Result
from aurix_core.phase16.models import Phase16IdempotencyKeyModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _result_from_payload(payload: Any) -> Phase16Result:
    """Deserialize a persisted idempotency result from JSON text or JSON data."""
    if isinstance(payload, str):
        payload = json.loads(payload)
    return Phase16Result.model_validate(payload)


def effective_key(metadata: MutationMetadata) -> Optional[str]:
    """Derive an idempotency key from explicit or source-system identity."""
    if metadata.idempotency_key:
        return metadata.idempotency_key
    if metadata.external_record_id:
        return f"{metadata.source_system}:{metadata.external_record_id}"
    return None


def begin(
    db: Session,
    tenant_id: str,
    metadata: MutationMetadata,
    operation: str,
) -> Tuple[Optional[Phase16IdempotencyKeyModel], Optional[Phase16Result]]:
    """Register a write request or return a previously completed result.

    The insert is protected by the database uniqueness constraint. A nested
    transaction isolates a duplicate-key race without rolling back the caller's
    outer transaction.
    """
    key = effective_key(metadata)
    if not key:
        return None, None

    source_identity = None
    if metadata.external_record_id:
        source_identity = f"{metadata.source_system}:{metadata.external_record_id}"

    existing = db.execute(
        select(Phase16IdempotencyKeyModel).where(
            Phase16IdempotencyKeyModel.tenant_id == tenant_id,
            Phase16IdempotencyKeyModel.idempotency_key == key,
        )
    ).scalar_one_or_none()

    if existing is None and source_identity is not None:
        existing = db.execute(
            select(Phase16IdempotencyKeyModel).where(
                Phase16IdempotencyKeyModel.tenant_id == tenant_id,
                Phase16IdempotencyKeyModel.source_identity == source_identity,
            )
        ).scalar_one_or_none()

    if existing is not None:
        if existing.status == "COMPLETED" and existing.result_json:
            return existing, _result_from_payload(existing.result_json)

        return existing, Phase16Result(
            success=False,
            status="IDEMPOTENCY_IN_PROGRESS",
            data={
                "idempotency_key": key,
                "operation": existing.operation,
            },
            warnings=["An equivalent request is already being processed."],
        )

    record = Phase16IdempotencyKeyModel(
        id=f"IDEMP-{__import__('uuid').uuid4().hex[:16].upper()}",
        tenant_id=tenant_id,
        idempotency_key=key,
        operation=operation,
        source_system=metadata.source_system,
        external_record_id=metadata.external_record_id,
        status="IN_PROGRESS",
        source_identity=source_identity,
        created_at=_now(),
    )

    try:
        with db.begin_nested():
            db.add(record)
            db.flush()
    except IntegrityError:
        existing = db.execute(
            select(Phase16IdempotencyKeyModel).where(
                Phase16IdempotencyKeyModel.tenant_id == tenant_id,
                Phase16IdempotencyKeyModel.idempotency_key == key,
            )
        ).scalar_one_or_none()

        if existing is None:
            raise

        if existing.status == "COMPLETED" and existing.result_json:
            return existing, _result_from_payload(existing.result_json)

        return existing, Phase16Result(
            success=False,
            status="IDEMPOTENCY_IN_PROGRESS",
            data={
                "idempotency_key": key,
                "operation": existing.operation,
            },
            warnings=["An equivalent request is already being processed."],
        )

    return record, None


def complete(
    db: Session,
    record: Optional[Phase16IdempotencyKeyModel],
    result: Phase16Result,
) -> None:
    """Persist the authoritative result in the same transaction as the write."""
    if record is None:
        return

    record.status = "COMPLETED"
    record.result_json = result.model_dump(mode="json")
    record.completed_at = _now()