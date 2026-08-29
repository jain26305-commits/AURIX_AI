"""
AURIX Enterprise Data Fabric — Checkpointing Engine
Phase 19 Core Implementation.
Tracks cursor positions, delta watermarks, and sync resumption tokens.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from aurix_core.data_fabric.contracts import CheckpointContract


class CheckpointManager:
    """Manages transactional checkpoints for stateful, resumable sync pipelines."""

    def __init__(self) -> None:
        # In-memory checkpoint registry: (tenant_id, connector_id, stream_name) -> CheckpointContract
        self._checkpoints: Dict[Tuple[str, str, str], CheckpointContract] = {}

    def get_checkpoint(
        self,
        tenant_id: str,
        connector_id: str,
        stream_name: str,
    ) -> Optional[CheckpointContract]:
        """Retrieve existing checkpoint for a connector stream."""
        key = (tenant_id, connector_id, stream_name)
        return self._checkpoints.get(key)

    def commit_checkpoint(
        self,
        tenant_id: str,
        connector_id: str,
        stream_name: str,
        cursor_field: Optional[str] = None,
        cursor_value: Optional[str] = None,
        high_watermark: Optional[datetime] = None,
        rows_processed: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CheckpointContract:
        """Persist or advance stream checkpoint upon successful batch processing."""
        key = (tenant_id, connector_id, stream_name)
        existing = self._checkpoints.get(key)

        now = datetime.now(timezone.utc)
        total_rows = (existing.rows_synced_total if existing else 0) + rows_processed

        new_checkpoint = CheckpointContract(
            tenant_id=tenant_id,
            connector_id=connector_id,
            stream_name=stream_name,
            cursor_field=cursor_field or (existing.cursor_field if existing else None),
            cursor_value=cursor_value or (existing.cursor_value if existing else None),
            high_watermark=high_watermark or (existing.high_watermark if existing else None),
            rows_synced_total=total_rows,
            last_successful_sync_at=now,
            last_attempted_sync_at=now,
            state_metadata=metadata or (existing.state_metadata if existing else {}),
        )

        self._checkpoints[key] = new_checkpoint
        return new_checkpoint

    def record_attempt(
        self,
        tenant_id: str,
        connector_id: str,
        stream_name: str,
    ) -> None:
        """Mark an attempted sync execution timestamp without advancing watermark."""
        key = (tenant_id, connector_id, stream_name)
        existing = self._checkpoints.get(key)
        now = datetime.now(timezone.utc)

        if existing:
            existing.last_attempted_sync_at = now
        else:
            self._checkpoints[key] = CheckpointContract(
                tenant_id=tenant_id,
                connector_id=connector_id,
                stream_name=stream_name,
                last_attempted_sync_at=now,
            )
