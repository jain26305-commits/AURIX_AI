"""
AURIX Continuous Assurance — Price Variance & Contract Compliance Engine
Phase 20 Core Implementation.
Audits Purchase Price Variance (PPV) against contracted price books.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.assurance.contracts import (
    AssuranceDomain,
    AssuranceFinding,
    LeakageSeverity,
)


class PriceVarianceEngine:
    """Computes Purchase Price Variance (PPV) and audits contract compliance."""

    @classmethod
    def evaluate_po_pricing(
        cls,
        tenant_id: str,
        purchase_orders: List[Dict[str, Any]],
        price_book: Dict[str, float],
    ) -> List[AssuranceFinding]:
        """Compare actual PO line unit prices against contracted master price books."""
        findings: List[AssuranceFinding] = []

        for po in purchase_orders:
            po_id = str(po.get("id") or po.get("po_number") or "")
            sku_id = str(po.get("sku_id") or po.get("sku") or "")
            supplier_id = str(po.get("supplier_id") or "")
            actual_price = float(po.get("unit_cost") or po.get("unit_price") or 0.0)
            qty = float(po.get("quantity") or 1.0)

            contracted_price = price_book.get(sku_id)
            if contracted_price is not None and actual_price > contracted_price:
                unit_var = actual_price - contracted_price
                ppv_total = round(unit_var * qty, 2)
                var_pct = round((unit_var / contracted_price) * 100.0, 2)

                severity = LeakageSeverity.CRITICAL if ppv_total > 5000 else (LeakageSeverity.HIGH if ppv_total > 1000 else LeakageSeverity.MEDIUM)
                finding = AssuranceFinding(
                    tenant_id=tenant_id,
                    domain=AssuranceDomain.PRICE_VARIANCE,
                    severity=severity,
                    title=f"Unfavorable PPV on PO {po_id}: SKU {sku_id}",
                    description=f"Purchased at {actual_price}/unit vs contracted rate of {contracted_price}/unit (+{var_pct}%).",
                    financial_exposure=ppv_total,
                    entity_type="purchase_order",
                    entity_id=po_id,
                    evidence_data={"sku_id": sku_id, "supplier_id": supplier_id, "actual_price": actual_price, "contracted_price": contracted_price, "qty": qty, "ppv": ppv_total},
                    recommended_action="Renegotiate or demand vendor rebate matching contracted terms.",
                )
                findings.append(finding)

        return findings
