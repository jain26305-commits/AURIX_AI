"""
AURIX Continuous Assurance — Automated 3-Way Match Engine
Phase 20 Core Implementation.
Evaluates PO, Goods Receipt (ASN/GRN), and Invoice alignments.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
from aurix_core.assurance.contracts import (
    AssuranceDomain,
    AssuranceFinding,
    FindingStatus,
    LeakageSeverity,
    MatchStatus,
    ThreeWayMatchResult,
)


class ThreeWayMatchEngine:
    """Automated matching between Purchase Orders, Goods Receipts, and Invoices."""

    DEFAULT_PRICE_TOLERANCE_PCT = 1.0  # 1% price variance allowance
    DEFAULT_QTY_TOLERANCE_PCT = 0.0    # Exact quantity match required

    @classmethod
    def evaluate(
        cls,
        tenant_id: str,
        po: Dict[str, Any],
        receipt: Optional[Dict[str, Any]],
        invoice: Dict[str, Any],
        price_tolerance_pct: float = DEFAULT_PRICE_TOLERANCE_PCT,
        qty_tolerance_pct: float = DEFAULT_QTY_TOLERANCE_PCT,
    ) -> Tuple[ThreeWayMatchResult, Optional[AssuranceFinding]]:
        """Perform 3-way match and return match result and optional finding."""
        po_id = str(po.get("id") or po.get("po_number") or "")
        inv_id = str(invoice.get("id") or invoice.get("invoice_number") or "")
        rcpt_id = str(receipt.get("id") or receipt.get("receipt_id") or "") if receipt else None

        po_unit_price = float(po.get("unit_cost") or po.get("unit_price") or 0.0)
        po_qty = float(po.get("quantity") or 0.0)
        po_total = float(po.get("total_amount") or (po_unit_price * po_qty))

        inv_unit_price = float(invoice.get("unit_price") or (float(invoice.get("total_amount", 0.0)) / max(1.0, float(invoice.get("quantity", 1.0)))))
        inv_qty = float(invoice.get("quantity") or 1.0)
        inv_total = float(invoice.get("total_amount") or (inv_unit_price * inv_qty))

        rcpt_qty = float(receipt.get("received_quantity") or receipt.get("quantity") or 0.0) if receipt else 0.0

        # Variance calculations
        price_diff = inv_unit_price - po_unit_price
        price_var_pct = (abs(price_diff) / po_unit_price * 100.0) if po_unit_price > 0 else 0.0

        qty_diff = inv_qty - rcpt_qty
        qty_var_pct = (abs(qty_diff) / rcpt_qty * 100.0) if rcpt_qty > 0 else (100.0 if inv_qty > 0 else 0.0)

        match_status = MatchStatus.PERFECT_MATCH
        is_approved = True
        leakage = 0.0
        finding: Optional[AssuranceFinding] = None

        if receipt is None or rcpt_qty == 0:
            match_status = MatchStatus.UNMATCHED_RECEIPT
            is_approved = False
            leakage = inv_total
            finding = AssuranceFinding(
                tenant_id=tenant_id,
                domain=AssuranceDomain.THREE_WAY_MATCH,
                severity=LeakageSeverity.HIGH,
                title=f"Invoice {inv_id} lacks Goods Receipt confirmation",
                description=f"Billed {inv_total} {invoice.get('currency', 'USD')} on PO {po_id} with no verified receipt.",
                financial_exposure=leakage,
                entity_type="invoice",
                entity_id=inv_id,
                evidence_data={"po_id": po_id, "invoice_total": inv_total, "received_qty": 0},
                recommended_action="Hold invoice payment pending warehouse receipt confirmation.",
            )
        elif price_diff > 0 and price_var_pct > price_tolerance_pct:
            match_status = MatchStatus.PRICE_MISMATCH
            is_approved = False
            leakage = round(price_diff * inv_qty, 2)
            finding = AssuranceFinding(
                tenant_id=tenant_id,
                domain=AssuranceDomain.THREE_WAY_MATCH,
                severity=LeakageSeverity.HIGH if leakage > 1000 else LeakageSeverity.MEDIUM,
                title=f"Price discrepancy on Invoice {inv_id}",
                description=f"Invoiced at {inv_unit_price}/unit vs PO price {po_unit_price}/unit ({price_var_pct:.2f}% variance).",
                financial_exposure=leakage,
                entity_type="invoice",
                entity_id=inv_id,
                evidence_data={"po_unit_price": po_unit_price, "invoice_unit_price": inv_unit_price, "variance_pct": price_var_pct},
                recommended_action="Request credit memo from supplier for overbilled unit cost.",
            )
        elif qty_diff > 0 and qty_var_pct > qty_tolerance_pct:
            match_status = MatchStatus.QUANTITY_MISMATCH
            is_approved = False
            leakage = round(qty_diff * inv_unit_price, 2)
            finding = AssuranceFinding(
                tenant_id=tenant_id,
                domain=AssuranceDomain.THREE_WAY_MATCH,
                severity=LeakageSeverity.CRITICAL if leakage > 5000 else LeakageSeverity.HIGH,
                title=f"Quantity overbill on Invoice {inv_id}",
                description=f"Invoiced {inv_qty} units but only received {rcpt_qty} units.",
                financial_exposure=leakage,
                entity_type="invoice",
                entity_id=inv_id,
                evidence_data={"invoiced_qty": inv_qty, "received_qty": rcpt_qty, "shortfall": qty_diff},
                recommended_action="Short-pay invoice to match physically received quantity.",
            )
        elif price_var_pct > 0 or qty_var_pct > 0:
            match_status = MatchStatus.TOLERANCE_MATCH
            is_approved = True

        result = ThreeWayMatchResult(
            tenant_id=tenant_id,
            po_id=po_id,
            receipt_id=rcpt_id,
            invoice_id=inv_id,
            match_status=match_status,
            po_amount=po_total,
            receipt_qty=rcpt_qty,
            invoice_amount=inv_total,
            invoice_qty=inv_qty,
            price_variance=round(price_diff, 2),
            qty_variance=round(qty_diff, 2),
            is_approved=is_approved,
            leakage_amount=leakage,
            details={"price_var_pct": round(price_var_pct, 2), "qty_var_pct": round(qty_var_pct, 2)},
        )

        return result, finding
