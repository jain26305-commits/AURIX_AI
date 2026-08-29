"""
AURIX Manufacturing & Production Intelligence — Production Revenue-at-Risk Engine
Phase 23 Core Implementation.
Quantifies commercial sales revenue exposed due to unfulfilled production shortages.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.manufacturing.contracts import (
    ProductionRevenueAtRiskItem,
    ProductionRevenueAtRiskReport,
)


class RevenueAtRiskEngine:
    """Bridges manufacturing bottlenecks to Phase 22 commercial sales orders."""

    @classmethod
    def evaluate_revenue_at_risk(
        cls,
        tenant_id: str,
        delayed_work_orders: List[Dict[str, Any]],
        sales_orders: List[Dict[str, Any]],
        period_key: str = "CURRENT",
    ) -> ProductionRevenueAtRiskReport:
        """
        Revenue at Risk = Shortage Quantity * Commercial Selling Price
        """
        # Map SKU selling prices from sales orders
        sku_price_map: Dict[str, float] = {}
        order_cust_map: Dict[str, str] = {}
        for so in sales_orders:
            sku = str(so.get("sku_id") or "SKU-GEN")
            price = float(so.get("unit_price") or float(so.get("total_amount") or 100.0) / max(1.0, float(so.get("quantity") or 1.0)))
            sku_price_map[sku] = price
            order_cust_map[sku] = str(so.get("customer_id") or "CUST-UNKNOWN")

        items: List[ProductionRevenueAtRiskItem] = []
        total_risk = 0.0

        for wo in delayed_work_orders:
            wo_id = str(wo.get("id") or wo.get("work_order_number"))
            sku = str(wo.get("sku_id"))
            target_qty = float(wo.get("target_quantity") or 0.0)
            completed_qty = float(wo.get("completed_quantity") or 0.0)
            shortage = max(0.0, target_qty - completed_qty)

            unit_price = sku_price_map.get(sku, 120.0)
            risk_amt = round(shortage * unit_price, 2)
            total_risk += risk_amt

            items.append(
                ProductionRevenueAtRiskItem(
                    work_order_id=wo_id,
                    sku_id=sku,
                    shortage_quantity=round(shortage, 2),
                    unit_selling_price=round(unit_price, 2),
                    revenue_at_risk=risk_amt,
                    customer_id=order_cust_map.get(sku),
                )
            )

        items.sort(key=lambda x: x.revenue_at_risk, reverse=True)

        return ProductionRevenueAtRiskReport(
            tenant_id=tenant_id,
            period_key=period_key,
            total_revenue_at_risk=round(total_risk, 2),
            impacted_work_orders_count=len(items),
            items=items,
        )
