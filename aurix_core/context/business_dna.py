"""
AURIX Enterprise Business Context Graph — Business DNA Engine
Phase 24 Core Implementation.
Computes empirical operating intensity, customer/supplier concentration (HHI), and operating model classifications.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.context.contracts import BusinessDNASnapshot


class BusinessDNAEngine:
    """Derives empirical operating DNA without subjective categorization."""

    @staticmethod
    def calculate_hhi(shares: List[float]) -> float:
        """Compute Herfindahl-Hirschman Index (0 to 10,000 scale)."""
        if not shares:
            return 0.0
        total = sum(shares)
        if total == 0:
            return 0.0
        normalized = [(s / total) * 100.0 for s in shares]
        return round(sum(p ** 2 for p in normalized), 1)

    @classmethod
    def derive_business_dna(
        cls,
        tenant_id: str,
        orders: List[Dict[str, Any]],
        purchase_orders: List[Dict[str, Any]],
        inventory_valuation: float,
        annual_revenue: float,
        period_key: str = "CURRENT",
    ) -> BusinessDNASnapshot:
        """
        Derives empirical operating profile:
        - Customer Concentration HHI
        - Supplier Concentration HHI
        - Inventory Intensity = Inventory / Annual Revenue
        """
        # Customer Concentration
        cust_rev: Dict[str, float] = {}
        for o in orders:
            c = str(o.get("customer_id") or "CUST-GEN")
            amt = float(o.get("total_amount") or 0.0)
            cust_rev[c] = cust_rev.get(c, 0.0) + amt

        cust_hhi = cls.calculate_hhi(list(cust_rev.values()))

        # Supplier Spend Concentration
        supp_spend: Dict[str, float] = {}
        for po in purchase_orders:
            s = str(po.get("supplier_id") or "SUPP-GEN")
            amt = float(po.get("total_amount") or (float(po.get("quantity") or 1.0) * 100.0))
            supp_spend[s] = supp_spend.get(s, 0.0) + amt

        supp_hhi = cls.calculate_hhi(list(supp_spend.values()))

        # Operating Ratios
        inv_intensity = round((inventory_valuation / max(1.0, annual_revenue)) * 100.0, 1)

        # Classification based on empirical boundaries
        if inv_intensity >= 25.0:
            op_model = "CAPITAL_INTENSIVE_MANUFACTURING"
            complexity = "HIGH"
        elif cust_hhi >= 2500:
            op_model = "HIGH_CONCENTRATION_ENTERPRISE_B2B"
            complexity = "MODERATE"
        else:
            op_model = "HIGH_VELOCITY_DISTRIBUTION_ECOMMERCE"
            complexity = "STANDARD"

        return BusinessDNASnapshot(
            tenant_id=tenant_id,
            period_key=period_key,
            operating_model=op_model,
            customer_concentration_hhi=cust_hhi,
            supplier_concentration_hhi=supp_hhi,
            inventory_intensity_pct=inv_intensity,
            working_capital_intensity_pct=round(inv_intensity * 1.2, 1),
            manufacturing_complexity_tier=complexity,
        )
