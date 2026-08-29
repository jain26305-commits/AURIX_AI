"""
AURIX Business Finance Intelligence — Accounts Receivable & Collections Engine
Phase 21 Core Implementation.
Calculates AR aging buckets, Days Sales Outstanding (DSO), and collections priorities.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from aurix_core.finance.contracts import ARAgingBucket, ARAgingReport


class AREngine:
    """Evaluates accounts receivable aging and collection prioritization."""

    @classmethod
    def calculate_ar_aging(
        cls,
        tenant_id: str,
        invoices: List[Dict[str, Any]],
        annual_revenue: float = 1200000.0,
        days_in_period: int = 365,
        currency: str = "USD",
    ) -> ARAgingReport:
        """
        DSO = (Accounts Receivable / Annual Revenue) * Days
        """
        now = datetime.now(timezone.utc)
        buckets = {
            "CURRENT": {"label": "Current", "amt": 0.0, "count": 0},
            "1_30": {"label": "1–30 Days", "amt": 0.0, "count": 0},
            "31_60": {"label": "31–60 Days", "amt": 0.0, "count": 0},
            "61_90": {"label": "61–90 Days", "amt": 0.0, "count": 0},
            "90_PLUS": {"label": "90+ Days", "amt": 0.0, "count": 0},
        }

        total_ar = 0.0
        total_overdue = 0.0
        customer_debt: Dict[str, Dict[str, Any]] = {}

        for inv in invoices:
            if str(inv.get("invoice_type") or "ACCOUNTS_RECEIVABLE") != "ACCOUNTS_RECEIVABLE":
                continue
            if str(inv.get("status") or "").upper() == "PAID":
                continue

            amt = float(inv.get("total_amount") or 0.0)
            total_ar += amt

            due_date_raw = inv.get("due_date")
            days_overdue = 0
            if isinstance(due_date_raw, datetime):
                due_tz = due_date_raw if due_date_raw.tzinfo else due_date_raw.replace(tzinfo=timezone.utc)
                diff = (now - due_tz).days
                days_overdue = max(0, diff)

            if days_overdue == 0:
                buckets["CURRENT"]["amt"] += amt
                buckets["CURRENT"]["count"] += 1
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

            # Group for collections priority
            c_id = str(inv.get("entity_id") or "UNKNOWN")
            if c_id not in customer_debt:
                customer_debt[c_id] = {"overdue_amt": 0.0, "max_days": 0}
            if days_overdue > 0:
                customer_debt[c_id]["overdue_amt"] += amt
                customer_debt[c_id]["max_days"] = max(customer_debt[c_id]["max_days"], days_overdue)

        # DSO Calculation
        dso = round((total_ar / max(1.0, annual_revenue)) * days_in_period, 1)

        bucket_list = [
            ARAgingBucket(
                bucket=k,
                label=v["label"],
                total_amount=round(v["amt"], 2),
                invoice_count=v["count"],
                percent_of_total=round((v["amt"] / max(1.0, total_ar)) * 100.0, 1),
            )
            for k, v in buckets.items()
        ]

        top_debtors = [
            {
                "customer_id": c_id,
                "overdue_amount": round(data["overdue_amt"], 2),
                "oldest_invoice_days": data["max_days"],
                "risk_tier": "HIGH" if data["max_days"] > 60 else "MEDIUM",
            }
            for c_id, data in sorted(customer_debt.items(), key=lambda x: x[1]["overdue_amt"], reverse=True)
            if data["overdue_amt"] > 0
        ]

        return ARAgingReport(
            tenant_id=tenant_id,
            currency=currency,
            total_receivables=round(total_ar, 2),
            total_overdue=round(total_overdue, 2),
            dso_days=dso,
            buckets=bucket_list,
            top_overdue_debtors=top_debtors[:10],
        )
