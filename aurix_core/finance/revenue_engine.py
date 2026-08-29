"""
AURIX Business Finance Intelligence — Revenue Intelligence Engine
Phase 21 Core Implementation.
Calculates Gross and Net revenue with deduction auditability.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from aurix_core.finance.contracts import RevenueBreakdown


class RevenueEngine:
    """Deterministic Revenue Intelligence engine enforcing Gross to Net integrity."""

    @classmethod
    def calculate_revenue(
        cls,
        tenant_id: str,
        orders: List[Dict[str, Any]],
        invoices: Optional[List[Dict[str, Any]]] = None,
        returns: Optional[List[Dict[str, Any]]] = None,
        period_key: str = "CURRENT",
        currency: str = "USD",
    ) -> RevenueBreakdown:
        """
        Net Revenue = Gross Revenue - Returns - Discounts - Credit Notes
        """
        gross_rev = 0.0
        discounts = 0.0
        by_customer: Dict[str, float] = {}
        by_sku: Dict[str, float] = {}
        by_channel: Dict[str, float] = {}
        by_geo: Dict[str, float] = {}

        # 1. Process Orders / Invoices for Gross Revenue & Deductions
        source_records = invoices if (invoices and len(invoices) > 0) else orders

        for rec in source_records:
            amt = float(rec.get("total_amount") or 0.0)
            disc = float(rec.get("discount_amount") or 0.0)
            gross_rev += amt
            discounts += disc

            cust = str(rec.get("customer_id") or rec.get("entity_id") or "UNKNOWN")
            sku = str(rec.get("sku_id") or "GENERAL")
            channel = str(rec.get("channel") or "DIRECT")
            geo = str(rec.get("country") or "GLOBAL")

            by_customer[cust] = round(by_customer.get(cust, 0.0) + (amt - disc), 2)
            by_sku[sku] = round(by_sku.get(sku, 0.0) + (amt - disc), 2)
            by_channel[channel] = round(by_channel.get(channel, 0.0) + (amt - disc), 2)
            by_geo[geo] = round(by_geo.get(geo, 0.0) + (amt - disc), 2)

        # 2. Process Returns
        returns_amt = 0.0
        if returns:
            for ret in returns:
                returns_amt += float(ret.get("recovery_value") or ret.get("total_amount") or 0.0)

        # 3. Process Credit Notes
        credits_amt = 0.0
        if invoices:
            for inv in invoices:
                credits_amt += float(inv.get("credit_note_amount") or 0.0)

        net_rev = max(0.0, round(gross_rev - returns_amt - discounts - credits_amt, 2))

        return RevenueBreakdown(
            tenant_id=tenant_id,
            period_key=period_key,
            currency=currency,
            gross_revenue=round(gross_rev, 2),
            net_revenue=net_rev,
            by_customer=by_customer,
            by_sku=by_sku,
            by_channel=by_channel,
            by_geography=by_geo,
        )
