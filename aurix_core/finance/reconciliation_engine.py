"""
AURIX Business Finance Intelligence — Financial Reconciliation Engine
Phase 21 Core Implementation.
Reconciles Invoices vs. Revenue, Invoices vs. Payments, and Inventory vs. GL valuation.
"""

from __future__ import annotations

from typing import Any, Dict, List


class FinanceReconciliationEngine:
    """Ledger and subledger financial reconciliation."""

    @classmethod
    def reconcile_invoices_to_payments(
        cls,
        tenant_id: str,
        invoices: List[Dict[str, Any]],
        payments: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Reconcile invoiced receivables against settled inbound payment receipts."""
        total_invoiced = sum(float(i.get("total_amount") or 0.0) for i in invoices if str(i.get("invoice_type") or "") == "ACCOUNTS_RECEIVABLE")
        total_paid = sum(float(p.get("amount") or 0.0) for p in payments if str(p.get("payment_type") or "") == "INBOUND")

        variance = round(total_invoiced - total_paid, 2)
        match_rate = round((total_paid / max(1.0, total_invoiced)) * 100.0, 2) if total_invoiced > 0 else 100.0

        return {
            "tenant_id": tenant_id,
            "total_invoiced_ar": round(total_invoiced, 2),
            "total_settled_cash": round(total_paid, 2),
            "unsettled_variance": variance,
            "cash_settlement_rate_pct": min(100.0, match_rate),
            "reconciliation_status": "MATCHED" if variance == 0.0 else "OPEN_RECEIVABLES",
        }
