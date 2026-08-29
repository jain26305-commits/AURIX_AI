"""
AURIX Enterprise Sales & Commercial Intelligence — Order & Fulfillment Engine
Phase 22 Core Implementation.
Calculates Commercial OTIF (customer-perspective), fill rates, backlog aging, and cancellations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
from aurix_core.commercial.contracts import CommercialOTIFReport


class OrderPerformanceEngine:
    """Evaluates customer-facing order delivery reliability and fill performance."""

    @classmethod
    def evaluate_order_performance(
        cls,
        tenant_id: str,
        orders: List[Dict[str, Any]],
        period_key: str = "CURRENT",
    ) -> CommercialOTIFReport:
        """
        Commercial OTIF = (On-Time Orders ∩ In-Full Orders) / Total Orders * 100
        """
        total_orders = len(orders)
        if total_orders == 0:
            return CommercialOTIFReport(
                tenant_id=tenant_id,
                period_key=period_key,
                total_orders=0,
                on_time_orders=0,
                in_full_orders=0,
                otif_orders=0,
                otif_rate_pct=100.0,
                fill_rate_pct=100.0,
                average_lead_time_days=0.0,
                backlog_order_count=0,
                cancellation_rate_pct=0.0,
            )

        on_time = 0
        in_full = 0
        otif = 0
        backlog = 0
        cancelled = 0
        total_lead_time_days = 0.0
        lead_time_count = 0

        for o in orders:
            status = str(o.get("order_status") or "").upper()
            if status == "CANCELLED":
                cancelled += 1
                continue

            if status in ("OPEN", "PENDING", "PROCESSING", "BACKLOG"):
                backlog += 1

            prom_date = o.get("promised_delivery_date")
            deliv_date = o.get("delivered_date")
            order_date = o.get("order_date")

            is_on_time = True
            if isinstance(prom_date, datetime) and isinstance(deliv_date, datetime):
                is_on_time = deliv_date <= prom_date
                lead_time = max(0, (deliv_date - order_date).days) if isinstance(order_date, datetime) else 0
                total_lead_time_days += lead_time
                lead_time_count += 1
            elif status == "DELIVERED":
                is_on_time = True

            is_in_full = status not in ("PARTIAL", "SHORT_SHIPPED")

            if is_on_time:
                on_time += 1
            if is_in_full:
                in_full += 1
            if is_on_time and is_in_full and status in ("DELIVERED", "COMPLETED", "OPEN"):
                otif += 1

        valid_orders = max(1, total_orders - cancelled)
        otif_rate = round((otif / valid_orders) * 100.0, 1)
        fill_rate = round((in_full / valid_orders) * 100.0, 1)
        cancel_rate = round((cancelled / total_orders) * 100.0, 1)
        avg_lead_time = round(total_lead_time_days / max(1, lead_time_count), 1)

        return CommercialOTIFReport(
            tenant_id=tenant_id,
            period_key=period_key,
            total_orders=total_orders,
            on_time_orders=on_time,
            in_full_orders=in_full,
            otif_orders=otif,
            otif_rate_pct=otif_rate,
            fill_rate_pct=fill_rate,
            average_lead_time_days=avg_lead_time,
            backlog_order_count=backlog,
            cancellation_rate_pct=cancel_rate,
        )
