"""
AURIX Enterprise Data Fabric — Backend High-Performance Aggregations
Phase 19 Core Implementation.
Performs high-throughput, tenant-isolated aggregations inside backend services.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AggregatedInventorySummary(BaseModel):
    """Materialized inventory metric rollup."""
    total_skus: int
    total_on_hand_units: float
    total_inventory_valuation: float
    total_locations: int
    low_stock_sku_count: int


class AggregatedOrderSummary(BaseModel):
    """Materialized sales order metric rollup."""
    total_orders: int
    total_order_value: float
    average_order_value: float
    pending_fulfillment_count: int


class DataFabricAggregator:
    """Executes performant in-engine multi-entity aggregations."""

    @staticmethod
    def aggregate_inventory_positions(
        positions: List[Dict[str, Any]],
        safety_stock_threshold: float = 10.0,
    ) -> AggregatedInventorySummary:
        """Compute consolidated inventory valuation and stock levels."""
        total_skus = len({p.get("sku") or p.get("sku_id") for p in positions if p.get("sku") or p.get("sku_id")})
        locations = {p.get("location") or p.get("warehouse_id") for p in positions if p.get("location") or p.get("warehouse_id")}

        total_units = 0.0
        total_val = 0.0
        low_stock = 0

        for p in positions:
            qty = float(p.get("quantity") or p.get("on_hand_units") or 0.0)
            cost = float(p.get("unit_cost") or p.get("cost_price") or 0.0)
            total_units += qty
            total_val += (qty * cost)
            if qty <= safety_stock_threshold:
                low_stock += 1

        return AggregatedInventorySummary(
            total_skus=total_skus,
            total_on_hand_units=round(total_units, 2),
            total_inventory_valuation=round(total_val, 2),
            total_locations=len(locations),
            low_stock_sku_count=low_stock,
        )

    @staticmethod
    def aggregate_orders(orders: List[Dict[str, Any]]) -> AggregatedOrderSummary:
        """Compute consolidated sales orders rollup."""
        total_orders = len(orders)
        if total_orders == 0:
            return AggregatedOrderSummary(
                total_orders=0,
                total_order_value=0.0,
                average_order_value=0.0,
                pending_fulfillment_count=0,
            )

        total_val = 0.0
        pending = 0

        for o in orders:
            val = float(o.get("total_amount") or o.get("total_value") or 0.0)
            status = str(o.get("status") or "").upper()
            total_val += val
            if status in ("PENDING", "PROCESSING", "OPEN"):
                pending += 1

        return AggregatedOrderSummary(
            total_orders=total_orders,
            total_order_value=round(total_val, 2),
            average_order_value=round(total_val / total_orders, 2),
            pending_fulfillment_count=pending,
        )
