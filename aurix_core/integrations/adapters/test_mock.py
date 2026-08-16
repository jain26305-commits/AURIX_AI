"""Deterministic synthetic test connector for Phase 12 test suites."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from aurix_core.integrations.base import BaseConnector, ConnectorException
from aurix_core.integrations.contracts import (
    ConnectorConfig,
    ConnectorHealthState,
)

logger = logging.getLogger("aurix.integrations.adapters.mock")


class MockIntegrationConnector(BaseConnector):
    """Configurable mock adapter for testing retries, rate limits, schema drifts, and incremental syncs."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self.force_auth_failure = bool(config.custom_settings.get("force_auth_failure", False))
        self.force_connection_failure = bool(config.custom_settings.get("force_connection_failure", False))
        self.force_rate_limit = bool(config.custom_settings.get("force_rate_limit", False))
        self.transient_failures_remaining = int(config.custom_settings.get("transient_failures_count", 0))
        self.mock_records: List[Dict[str, Any]] = config.custom_settings.get("mock_records", [])

    def connect(self) -> bool:
        if self.force_connection_failure:
            return False
        return True

    def authenticate(self) -> bool:
        if self.force_auth_failure:
            return False
        return True

    def health_check(self) -> ConnectorHealthState:
        if self.force_auth_failure:
            return ConnectorHealthState.AUTHENTICATION_ERROR
        if self.force_rate_limit:
            return ConnectorHealthState.RATE_LIMITED
        if self.force_connection_failure:
            return ConnectorHealthState.FAILED
        return ConnectorHealthState.HEALTHY

    def fetch_initial(
        self,
        batch_size: int = 1000,
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        return self.fetch_incremental(cursor=None, batch_size=batch_size)

    def fetch_incremental(
        self,
        cursor: Optional[Dict[str, Any]] = None,
        batch_size: int = 1000,
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        # Simulate transient error for retry backoff testing
        if self.transient_failures_remaining > 0:
            self.transient_failures_remaining -= 1
            raise ConnectorException(
                "Simulated transient network timeout.",
                connector_id=self.connector_id,
                code="TRANSIENT_TIMEOUT",
            )

        if self.force_rate_limit:
            raise ConnectorException(
                "Simulated external 429 rate limit exceeded.",
                connector_id=self.connector_id,
                code="RATE_LIMITED",
            )

        records = self.mock_records[:batch_size]
        new_cursor = {
            "last_sync_timestamp": datetime.now(timezone.utc).isoformat(),
            "batch_size_extracted": len(records),
            "offset": int((cursor or {}).get("offset", 0)) + len(records),
        }
        return records, new_cursor