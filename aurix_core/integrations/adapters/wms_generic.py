"""Generic WMS Integration Adapter enforcing Zero-Fabrication Transformations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from aurix_core.integrations.base import BaseConnector
from aurix_core.integrations.contracts import (
    ConnectorConfig,
    ConnectorHealthState,
    IntegrationFamily,
)

logger = logging.getLogger("aurix_core.integrations.adapters.wms_generic")


class WMSInventoryRecord(BaseModel):
    """Normalized WMS inventory snapshot preserving nullability and strict zero-fabrication."""
    tenant_id: str
    sku_id: Optional[str] = None
    location_id: Optional[str] = None
    zone: Optional[str] = None
    bin_location: Optional[str] = None
    quantity_on_hand: Optional[float] = None
    quantity_allocated: Optional[float] = None
    quantity_available: Optional[float] = None
    unit_of_measure: Optional[str] = None
    lot_number: Optional[str] = None
    expiry_date: Optional[str] = None
    source_updated_at: Optional[str] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


class GenericWmsConnector(BaseConnector):
    """
    Standardized connector adapter for Generic WMS endpoints.
    Enforces strict zero-fabrication transforms on raw payloads.
    """

    def __init__(self, config: Optional[ConnectorConfig] = None, tenant_id: Optional[str] = None) -> None:
        if config is not None:
            super().__init__(config)
            self.tenant_id = config.tenant_id
        else:
            t_id = tenant_id or "default_tenant"
            cfg = ConnectorConfig(
                connector_id="WMS-GENERIC-01",
                tenant_id=t_id,
                name="Generic Warehouse Management System Adapter",
                family=IntegrationFamily.WMS,
                adapter_type="wms_generic",
            )
            super().__init__(cfg)
            self.tenant_id = t_id
        self.mock_dataset: List[Dict[str, Any]] = self.config.custom_settings.get("mock_dataset", [])

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

    def _safe_parse_float(self, value: Any) -> Optional[float]:
        """Safely parses float values without defaulting missing numbers to zero."""
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning("Failed parsing non-numeric value [%s] to float; propagating None.", value)
            return None

    def _safe_parse_iso_date(self, value: Any) -> Optional[str]:
        """Validates date strings without defaulting missing timestamps to current time."""
        if not value or not isinstance(value, str):
            return None
        clean_val = value.strip()
        if not clean_val:
            return None
        try:
            dt = datetime.fromisoformat(clean_val.replace("Z", "+00:00"))
            return dt.isoformat()
        except ValueError:
            logger.warning("Date string [%s] is not valid ISO format; preserving as-is or null.", clean_val)
            return str(clean_val)

    def transform_inventory_payload(
        self,
        raw_items: List[Dict[str, Any]],
    ) -> List[WMSInventoryRecord]:
        """Transforms raw WMS items into canonical schema adhering strictly to Zero-Fabrication."""
        transformed: List[WMSInventoryRecord] = []

        for item in raw_items:
            prod_val = (
                item.get("sku")
                or item.get("sku_id")
                or item.get("item_code")
                or item.get("product_id")
                or item.get("product_code")
                or item.get("id")
            )
            if isinstance(prod_val, (list, tuple)) and len(prod_val) > 1:
                sku = str(prod_val[1]).strip() if prod_val[1] is not None else None
            else:
                sku = str(prod_val).strip() if prod_val is not None and str(prod_val).strip() != "" else None

            loc_val = (
                item.get("warehouse")
                or item.get("location_id")
                or item.get("site_id")
                or item.get("location")
                or item.get("loc")
                or item.get("facility")
            )
            if isinstance(loc_val, (list, tuple)) and len(loc_val) > 1:
                loc = str(loc_val[1]).strip() if loc_val[1] is not None else None
            else:
                loc = str(loc_val).strip() if loc_val is not None and str(loc_val).strip() != "" else None

            qty_val = (
                item.get("qty_on_hand")
                or item.get("on_hand_qty")
                or item.get("quantity")
                or item.get("qty")
                or item.get("inventory_level")
            )

            record = WMSInventoryRecord(
                tenant_id=self.tenant_id,
                sku_id=sku,
                location_id=loc,
                zone=item.get("zone"),
                bin_location=item.get("bin") or item.get("bin_location") or item.get("bin_id"),
                quantity_on_hand=self._safe_parse_float(qty_val),
                quantity_allocated=self._safe_parse_float(item.get("qty_allocated") or item.get("reserved_qty")),
                quantity_available=self._safe_parse_float(item.get("qty_available")),
                unit_of_measure=item.get("uom") or item.get("unit"),
                lot_number=item.get("lot") or item.get("lot_number"),
                expiry_date=self._safe_parse_iso_date(item.get("expiry_date")),
                source_updated_at=self._safe_parse_iso_date(item.get("updated_at") or item.get("timestamp") or item.get("snapshot_date")),
                raw_payload=item,
            )
            transformed.append(record)

        return transformed

    def transform(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Canonical transform interface returning dictionary with 'inventory_level' for Phase 12 compliance."""
        transformed: List[Dict[str, Any]] = []
        for item in raw_records:
            prod_val = (
                item.get("sku")
                or item.get("sku_id")
                or item.get("item_code")
                or item.get("product_id")
                or item.get("id")
            )
            sku = (
                str(prod_val[1]).strip() if isinstance(prod_val, (list, tuple)) and len(prod_val) > 1
                else (str(prod_val).strip() if prod_val is not None and str(prod_val).strip() != "" else None)
            )

            loc_val = (
                item.get("warehouse")
                or item.get("location_id")
                or item.get("facility")
                or item.get("location")
            )
            loc = (
                str(loc_val[1]).strip() if isinstance(loc_val, (list, tuple)) and len(loc_val) > 1
                else (str(loc_val).strip() if loc_val is not None and str(loc_val).strip() != "" else None)
            )

            on_hand = self._safe_parse_float(
                item.get("on_hand_qty")
                or item.get("qty_on_hand")
                or item.get("quantity")
            )
            reserved = self._safe_parse_float(
                item.get("reserved_qty")
                or item.get("allocated_qty")
            )

            inventory_level = (on_hand - reserved) if (on_hand is not None and reserved is not None) else on_hand

            row: Dict[str, Any] = {
                "sku_id": sku,
                "inventory_level": inventory_level,
                "quantity_on_hand": on_hand,
                "quantity_reserved": reserved,
                "date": self._safe_parse_iso_date(item.get("snapshot_date") or item.get("updated_at")),
                "location_id": loc,
                "bin_location": item.get("bin_id") or item.get("bin_location"),
            }
            transformed.append(row)
        return transformed

    def fetch_inventory_snapshot(
        self,
        source_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Executes transformation against incoming WMS payloads."""
        start_time = datetime.now(timezone.utc)
        payloads = source_data or []

        try:
            records = self.transform_inventory_payload(payloads)
            serialized_records = [r.model_dump() for r in records]

            return {
                "execution_id": f"EXEC-WMS-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                "connector_id": self.config.connector_id,
                "tenant_id": self.tenant_id,
                "status": ConnectorHealthState.HEALTHY.value,
                "success": True,
                "records_processed": len(records),
                "records_failed": len(payloads) - len(records),
                "output_payload": {"inventory_records": serialized_records},
                "executed_at": start_time.isoformat(),
            }
        except Exception as e:
            logger.error("WMS Generic Adapter execution error: %s", str(e), exc_info=True)
            return {
                "execution_id": f"EXEC-WMS-ERR-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                "connector_id": self.config.connector_id,
                "tenant_id": self.tenant_id,
                "status": ConnectorHealthState.DEGRADED.value,
                "success": False,
                "records_processed": 0,
                "records_failed": len(payloads),
                "error_message": str(e),
                "executed_at": start_time.isoformat(),
            }


# Backward-compatible alias
GenericWMSAdapter = GenericWmsConnector
