"""
AURIX Manufacturing & Production Intelligence — Deterministic MRP Engine
Phase 23 Core Implementation.
Calculates Gross-to-Net requirements factoring demand, on-hand, open POs/WOs, safety stock, and lead times.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from aurix_core.manufacturing.bom_engine import BOMExplosionEngine
from aurix_core.manufacturing.contracts import (
    MRPPlannedOrder,
    MRPRunResult,
)


class MRPEngine:
    """Deterministic Material Requirements Planning (MRP) Engine."""

    @classmethod
    def calculate_mrp(
        cls,
        tenant_id: str,
        demand_schedule: List[Dict[str, Any]],
        bom_relationships: List[Dict[str, Any]],
        inventory_positions: List[Dict[str, Any]],
        open_purchase_orders: Optional[List[Dict[str, Any]]] = None,
        open_work_orders: Optional[List[Dict[str, Any]]] = None,
        products_lookup: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> MRPRunResult:
        """
        Executes MRP Gross-to-Net Netting:
        Net Requirement = max(0.0, Gross Requirement - Available OnHand - Scheduled Receipts + Safety Stock)
        """
        now = datetime.now(timezone.utc)
        prod_lookup = products_lookup or {}

        # 1. Map Inventory Positions (On-Hand, Safety Stock)
        stock_map: Dict[str, Dict[str, float]] = {}
        for pos in inventory_positions:
            sku = str(pos.get("sku_id") or pos.get("sku"))
            on_hand = float(pos.get("on_hand") or 0.0)
            safety = float(pos.get("safety_stock") or 0.0)
            if sku not in stock_map:
                stock_map[sku] = {"on_hand": 0.0, "safety": 0.0, "scheduled_receipts": 0.0}
            stock_map[sku]["on_hand"] += on_hand
            stock_map[sku]["safety"] = max(stock_map[sku]["safety"], safety)

        # 2. Map Scheduled Receipts (Open POs and Open WOs)
        if open_purchase_orders:
            for po in open_purchase_orders:
                sku = str(po.get("sku_id"))
                qty = float(po.get("quantity") or 0.0)
                if sku not in stock_map:
                    stock_map[sku] = {"on_hand": 0.0, "safety": 0.0, "scheduled_receipts": 0.0}
                stock_map[sku]["scheduled_receipts"] += qty

        if open_work_orders:
            for wo in open_work_orders:
                sku = str(wo.get("sku_id"))
                qty = float(wo.get("target_quantity") or 0.0) - float(wo.get("completed_quantity") or 0.0)
                if sku not in stock_map:
                    stock_map[sku] = {"on_hand": 0.0, "safety": 0.0, "scheduled_receipts": 0.0}
                stock_map[sku]["scheduled_receipts"] += max(0.0, qty)

        # 3. Explode Gross Requirements from Demand Schedule
        gross_requirements: Dict[str, Dict[str, Any]] = {}
        total_gross = 0.0

        for demand in demand_schedule:
            parent_sku = str(demand.get("sku_id"))
            target_qty = float(demand.get("quantity") or 0.0)
            due_date = demand.get("due_date") or (now + timedelta(days=14))
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
            if not due_date.tzinfo:
                due_date = due_date.replace(tzinfo=timezone.utc)

            total_gross += target_qty

            # Add parent demand
            if parent_sku not in gross_requirements:
                gross_requirements[parent_sku] = {"gross": 0.0, "due_date": due_date, "is_parent": True}
            gross_requirements[parent_sku]["gross"] += target_qty

            # Explode multi-level components if BOM exists
            try:
                explosion = BOMExplosionEngine.explode_bom(
                    parent_sku_id=parent_sku,
                    target_quantity=target_qty,
                    bom_relationships=bom_relationships,
                    products_lookup=prod_lookup,
                )
                for comp in explosion.components:
                    c_sku = comp.component_sku_id
                    comp_lead = comp.lead_time_days
                    comp_due = due_date - timedelta(days=comp_lead)
                    total_gross += comp.total_required_quantity

                    if c_sku not in gross_requirements:
                        gross_requirements[c_sku] = {"gross": 0.0, "due_date": comp_due, "is_parent": False}
                    gross_requirements[c_sku]["gross"] += comp.total_required_quantity
            except Exception:
                pass  # Fall back to single-level if no children

        # 4. Perform Netting and Generate Planned Orders
        planned_orders: List[MRPPlannedOrder] = []
        total_net = 0.0

        for sku, req in gross_requirements.items():
            gross_qty = req["gross"]
            stock_info = stock_map.get(sku, {"on_hand": 0.0, "safety": 0.0, "scheduled_receipts": 0.0})
            on_hand = stock_info["on_hand"]
            scheduled = stock_info["scheduled_receipts"]
            safety = stock_info["safety"]

            # Net Requirement formula
            net_qty = max(0.0, round(gross_qty - on_hand - scheduled + safety, 4))
            total_net += net_qty

            if net_qty > 0:
                p_info = prod_lookup.get(sku, {})
                lead_time = float(p_info.get("lead_time_days") or 7.0)
                order_type = "MANUFACTURE" if req.get("is_parent") else "PURCHASE"

                due_d = req["due_date"]
                release_d = due_d - timedelta(days=lead_time)

                planned_orders.append(
                    MRPPlannedOrder(
                        sku_id=sku,
                        order_type=order_type,
                        gross_requirement=round(gross_qty, 2),
                        available_inventory=round(on_hand, 2),
                        scheduled_receipts=round(scheduled, 2),
                        safety_stock=round(safety, 2),
                        net_requirement=round(net_qty, 2),
                        planned_order_quantity=round(net_qty, 2),
                        release_date=release_d,
                        due_date=due_d,
                        lead_time_days=lead_time,
                    )
                )

        planned_orders.sort(key=lambda x: x.release_date)

        return MRPRunResult(
            tenant_id=tenant_id,
            total_gross_requirement=round(total_gross, 2),
            total_net_requirement=round(total_net, 2),
            planned_orders=planned_orders,
            executed_at=now,
        )
