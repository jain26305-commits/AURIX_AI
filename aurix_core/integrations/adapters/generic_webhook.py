"""Generic secure Webhook intake adapter for Phase 12 Universal Integration Hub."""

import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from aurix_core.config.settings import settings
from aurix_core.integrations.auth import SecretResolver
from aurix_core.integrations.base import BaseConnector, ConnectorException
from aurix_core.integrations.contracts import (
    ConnectorConfig,
    ConnectorHealthState,
    WebhookEventPayload,
)

logger = logging.getLogger("aurix.integrations.adapters.webhook")


class GenericWebhookAdapter(BaseConnector):
    """Secure webhook intake adapter supporting HMAC-SHA256 verification and replay protection."""

    _processed_event_ids: Set[str] = set()
    _buffered_events: Dict[str, List[Dict[str, Any]]] = {}

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self.secret_header = str(config.custom_settings.get("signature_header", "X-Signature-SHA256"))
        self.timestamp_header = str(config.custom_settings.get("timestamp_header", "X-Timestamp"))
        self.tolerance_seconds = int(
            config.custom_settings.get(
                "timestamp_tolerance_seconds",
                settings.webhook_timestamp_tolerance_seconds,
            )
        )
        self.field_mappings: Dict[str, str] = config.custom_settings.get("field_mappings", {})

    @classmethod
    def clear_test_buffers(cls) -> None:
        """Clears in-memory event deduplication and buffer caches for test suites."""
        cls._processed_event_ids.clear()
        cls._buffered_events.clear()

    def connect(self) -> bool:
        """Webhook endpoints are passive listeners; returns True when active."""
        return self.config.enabled

    def authenticate(self) -> bool:
        """Verifies secret key presence for signature verification."""
        if not self.config.auth_config.secret_ref:
            return True
        try:
            secret = SecretResolver.resolve(self.config.auth_config.secret_ref)
            return bool(secret)
        except Exception as e:
            self.logger.error("Failed to resolve webhook signing secret: %s", str(e))
            return False

    def health_check(self) -> ConnectorHealthState:
        """Evaluates webhook receiver readiness."""
        if not self.config.enabled:
            return ConnectorHealthState.DEGRADED
        if self.config.auth_config.secret_ref:
            try:
                SecretResolver.resolve(self.config.auth_config.secret_ref)
            except Exception:
                return ConnectorHealthState.AUTHENTICATION_ERROR
        return ConnectorHealthState.HEALTHY

    def verify_timestamp(self, timestamp_str: str) -> bool:
        """Verifies that the incoming request timestamp is within the tolerance window."""
        try:
            ts_val = float(timestamp_str)
        except (ValueError, TypeError):
            return False

        now = time.time()
        return abs(now - ts_val) <= self.tolerance_seconds

    def verify_signature(
        self,
        raw_body: bytes,
        signature: str,
        timestamp: Optional[str] = None,
    ) -> bool:
        """Validates HMAC-SHA256 signature against the raw payload and timestamp."""
        if not self.config.auth_config.secret_ref:
            return True

        secret = SecretResolver.resolve(self.config.auth_config.secret_ref)
        message = (f"{timestamp}.".encode("utf-8") if timestamp else b"") + raw_body
        computed = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()

        return hmac.compare_digest(computed.lower(), signature.strip().lower())

    def ingest_event(
        self,
        event: WebhookEventPayload,
        raw_body: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """
        Validates security tokens, checks replay guards, and stages the incoming webhook event.
        """
        # 1. Replay attack guard: check duplicate event_id
        if event.event_id in self._processed_event_ids:
            raise ConnectorException(
                f"Duplicate webhook event ID '{event.event_id}' rejected (replay protection).",
                connector_id=self.connector_id,
                code="DUPLICATE_EVENT",
            )

        # 2. Timestamp verification if present
        ts_header_val = event.headers.get(self.timestamp_header) or event.event_timestamp
        if ts_header_val and not self.verify_timestamp(ts_header_val):
            # Fallback check if provided in ISO format
            try:
                dt = datetime.fromisoformat(ts_header_val.replace("Z", "+00:00"))
                if not self.verify_timestamp(str(dt.timestamp())):
                    raise ConnectorException(
                        f"Webhook timestamp drift exceeds tolerance window of {self.tolerance_seconds}s.",
                        connector_id=self.connector_id,
                        code="TIMESTAMP_DRIFT_EXCEEDED",
                    )
            except Exception as e:
                if isinstance(e, ConnectorException):
                    raise e
                raise ConnectorException(
                    "Invalid webhook timestamp header.",
                    connector_id=self.connector_id,
                    code="INVALID_TIMESTAMP",
                ) from e

        # 3. Signature verification if configured
        sig_header_val = event.signature or event.headers.get(self.secret_header)
        if self.config.auth_config.secret_ref and sig_header_val:
            body_bytes = raw_body or json.dumps(event.payload, default=str).encode("utf-8")
            if not self.verify_signature(body_bytes, sig_header_val, ts_header_val):
                raise ConnectorException(
                    "Invalid webhook HMAC signature.",
                    connector_id=self.connector_id,
                    code="INVALID_SIGNATURE",
                )

        # 4. Stage event payload
        self._processed_event_ids.add(event.event_id)
        record = dict(event.payload)
        record["_webhook_event_id"] = event.event_id
        record["_webhook_received_at"] = event.received_timestamp

        self._buffered_events.setdefault(self.connector_id, []).append(record)
        return record

    def fetch_initial(
        self,
        batch_size: int = 1000,
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Returns empty baseline for event-driven webhooks."""
        return [], {"last_sync_timestamp": datetime.now(timezone.utc).isoformat()}

    def fetch_incremental(
        self,
        cursor: Optional[Dict[str, Any]] = None,
        batch_size: int = 1000,
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Pulls and drains buffered webhook events staged by incoming webhook requests."""
        buffer = self._buffered_events.get(self.connector_id, [])
        records_to_flush = buffer[:batch_size]
        self._buffered_events[self.connector_id] = buffer[batch_size:]

        new_cursor = {
            "last_sync_timestamp": datetime.now(timezone.utc).isoformat(),
            "flushed_records_count": len(records_to_flush),
            "remaining_buffered_count": len(self._buffered_events.get(self.connector_id, [])),
        }
        return records_to_flush, new_cursor

    def transform(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalizes field names from webhook events into canonical schema."""
        if not self.field_mappings:
            return raw_records

        transformed: List[Dict[str, Any]] = []
        for row in raw_records:
            normalized_row = dict(row)
            for src_col, canon_field in self.field_mappings.items():
                if src_col in row:
                    normalized_row[canon_field] = row[src_col]
            transformed.append(normalized_row)
        return transformed