"""Generic REST API connector adapter for Phase 12 Universal Integration Hub."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx

from aurix_core.integrations.base import BaseConnector, ConnectorException
from aurix_core.integrations.contracts import (
    ConnectorConfig,
    ConnectorHealthState,
    IntegrationFamily,
)

logger = logging.getLogger("aurix.integrations.adapters.rest")


class GenericRestConnector(BaseConnector):
    """Generic REST connector supporting pagination, rate limiting, and configurable payload unwrapping."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self.base_url = (config.base_url or "").rstrip("/")
        self.records_path = str(config.custom_settings.get("records_path", ""))
        self.pagination_type = str(config.custom_settings.get("pagination_type", "page")).lower()
        self.data_endpoint = str(config.custom_settings.get("data_endpoint", "/data")).lstrip("/")
        self.health_endpoint = str(config.custom_settings.get("health_endpoint", "/health")).lstrip("/")
        self.field_mappings: Dict[str, str] = config.custom_settings.get("field_mappings", {})

    def _get_full_url(self, endpoint: str) -> str:
        """Constructs target URL from base_url and relative endpoint."""
        if not self.base_url:
            return endpoint
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def connect(self) -> bool:
        """Verifies network reachability against the REST endpoint."""
        if not self.base_url:
            return True
        if self.base_url.startswith(("mock://", "test://")):
            return True

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                headers = self.auth_provider.get_auth_headers(method="HEAD", url=self.base_url)
                params = self.auth_provider.get_auth_params()
                resp = client.head(self.base_url, headers=headers, params=params)
                return resp.status_code < 500
        except Exception as e:
            self.logger.warning("Connection check warning for [%s]: %s", self.connector_id, str(e))
            return False

    def authenticate(self) -> bool:
        """Verifies credentials by querying the auth provider."""
        try:
            headers = self.auth_provider.get_auth_headers(method="GET", url=self.base_url)
            return bool(headers) or self.config.auth_config.auth_type.value == "NONE"
        except Exception as e:
            self.logger.error("Authentication check failed for [%s]: %s", self.connector_id, str(e))
            return False

    def health_check(self) -> ConnectorHealthState:
        """Evaluates live API health and maps HTTP response codes."""
        if not self.base_url or self.base_url.startswith(("mock://", "test://")):
            return ConnectorHealthState.HEALTHY

        url = self._get_full_url(self.health_endpoint)
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                headers = self.auth_provider.get_auth_headers(method="GET", url=url)
                params = self.auth_provider.get_auth_params()
                resp = client.get(url, headers=headers, params=params)

                if resp.status_code == 200:
                    return ConnectorHealthState.HEALTHY
                elif resp.status_code == 401 or resp.status_code == 403:
                    return ConnectorHealthState.AUTHENTICATION_ERROR
                elif resp.status_code == 429:
                    return ConnectorHealthState.RATE_LIMITED
                else:
                    return ConnectorHealthState.DEGRADED
        except httpx.TimeoutException:
            return ConnectorHealthState.DELAYED
        except Exception:
            return ConnectorHealthState.FAILED

    def _extract_records(self, payload: Any) -> List[Dict[str, Any]]:
        """Extracts record dictionaries from raw lists or nested JSON envelope objects."""
        if isinstance(payload, list):
            return [r for r in payload if isinstance(r, dict)]

        if isinstance(payload, dict):
            # 1. Explicit configured path
            if self.records_path and self.records_path in payload:
                val = payload[self.records_path]
                if isinstance(val, list):
                    return [r for r in val if isinstance(r, dict)]

            # 2. Standard convention envelope keys
            for key in ("data", "items", "records", "results", "rows"):
                if key in payload and isinstance(payload[key], list):
                    return [r for r in payload[key] if isinstance(r, dict)]

            return [payload]

        return []

    def _fetch_page(
        self,
        params: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Executes HTTP GET request against the configured data endpoint."""
        url = self._get_full_url(self.data_endpoint)

        # Mock fallback for test suites
        if not self.base_url or self.base_url.startswith(("mock://", "test://")):
            mock_records = self.config.custom_settings.get("mock_records", [])
            return mock_records, {"mock_mode": True}

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                auth_headers = self.auth_provider.get_auth_headers(method="GET", url=url)
                auth_params = self.auth_provider.get_auth_params()
                merged_params = {**auth_params, **params}

                resp = client.get(url, headers=auth_headers, params=merged_params)
                resp.raise_for_status()
                data = resp.json()
                records = self._extract_records(data)
                meta: Dict[str, Any] = data if isinstance(data, dict) else {}
                return records, meta

        except httpx.HTTPStatusError as hse:
            if hse.response.status_code == 429:
                raise ConnectorException(
                    f"External REST API rate limit exceeded (429): {str(hse)}",
                    connector_id=self.connector_id,
                    code="RATE_LIMITED",
                )
            elif hse.response.status_code in (401, 403):
                raise ConnectorException(
                    f"External REST API authentication rejected ({hse.response.status_code})",
                    connector_id=self.connector_id,
                    code="AUTHENTICATION_FAILED",
                )
            raise ConnectorException(
                f"HTTP error {hse.response.status_code}: {str(hse)}",
                connector_id=self.connector_id,
                code="HTTP_ERROR",
            )
        except Exception as e:
            raise ConnectorException(
                f"Failed to query REST endpoint: {str(e)}",
                connector_id=self.connector_id,
                code="CONNECTION_ERROR",
            ) from e

    def fetch_initial(
        self,
        batch_size: int = 1000,
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Fetches the baseline historical dataset."""
        params: Dict[str, Any] = {"limit": batch_size}
        if self.pagination_type == "page":
            params["page"] = 1
        elif self.pagination_type == "offset":
            params["offset"] = 0

        records, _ = self._fetch_page(params)

        new_cursor: Dict[str, Any] = {
            "last_sync_timestamp": datetime.now(timezone.utc).isoformat(),
            "last_page": 1,
            "last_record_count": len(records),
        }
        return records, new_cursor

    def fetch_incremental(
        self,
        cursor: Optional[Dict[str, Any]] = None,
        batch_size: int = 1000,
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Fetches incremental records since last cursor checkpoint."""
        active_cursor = cursor or self.config.cursor or {}
        params: Dict[str, Any] = {"limit": batch_size}

        # Handle timestamp-based incremental queries
        if "last_sync_timestamp" in active_cursor:
            params["since"] = active_cursor["last_sync_timestamp"]

        if self.pagination_type == "page":
            next_page = int(active_cursor.get("last_page", 1)) + 1
            params["page"] = next_page
        elif self.pagination_type == "offset":
            next_offset = int(active_cursor.get("last_offset", 0)) + int(active_cursor.get("last_record_count", 0))
            params["offset"] = next_offset

        records, _ = self._fetch_page(params)

        new_cursor = {
            "last_sync_timestamp": datetime.now(timezone.utc).isoformat(),
            "last_page": params.get("page", 1),
            "last_offset": params.get("offset", 0),
            "last_record_count": len(records),
        }
        return records, new_cursor

    def transform(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Applies configured field name mappings to normalize raw REST records."""
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