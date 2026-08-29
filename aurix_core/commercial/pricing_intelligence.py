"""
AURIX Enterprise Sales & Commercial Intelligence — Pricing & PVM Engine
Phase 22 Core Implementation.
Calculates Price-Volume-Mix (PVM) variance decomposition and audits discount leakage.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.commercial.config import CommercialConfigManager
from aurix_core.commercial.contracts import (
    DiscountLeakageAudit,
    PVMDecomposition,
)


class PricingIntelligenceEngine:
    """Decomposes revenue changes into Price, Volume, and Mix effects."""

    @classmethod
    def decompose_pvm(
        cls,
        tenant_id: str,
        baseline_sales: List[Dict[str, Any]],
        current_sales: List[Dict[str, Any]],
        baseline_period: str = "PRIOR_PERIOD",
        current_period: str = "CURRENT_PERIOD",
        currency: str = "USD",
    ) -> PVMDecomposition:
        """
        Price Effect  = Σ (P1 - P0) * Q1
        Volume Effect = Σ (Q1 - Q0) * P0
        Mix Effect    = Total Change - Price Effect - Volume Effect
        """
        base_map = {str(r.get("sku_id")): {"qty": float(r.get("quantity") or 0.0), "price": float(r.get("unit_price") or 0.0)} for r in baseline_sales}
        curr_map = {str(r.get("sku_id")): {"qty": float(r.get("quantity") or 0.0), "price": float(r.get("unit_price") or 0.0)} for r in current_sales}

        total_base_rev = sum(d["qty"] * d["price"] for d in base_map.values())
        total_curr_rev = sum(d["qty"] * d["price"] for d in curr_map.values())
        total_change = total_curr_rev - total_base_rev

        price_effect = 0.0
        volume_effect = 0.0

        all_skus = set(base_map.keys()).union(set(curr_map.keys()))
        for sku in all_skus:
            p0 = base_map.get(sku, {}).get("price", 0.0)
            q0 = base_map.get(sku, {}).get("qty", 0.0)
            p1 = curr_map.get(sku, {}).get("price", p0)
            q1 = curr_map.get(sku, {}).get("qty", 0.0)

            price_effect += (p1 - p0) * q1
            volume_effect += (q1 - q0) * p0

        mix_effect = total_change - price_effect - volume_effect

        p_pct = round((price_effect / max(1.0, abs(total_base_rev))) * 100.0, 2)
        v_pct = round((volume_effect / max(1.0, abs(total_base_rev))) * 100.0, 2)
        m_pct = round((mix_effect / max(1.0, abs(total_base_rev))) * 100.0, 2)

        return PVMDecomposition(
            tenant_id=tenant_id,
            baseline_period=baseline_period,
            current_period=current_period,
            currency=currency,
            baseline_revenue=round(total_base_rev, 2),
            current_revenue=round(total_curr_rev, 2),
            total_revenue_change=round(total_change, 2),
            price_effect=round(price_effect, 2),
            volume_effect=round(volume_effect, 2),
            mix_effect=round(mix_effect, 2),
            price_effect_pct=p_pct,
            volume_effect_pct=v_pct,
            mix_effect_pct=m_pct,
            notes="Deterministic Price-Volume-Mix decomposition completed.",
        )

    @classmethod
    def audit_discount_leakage(
        cls,
        tenant_id: str,
        orders: List[Dict[str, Any]],
    ) -> DiscountLeakageAudit:
        """Audit concession leakage and off-invoice discount breaches."""
        config = CommercialConfigManager.get_config(tenant_id)

        gross_rev = 0.0
        total_disc = 0.0
        unauth_disc = 0.0
        leakage_count = 0
        cust_discounts: Dict[str, Dict[str, float]] = {}

        for o in orders:
            amt = float(o.get("total_amount") or 0.0)
            disc = float(o.get("discount_amount") or 0.0)
            c_id = str(o.get("customer_id") or "UNKNOWN")

            gross_rev += amt
            total_disc += disc

            rate = (disc / max(1.0, amt)) * 100.0
            if rate > config.max_authorized_discount_pct:
                excess = disc - (amt * (config.max_authorized_discount_pct / 100.0))
                unauth_disc += excess
                leakage_count += 1

            if c_id not in cust_discounts:
                cust_discounts[c_id] = {"gross": 0.0, "disc": 0.0}
            cust_discounts[c_id]["gross"] += amt
            cust_discounts[c_id]["disc"] += disc

        overall_rate = round((total_disc / max(1.0, gross_rev)) * 100.0, 2)

        top_leakage_custs = [
            {
                "customer_id": c_id,
                "gross_revenue": round(data["gross"], 2),
                "discount_granted": round(data["disc"], 2),
                "discount_pct": round((data["disc"] / max(1.0, data["gross"])) * 100.0, 2),
            }
            for c_id, data in sorted(cust_discounts.items(), key=lambda x: x[1]["disc"], reverse=True)
            if data["disc"] > 0
        ]

        return DiscountLeakageAudit(
            tenant_id=tenant_id,
            total_gross_revenue=round(gross_rev, 2),
            total_discounts_granted=round(total_disc, 2),
            overall_discount_rate_pct=overall_rate,
            unauthorized_discounts_total=round(unauth_disc, 2),
            leakage_count=leakage_count,
            top_discounted_accounts=top_leakage_custs[:10],
        )
