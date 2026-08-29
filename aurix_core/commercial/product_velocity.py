"""
AURIX Enterprise Sales & Commercial Intelligence — Product Velocity & Attach Engine
Phase 22 Core Implementation.
Categorizes catalog into Fast/Slow/Dead movement and calculates cross-sell basket attach rates.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.commercial.contracts import (
    ProductVelocitySummary,
    VelocityTier,
)


class ProductVelocityEngine:
    """Analyzes product commercial sales velocity, attach rates, and catalog concentration."""

    @classmethod
    def evaluate_velocity(
        cls,
        products: List[Dict[str, Any]],
        order_lines: List[Dict[str, Any]],
        total_orders_count: int = 100,
    ) -> List[ProductVelocitySummary]:
        """Categorize catalog velocity and attach rates."""
        prod_map = {str(p.get("id")): p for p in products}
        sku_stats: Dict[str, Dict[str, Any]] = {}
        order_baskets: Dict[str, List[str]] = {}

        for line in order_lines:
            sku = str(line.get("sku_id") or "UNKNOWN")
            o_id = str(line.get("order_id") or "O-0")
            qty = float(line.get("quantity") or 1.0)
            price = float(line.get("unit_price") or 0.0)

            if sku not in sku_stats:
                sku_stats[sku] = {"qty": 0.0, "rev": 0.0, "order_ids": set()}
            sku_stats[sku]["qty"] += qty
            sku_stats[sku]["rev"] += qty * price
            sku_stats[sku]["order_ids"].add(o_id)

            if o_id not in order_baskets:
                order_baskets[o_id] = []
            order_baskets[o_id].append(sku)

        summaries: List[ProductVelocitySummary] = []
        for p_id, p_info in prod_map.items():
            stats = sku_stats.get(p_id, {"qty": 0.0, "rev": 0.0, "order_ids": set()})
            units = stats["qty"]
            rev = stats["rev"]
            orders_present = len(stats["order_ids"])

            # Velocity Classification
            if units >= 50:
                vel_tier = VelocityTier.FAST_MOVING
            elif units >= 15:
                vel_tier = VelocityTier.STEADY
            elif units > 0:
                vel_tier = VelocityTier.SLOW_MOVING
            else:
                vel_tier = VelocityTier.DEAD_STOCK

            attach_rate = round((orders_present / max(1, total_orders_count)) * 100.0, 1)

            # Find top cross-sell co-occurrences
            co_occurrences: Dict[str, int] = {}
            for o_id in stats["order_ids"]:
                basket = order_baskets.get(o_id, [])
                for co_sku in basket:
                    if co_sku != p_id:
                        co_occurrences[co_sku] = co_occurrences.get(co_sku, 0) + 1

            top_cross_sells = sorted(co_occurrences.keys(), key=lambda k: co_occurrences[k], reverse=True)[:3]

            summaries.append(
                ProductVelocitySummary(
                    sku_id=p_id,
                    sku_name=str(p_info.get("name") or p_info.get("sku_code") or p_id),
                    category=str(p_info.get("category") or "GENERAL"),
                    velocity_tier=vel_tier,
                    units_sold=units,
                    gross_revenue=round(rev, 2),
                    gross_margin_pct=35.0,
                    order_attach_rate_pct=attach_rate,
                    top_cross_sell_skus=top_cross_sells,
                )
            )

        summaries.sort(key=lambda x: x.units_sold, reverse=True)
        return summaries
