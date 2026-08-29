"""
AURIX Continuous Assurance — Unbilled Shipments & Revenue Leakage Engine
Phase 20 Core Implementation.
Tracks fulfilled shipments lacking corresponding billing records past SLA thresholds.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Set
from aurix_core.assurance.contracts import (
    AssuranceDomain,
    AssuranceFinding,
    LeakageSeverity,
)


class UnbilledShipmentsEngine:
    """Detects fulfilled orders or delivered shipments that have not been invoiced."""

    DEFAULT_UNBILLED_SLA_DAYS = 5

    @classmethod
    def evaluate_unbilled_shipments(
        cls,
        tenant_id: str,
        shipments: List[Dict[str, Any]],
        orders: List[Dict[str, Any]],
        invoices: List[Dict[str, Any]],
        unbilled_sla_days: int = DEFAULT_UNBILLED_SLA_DAYS,
    ) -> List[AssuranceFinding]:
        """Scan shipments and identify those delivered without customer invoices past SLA."""
        findings: List[AssuranceFinding] = []
        now = datetime.now(timezone.utc)

        # Map invoiced order IDs / entity IDs
        invoiced_order_ids: Set[str] = set()
        for inv in invoices:
            order_ref = str(inv.get("order_id") or inv.get("reference_document") or inv.get("entity_id") or "")
            if order_ref:
                invoiced_order_ids.add(order_ref)

        order_map: Dict[str, Dict[str, Any]] = {
            str(o.get("id") or o.get("order_number") or ""): o for o in orders
        }

        for shp in shipments:
            shp_id = str(shp.get("id") or shp.get("shipment_number") or "")
            order_id = str(shp.get("order_id") or shp.get("reference_document") or "")
            status = str(shp.get("status") or "").upper()

            if status not in ("DELIVERED", "COMPLETED", "SHIPPED"):
                continue

            # Check if invoiced
            if order_id and (order_id in invoiced_order_ids or shp_id in invoiced_order_ids):
                continue

            order_data = order_map.get(order_id, {})
            exposure = float(order_data.get("total_amount") or shp.get("declared_value") or 0.0)

            # Age calculation
            shipped_date = shp.get("shipped_date") or shp.get("created_at")
            age_days = 0
            if isinstance(shipped_date, datetime):
                shipped_tz = shipped_date if shipped_date.tzinfo else shipped_date.replace(tzinfo=timezone.utc)
                age_days = (now - shipped_tz).days

            if age_days >= unbilled_sla_days or exposure > 0:
                severity = LeakageSeverity.CRITICAL if exposure > 10000 else (LeakageSeverity.HIGH if exposure > 2000 else LeakageSeverity.MEDIUM)
                finding = AssuranceFinding(
                    tenant_id=tenant_id,
                    domain=AssuranceDomain.UNBILLED_SHIPMENT,
                    severity=severity,
                    title=f"Unbilled Shipment {shp_id} for Order {order_id}",
                    description=f"Shipment {shp_id} was delivered {age_days} days ago but has no customer invoice generated.",
                    financial_exposure=exposure,
                    entity_type="shipment",
                    entity_id=shp_id,
                    evidence_data={"order_id": order_id, "exposure": exposure, "age_days": age_days, "carrier": shp.get("carrier")},
                    recommended_action="Generate and dispatch accounts receivable customer invoice immediately.",
                )
                findings.append(finding)

        return findings
