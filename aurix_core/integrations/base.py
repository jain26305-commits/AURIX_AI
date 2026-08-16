"""Abstract Base Connector interface and lifecycle state manager for Phase 12 Universal Integration Hub."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from aurix_core.config.settings import settings
from aurix_core.integrations.auth import AuthProvider, AuthProviderFactory
from aurix_core.integrations.contracts import (
    ConnectorConfig,
    ConnectorHealthState,
    ConnectorLifecycleState,
    IntegrationHealthReport,
    SyncMode,
)


class ConnectorException(Exception):
    """Exception raised when an integration connector encounters an operational failure."""

    def __init__(self, message: str, connector_id: str, code: str = "CONNECTOR_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.connector_id = connector_id
        self.code = code


class BaseConnector(ABC):
    """Abstract Base Class establishing standard lifecycle hooks for external system integrations."""

    def __init__(self, config: ConnectorConfig) -> None:
        self.config = config
        self.connector_id = config.connector_id
        self.tenant_id = config.tenant_id
        self.lifecycle_state = ConnectorLifecycleState.CONFIGURED
        self.logger = logging.getLogger(f"aurix.integrations.{config.family.value.lower()}.{config.connector_id}")
        self.auth_provider: AuthProvider = AuthProviderFactory.create(config.auth_config)
        self.timeout_seconds = int(
            config.custom_settings.get("timeout_seconds", settings.connector_default_timeout_seconds)
        )
        self.max_retries = int(
            config.custom_settings.get("max_retries", settings.connector_max_retry_attempts)
        )

    def transition_state(self, new_state: ConnectorLifecycleState) -> None:
        """Transitions and logs the current execution state of the connector."""
        self.logger.debug(
            "Connector [%s] state transition: %s -> %s",
            self.connector_id,
            self.lifecycle_state.value,
            new_state.value,
        )
        self.lifecycle_state = new_state

    @abstractmethod
    def connect(self) -> bool:
        """Establishes network connection or verifies client reachability."""
        pass

    @abstractmethod
    def authenticate(self) -> bool:
        """Verifies or exchanges authentication credentials."""
        pass

    @abstractmethod
    def health_check(self) -> ConnectorHealthState:
        """Executes a lightweight ping/readiness check against the external system."""
        pass

    def discover_schema(self) -> Optional[Dict[str, Any]]:
        """Optional hook to inspect remote schema metadata and available entities."""
        return None

    @abstractmethod
    def fetch_initial(
        self,
        batch_size: int = 1000,
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Fetches the initial historical baseline dataset.
        Returns: (records, next_cursor_checkpoint)
        """
        pass

    @abstractmethod
    def fetch_incremental(
        self,
        cursor: Optional[Dict[str, Any]] = None,
        batch_size: int = 1000,
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Fetches new or modified records since the specified cursor checkpoint.
        Returns: (records, updated_cursor_checkpoint)
        """
        pass

    def transform(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalizes raw external payload keys into canonical AURIX format.
        Default implementation passes records through; specialized adapters override this.
        """
        return raw_records

    def validate(
        self,
        records: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Validates transformed records against schema constraints.
        Returns: (accepted_records, rejected_records, summary_stats)
        """
        # Default pass-through validation
        return records, [], {"total": len(records), "accepted": len(records), "rejected": 0}

    def disconnect(self) -> None:
        """Releases active network connections, sockets, and client sessions."""
        self.logger.debug("Disconnecting connector [%s]", self.connector_id)

    def execute_sync(
        self,
        mode: SyncMode = SyncMode.INCREMENTAL,
        cursor: Optional[Dict[str, Any]] = None,
        batch_size: int = 1000,
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Executes a complete extraction pass adhering to standard lifecycle transitions.
        Returns: (accepted_canonical_records, updated_cursor)
        """
        try:
            self.transition_state(ConnectorLifecycleState.AUTHENTICATING)
            if not self.authenticate():
                raise ConnectorException(
                    f"Authentication failed for connector '{self.connector_id}'.",
                    connector_id=self.connector_id,
                    code="AUTHENTICATION_FAILED",
                )

            self.transition_state(ConnectorLifecycleState.CONNECTED)
            if not self.connect():
                raise ConnectorException(
                    f"Connection failed for connector '{self.connector_id}'.",
                    connector_id=self.connector_id,
                    code="CONNECTION_FAILED",
                )

            self.transition_state(ConnectorLifecycleState.SYNCING)
            active_cursor = cursor or self.config.cursor

            if mode == SyncMode.INITIAL_FULL:
                raw_records, new_cursor = self.fetch_initial(batch_size=batch_size)
            else:
                raw_records, new_cursor = self.fetch_incremental(cursor=active_cursor, batch_size=batch_size)

            self.transition_state(ConnectorLifecycleState.NORMALIZING)
            transformed_records = self.transform(raw_records)

            self.transition_state(ConnectorLifecycleState.VALIDATING)
            accepted, _, _ = self.validate(transformed_records)

            self.transition_state(ConnectorLifecycleState.COMPLETED)
            return accepted, new_cursor

        except Exception as e:
            self.transition_state(ConnectorLifecycleState.FAILED)
            self.logger.error("Sync execution failed on connector [%s]: %s", self.connector_id, str(e))
            if isinstance(e, ConnectorException):
                raise e
            raise ConnectorException(str(e), connector_id=self.connector_id, code="SYNC_EXECUTION_ERROR") from e

        finally:
            self.disconnect()

    def get_health_report(self) -> IntegrationHealthReport:
        """Generates a health and reliability report for the connector."""
        health = self.health_check()
        return IntegrationHealthReport(
            connector_id=self.connector_id,
            tenant_id=self.tenant_id,
            health_state=health,
            last_successful_sync=self.config.last_sync_timestamp,
            last_attempt=self.config.updated_at,
            success_rate_pct=100.0 if health == ConnectorHealthState.HEALTHY else 50.0,
        )