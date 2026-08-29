"""
AURIX Risk, Causal & External Intelligence — Signal-to-Enterprise Mapping Engine
Phase 26 Core Implementation.
Binds external signals to internal enterprise entities (Port -> Lane -> Supplier -> SKU -> Order).
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.risk.contracts import ExternalSignal, ExternalSignalMapping


class SignalMappingEngine:
    """Maps external reality signals directly to internal enterprise assets."""

    @classmethod
    def map_signals_to_entities(
        cls,
        tenant_id: str,
        signals: List[ExternalSignal],
        suppliers: List[Dict[str, Any]],
        shipments: List[Dict[str, Any]],
    ) -> List[ExternalSignalMapping]:
        """Bind geographic and lane signals to matching suppliers and active shipments."""
        mappings: List[ExternalSignalMapping] = []

        for sig in signals:
            geo = sig.geography.upper()

            # Map to Suppliers located in the affected geography
            for s in suppliers:
                s_id = str(s.get("id") or s.get("supplier_id"))
                s_country = str(s.get("country") or "").upper()
                if geo in s_country or s_country in geo:
                    mappings.append(
                        ExternalSignalMapping(
                            tenant_id=tenant_id,
                            signal_id=sig.signal_id,
                            entity_type="SUPPLIER",
                            entity_id=s_id,
                            mapping_rule=f"GEOGRAPHIC_ALIGNMENT_{geo}",
                            confidence=sig.confidence,
                        )
                    )

            # Map to Shipments traversing affected ports / lanes
            for shp in shipments:
                shp_id = str(shp.get("id") or shp.get("shipment_number"))
                carrier = str(shp.get("carrier") or "").upper()
                if sig.signal_type.value == "PORT_CONGESTION":
                    mappings.append(
                        ExternalSignalMapping(
                            tenant_id=tenant_id,
                            signal_id=sig.signal_id,
                            entity_type="SHIPMENT",
                            entity_id=shp_id,
                            mapping_rule="PORT_TRANSIT_INTERSECTION",
                            confidence=0.85,
                        )
                    )

        return mappings
