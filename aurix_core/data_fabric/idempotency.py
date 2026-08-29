"""
AURIX Enterprise Data Fabric — Idempotency Engine
Phase 19 Core Implementation.
Guarantees duplicate prevention and idempotent ingestion execution.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional, Set


class IdempotencyEngine:
    """Generates composite deterministic keys and tracks ingestion duplicates."""

    def __init__(self) -> None:
        self._processed_keys: Set[str] = set()

    @staticmethod
    def generate_idempotency_key(
        tenant_id: str,
        source_system: str,
        source_record_id: str,
        source_version: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate deterministic SHA-256 idempotency key:
        HASH(tenant_id:source_system:source_record_id:version:payload_hash)
        """
        payload_hash = ""
        if payload:
            serialized = json.dumps(payload, sort_keys=True, default=str)
            payload_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]

        raw_str = f"{tenant_id}:{source_system.upper()}:{str(source_record_id).upper()}:{source_version or '1'}:{payload_hash}"
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    def is_duplicate(self, idempotency_key: str) -> bool:
        """Check if an idempotency key has already been successfully committed."""
        return idempotency_key in self._processed_keys

    def register(self, idempotency_key: str) -> None:
        """Mark an idempotency key as committed."""
        self._processed_keys.add(idempotency_key)

    def unregister(self, idempotency_key: str) -> None:
        """Revoke key registration in case of downstream transaction rollback."""
        self._processed_keys.discard(idempotency_key)
