"""Odoo ERP connector adapter for Phase 12 Universal Integration Hub enforcing Zero-Fabrication."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from aurix_core.integrations.base import BaseConnector
from aurix_core.integrations.contracts import (
    ConnectorConfig,
    ConnectorHealthState,
)

logger = logging.getLogger("aurix.integrations.adapters.odoo")


class OdooErpConnector(BaseConnector):
    """Reference ERP adapter for Odoo normalizing inventory and orders to canonical schemas without fabrication."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self.model_name = str(config.custom_settings.get("model_name", "stock.quant"))
        self.mock_dataset: List[Dict[str, Any]] = config.custom_settings.get("mock_dataset", [])

    def connect(self) -> bool:
        return self.config.enabled

    def authenticate(self) -> bool:
        return True

    def health_check(self) -> ConnectorHealthState:
        return ConnectorHealthState.HEALTHY if self.config.enabled else ConnectorHealthState.DEGRADED

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
        records = self.mock_dataset[:batch_size]
        new_cursor = {
            "last_sync_timestamp": datetime.now(timezone.utc).isoformat(),
            "records_count": len(records),
        }
        return records, new_cursor

    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely parses float values without defaulting missing numbers to zero."""
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _safe_string(self, value: Any) -> Optional[str]:
        """Safely parses string values."""
        if value is None:
            return None
        s = str(value).strip()
        return s if s else None

    def transform(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalizes Odoo stock.quant / sale.order fields to canonical AURIX entities.
        Adheres strictly to Zero-Fabrication: missing metrics and locations propagate as None.
        """
        transformed: List[Dict[str, Any]] = []

        for row in raw_records:
            prod_val = row.get("product_id")
            sku_id = (
                str(prod_val[1]).strip() if isinstance(prod_val, (list, tuple)) and len(prod_val) > 1 and prod_val[1] is not None
                else self._safe_string(prod_val)
            )

            resolved_sku = (
                sku_id
                or self._safe_string(row.get("default_code"))
                or self._safe_string(row.get("sku_id"))
            )

            loc_val = row.get("location_id")
            resolved_loc = (
                str(loc_val[1]).strip() if isinstance(loc_val, (list, tuple)) and len(loc_val) > 1 and loc_val[1] is not None
                else self._safe_string(loc_val)
            )

            canon_row: Dict[str, Any] = {
                "sku_id": resolved_sku,
                "inventory_level": self._safe_float(
                    row.get("quantity") or row.get("qty_available") or row.get("inventory_level")
                ),
                "date": self._safe_string(row.get("write_date") or row.get("date")),
                "unit_cost": self._safe_float(
                    row.get("standard_price") or row.get("unit_cost")
                ),
                "location_id": resolved_loc,
            }
            transformed.append(canon_row)

        return transformed