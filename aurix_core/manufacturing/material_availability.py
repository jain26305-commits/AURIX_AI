"""
AURIX Manufacturing & Production Intelligence — Material Availability Engine
Phase 23 Core Implementation.
Evaluates component availability, shortages, lead-time gaps, and pegs shortages to work orders.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
from aurix_core.manufacturing.contracts import (
    MaterialAvailabilityItem,
    MaterialAvailabilityReport,
)


class MaterialAvailabilityEngine:
    """Evaluates material readiness and identifies production shortage bottlenecks."""

    @classmethod
    def evaluate_availability(
        cls,
        tenant_id: str,
        required_components: List[Dict[str, Any]],
        inventory_positions: List[Dict[str, Any]],
        open_purchase_orders: List[Dict[str, Any]] | None = None,
        work_order_id: str | None = None,
    ) -> MaterialAvailabilityReport:
        """
        Evaluates material readiness against stock on hand and scheduled receipts.
        Shortage = max(0.0, Required - NetAvailable)
        """
        stock_map = {str(p.get("sku_id") or p.get("sku")): float(p.get("on_hand") or 0.0) for p in inventory_positions}
        po_map = {str(po.get("sku_id")): float(po.get("quantity") or 0.0) for po in (open_purchase_orders or [])}

        items: List[MaterialAvailabilityItem] = []
        shortage_count = 0
        total_required = 0.0
        total_satisfied = 0.0

        for req in required_components:
            sku = str(req.get("sku_id") or req.get("component_sku_id"))
            name = str(req.get("sku_name") or req.get("component_name") or sku)
            qty_req = float(req.get("quantity") or req.get("total_required_quantity") or 0.0)
            total_required += qty_req

            on_hand = stock_map.get(sku, 0.0)
            on_order = po_map.get(sku, 0.0)
            net_avail = on_hand + on_order

            shortage = max(0.0, round(qty_req - net_avail, 4))
            is_critical = shortage > 0 and on_hand < (qty_req * 0.5)

            if shortage > 0:
                shortage_count += 1
                total_satisfied += max(0.0, net_avail)
            else:
                total_satisfied += qty_req

            items.append(
                MaterialAvailabilityItem(
                    sku_id=sku,
                    sku_name=name,
                    required_quantity=round(qty_req, 2),
                    on_hand_quantity=round(on_hand, 2),
                    on_order_quantity=round(on_order, 2),
                    allocated_quantity=0.0,
                    net_available_quantity=round(net_avail, 2),
                    shortage_quantity=round(shortage, 2),
                    is_critical_shortage=is_critical,
                )
            )

        readiness_pct = round((total_satisfied / max(1.0, total_required)) * 100.0, 1)

        return MaterialAvailabilityReport(
            tenant_id=tenant_id,
            work_order_id=work_order_id,
            readiness_pct=min(100.0, readiness_pct),
            total_components_checked=len(items),
            shortage_items_count=shortage_count,
            items=items,
        )
