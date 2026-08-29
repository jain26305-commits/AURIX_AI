"""
AURIX Business Finance Intelligence — Accounts Payable Intelligence Engine
Phase 21 Core Implementation.
Calculates AP aging, Days Payable Outstanding (DPO), and supplier cash commitments.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
from aurix_core.finance.contracts import APAgingReport


class APEngine:
    """Evaluates accounts payable obligations and payment timing."""

    @classmethod
    def calculate_ap_aging(
        cls,
        tenant_id: str,
        invoices: List[Dict[str, Any]],
        annual_cogs: float = 720000.0,
        days_in_period: int = 365,
        currency: str = "USD",
    ) -> APAgingReport:
        """
        DPO = (Accounts Payable / Annual COGS) * Days
        """
        now = datetime.now(timezone.utc)
        buckets = {
            "CURRENT": {"label": "Current", "amt": 0.0, "count": 0},
            "1_30": {"label": "1–30 Days", "amt": 0.0, "count": 0},
            "31_60": {"label": "31–60 Days", "amt": 0.0, "count": 0},
            "61_90": {"label": "61–90 Days", "amt": 0.0, "count": 0},
            "90_PLUS": {"label": "90+ Days", "amt": 0.0, "count": 0},
        }

        total_ap = 0.0
        total_overdue = 0.0
        upcoming: List[Dict[str, Any]] = []

        for inv in invoices:
            if str(inv.get("invoice_type") or "") not in ("ACCOUNTS_PAYABLE", "PURCHASE_INVOICE", "SUPPLIER_INVOICE"):
                continue
            if str(inv.get("status") or "").upper() == "PAID":
                continue

            amt = float(inv.get("total_amount") or 0.0)
            total_ap += amt

            due_date_raw = inv.get("due_date")
            days_overdue = 0
            if isinstance(due_date_raw, datetime):
                due_tz = due_date_raw if due_date_raw.tzinfo else due_date_raw.replace(tzinfo=timezone.utc)
                diff = (now - due_tz).days
                days_overdue = max(0, diff)

            if days_overdue == 0:
                buckets["CURRENT"]["amt"] += amt
                buckets["CURRENT"]["count"] += 1
                upcoming.append({
                    "supplier_id": str(inv.get("entity_id") or "SUPP-UNKNOWN"),
                    "amount": amt,
                    "due_date": due_date_raw.isoformat() if isinstance(due_date_raw, datetime) else str(due_date_raw),
                    "discount_available": False,
                })
            else:
                total_overdue += amt
                if days_overdue <= 30:
                    buckets["1_30"]["amt"] += amt
                    buckets["1_30"]["count"] += 1
                elif days_overdue <= 60:
                    buckets["31_60"]["amt"] += amt
                    buckets["31_60"]["count"] += 1
                elif days_overdue <= 90:
                    buckets["61_90"]["amt"] += amt
                    buckets["61_90"]["count"] += 1
                else:
                    buckets["90_PLUS"]["amt"] += amt
                    buckets["90_PLUS"]["count"] += 1

        dpo = round((total_ap / max(1.0, annual_cogs)) * days_in_period, 1)

        bucket_list = [
            {
                "bucket": k,
                "label": v["label"],
                "total_amount": round(v["amt"], 2),
                "invoices_count": v["count"],
            }
            for k, v in buckets.items()
        ]

        return APAgingReport(
            tenant_id=tenant_id,
            currency=currency,
            total_payables=round(total_ap, 2),
            total_overdue=round(total_overdue, 2),
            dpo_days=dpo,
            buckets=bucket_list,
            upcoming_obligations=upcoming[:10],
        )
