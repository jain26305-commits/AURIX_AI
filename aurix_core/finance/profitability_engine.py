"""
AURIX Business Finance Intelligence — Customer & SKU Profitability Engine
Phase 21 Core Implementation.
Evaluates multi-tier profitability, margin dilution, and loss-maker identification.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from aurix_core.finance.contracts import (
    CustomerProfitabilitySummary,
    SkuProfitabilitySummary,
)


class ProfitabilityEngine:
    """Computes customer and SKU financial contribution rankings."""

    @classmethod
    def evaluate_customer_profitability(
        cls,
        customers: List[Dict[str, Any]],
        invoices: List[Dict[str, Any]],
        cogs_lookup: Dict[str, float],
    ) -> List[CustomerProfitabilitySummary]:
        """Compute customer-level revenue, COGS, and contribution margin."""
        cust_map: Dict[str, Dict[str, Any]] = {str(c.get("id")): c for c in customers}
        cust_metrics: Dict[str, Dict[str, float]] = {}

        for inv in invoices:
            c_id = str(inv.get("entity_id") or inv.get("customer_id") or "UNKNOWN")
            amt = float(inv.get("total_amount") or 0.0)
            disc = float(inv.get("discount_amount") or 0.0)
            net_amt = amt - disc
            cogs = cogs_lookup.get(c_id, net_amt * 0.60)  # Standard COGS fallback
            v_costs = float(inv.get("variable_cost_amount") or 0.0)

            if c_id not in cust_metrics:
                cust_metrics[c_id] = {"gross_rev": 0.0, "net_rev": 0.0, "cogs": 0.0, "v_costs": 0.0}

            cust_metrics[c_id]["gross_rev"] += amt
            cust_metrics[c_id]["net_rev"] += net_amt
            cust_metrics[c_id]["cogs"] += cogs
            cust_metrics[c_id]["v_costs"] += v_costs

        summaries: List[CustomerProfitabilitySummary] = []
        for c_id, m in cust_metrics.items():
            cust_data = cust_map.get(c_id, {})
            name = str(cust_data.get("customer_name") or f"Customer {c_id}")
            gp = m["net_rev"] - m["cogs"]
            gm_pct = round((gp / m["net_rev"] * 100.0), 2) if m["net_rev"] > 0 else 0.0
            cm = m["net_rev"] - m["cogs"] - m["v_costs"]

            tier = "HIGH_VALUE" if gm_pct >= 40.0 else ("STANDARD" if gm_pct >= 20.0 else "AT_RISK")

            summaries.append(
                CustomerProfitabilitySummary(
                    customer_id=c_id,
                    customer_name=name,
                    gross_revenue=round(m["gross_rev"], 2),
                    net_revenue=round(m["net_rev"], 2),
                    cogs=round(m["cogs"], 2),
                    gross_profit=round(gp, 2),
                    gross_margin_pct=gm_pct,
                    variable_costs=round(m["v_costs"], 2),
                    contribution_margin=round(cm, 2),
                    profitability_tier=tier,
                )
            )

        summaries.sort(key=lambda x: x.contribution_margin, reverse=True)
        return summaries

    @classmethod
    def evaluate_sku_profitability(
        cls,
        products: List[Dict[str, Any]],
        order_lines: List[Dict[str, Any]],
    ) -> List[SkuProfitabilitySummary]:
        """Compute SKU-level margin contribution and loss-maker classification."""
        prod_map: Dict[str, Dict[str, Any]] = {str(p.get("id")): p for p in products}
        sku_metrics: Dict[str, Dict[str, float]] = {}

        for line in order_lines:
            sku_id = str(line.get("sku_id") or "UNKNOWN")
            qty = float(line.get("quantity") or 1.0)
            price = float(line.get("unit_price") or 0.0)
            rev = qty * price

            prod_data = prod_map.get(sku_id, {})
            unit_cost = float(prod_data.get("unit_cost") or 0.0)
            cogs = qty * unit_cost

            if sku_id not in sku_metrics:
                sku_metrics[sku_id] = {"qty": 0.0, "rev": 0.0, "cogs": 0.0}

            sku_metrics[sku_id]["qty"] += qty
            sku_metrics[sku_id]["rev"] += rev
            sku_metrics[sku_id]["cogs"] += cogs

        summaries: List[SkuProfitabilitySummary] = []
        for sku_id, m in sku_metrics.items():
            prod_data = prod_map.get(sku_id, {})
            name = str(prod_data.get("name") or prod_data.get("sku_code") or sku_id)
            gp = m["rev"] - m["cogs"]
            gm_pct = round((gp / m["rev"] * 100.0), 2) if m["rev"] > 0 else 0.0
            unit_cm = round(gp / max(1.0, m["qty"]), 2)

            summaries.append(
                SkuProfitabilitySummary(
                    sku_id=sku_id,
                    sku_name=name,
                    units_sold=m["qty"],
                    gross_revenue=round(m["rev"], 2),
                    cogs=round(m["cogs"], 2),
                    gross_profit=round(gp, 2),
                    gross_margin_pct=gm_pct,
                    unit_contribution=unit_cm,
                    is_loss_maker=(gp < 0.0),
                )
            )

        summaries.sort(key=lambda x: x.gross_profit, reverse=True)
        return summaries
