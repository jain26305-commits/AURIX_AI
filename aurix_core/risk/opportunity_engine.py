"""
AURIX Risk, Causal & External Intelligence — Opportunity Detection & Ranking Engine
Phase 26 Core Implementation.
Identifies and ranks positive operational upside (Procurement savings, Freight consolidation, Working Capital release).
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.risk.contracts import (
    OpportunityFinding,
    OpportunityType,
)


class OpportunityEngine:
    """Detects and ranks operational and financial upside opportunities."""

    @classmethod
    def detect_opportunities(
        cls,
        tenant_id: str,
        purchase_orders: List[Dict[str, Any]],
        inventory_items: List[Dict[str, Any]],
        invoices: List[Dict[str, Any]],
    ) -> List[OpportunityFinding]:
        """Discover actionable operational opportunities across procurement and working capital."""
        opportunities: List[OpportunityFinding] = []

        # 1. Working Capital Release from Excess Inventory
        for item in inventory_items:
            sku_id = str(item.get("sku_id") or item.get("sku"))
            on_hand = float(item.get("on_hand") or 0.0)
            safety = float(item.get("safety_stock") or 0.0)
            cost = float(item.get("unit_cost") or 50.0)

            excess_qty = max(0.0, on_hand - (safety * 2.0))
            if excess_qty > 10.0:
                val = round(excess_qty * cost, 2)
                opportunities.append(
                    OpportunityFinding(
                        tenant_id=tenant_id,
                        opportunity_type=OpportunityType.WORKING_CAPITAL_RELEASE,
                        entity_type="SKU",
                        entity_id=sku_id,
                        title=f"Working Capital Release: {sku_id}",
                        description=f"Stock level ({on_hand:.0f}) exceeds double safety stock. Liquidating {excess_qty:.0f} units recovers capital.",
                        potential_value_usd=val,
                        probability=0.90,
                        confidence=0.95,
                        priority_rank=1 if val > 20000 else 2,
                        evidence={"excess_quantity": excess_qty, "unit_cost": cost},
                    )
                )

        # 2. Procurement Early-Payment Discount Opportunities
        for inv in invoices:
            inv_id = str(inv.get("id") or inv.get("invoice_number"))
            amt = float(inv.get("total_amount") or 0.0)
            if amt > 10000.0:
                discount_val = round(amt * 0.02, 2)  # 2% dynamic discounting
                opportunities.append(
                    OpportunityFinding(
                        tenant_id=tenant_id,
                        opportunity_type=OpportunityType.PROCUREMENT_SAVINGS,
                        entity_type="INVOICE",
                        entity_id=inv_id,
                        title=f"Early-Payment Discount on Invoice {inv_id}",
                        description=f"Settling invoice within 10 days captures a 2% discount (${discount_val:,.2f}).",
                        potential_value_usd=discount_val,
                        probability=0.95,
                        confidence=0.98,
                        priority_rank=1,
                        evidence={"invoice_amount": amt, "discount_pct": 2.0},
                    )
                )

        opportunities.sort(key=lambda x: x.potential_value_usd, reverse=True)
        return opportunities
