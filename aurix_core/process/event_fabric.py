"""
AURIX Process Intelligence — Process Event Fabric Engine
Phase 25 Core Implementation.
Extracts and normalizes state transitions from multi-domain canonical records into standardized event envelopes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
from aurix_core.process.contracts import ProcessEvent, ProcessEventType, ProcessType


class ProcessEventFabric:
    """Extracts and normalizes multi-system transactions into standardized process events."""

    @classmethod
    def extract_events(
        cls,
        tenant_id: str,
        orders: List[Dict[str, Any]],
        invoices: List[Dict[str, Any]],
        payments: List[Dict[str, Any]],
        shipments: List[Dict[str, Any]],
        work_orders: List[Dict[str, Any]] | None = None,
        returns: List[Dict[str, Any]] | None = None,
    ) -> List[ProcessEvent]:
        """Extract and normalize all domain entity state transitions into a unified chronological event stream."""
        events: List[ProcessEvent] = []
        now = datetime.now(timezone.utc)

        # 1. Orders (OrderPlaced, Delivered)
        for o in orders:
            o_id = str(o.get("id") or o.get("order_number"))
            c_id = str(o.get("customer_id") or "")
            o_date = o.get("order_date") or now
            if isinstance(o_date, str):
                try:
                    o_date = datetime.fromisoformat(o_date.replace("Z", "+00:00"))
                except Exception:
                    o_date = now
            if not o_date.tzinfo:
                o_date = o_date.replace(tzinfo=timezone.utc)

            events.append(
                ProcessEvent(
                    tenant_id=tenant_id,
                    process_type=ProcessType.ORDER_TO_CASH,
                    event_type=ProcessEventType.ORDER_PLACED.value,
                    event_timestamp=o_date,
                    source_record_id=f"orders:{o_id}",
                    object_bindings={"order_id": o_id, "customer_id": c_id},
                    attributes={"total_amount": o.get("total_amount")},
                )
            )

        # 2. Shipments (GoodsDispatched, Delivered)
        for s in shipments:
            s_id = str(s.get("id") or s.get("shipment_number"))
            shipped_date = s.get("shipped_date") or now
            if isinstance(shipped_date, str):
                try:
                    shipped_date = datetime.fromisoformat(shipped_date.replace("Z", "+00:00"))
                except Exception:
                    shipped_date = now
            if not shipped_date.tzinfo:
                shipped_date = shipped_date.replace(tzinfo=timezone.utc)

            events.append(
                ProcessEvent(
                    tenant_id=tenant_id,
                    process_type=ProcessType.ORDER_TO_CASH,
                    event_type=ProcessEventType.GOODS_DISPATCHED.value,
                    event_timestamp=shipped_date,
                    source_record_id=f"shipments:{s_id}",
                    object_bindings={"shipment_id": s_id},
                    attributes={"carrier": s.get("carrier"), "status": s.get("status")},
                )
            )

        # 3. Invoices (InvoiceIssued)
        for inv in invoices:
            inv_id = str(inv.get("id") or inv.get("invoice_number"))
            inv_date = inv.get("issue_date") or now
            if isinstance(inv_date, str):
                try:
                    inv_date = datetime.fromisoformat(inv_date.replace("Z", "+00:00"))
                except Exception:
                    inv_date = now
            if not inv_date.tzinfo:
                inv_date = inv_date.replace(tzinfo=timezone.utc)

            events.append(
                ProcessEvent(
                    tenant_id=tenant_id,
                    process_type=ProcessType.ORDER_TO_CASH,
                    event_type=ProcessEventType.INVOICE_ISSUED.value,
                    event_timestamp=inv_date,
                    source_record_id=f"invoices:{inv_id}",
                    object_bindings={"invoice_id": inv_id},
                    attributes={"total_amount": inv.get("total_amount")},
                )
            )

        # 4. Payments (PaymentSettled)
        for p in payments:
            p_id = str(p.get("id") or p.get("payment_number"))
            p_date = p.get("payment_date") or now
            if isinstance(p_date, str):
                try:
                    p_date = datetime.fromisoformat(p_date.replace("Z", "+00:00"))
                except Exception:
                    p_date = now
            if not p_date.tzinfo:
                p_date = p_date.replace(tzinfo=timezone.utc)

            events.append(
                ProcessEvent(
                    tenant_id=tenant_id,
                    process_type=ProcessType.ORDER_TO_CASH,
                    event_type=ProcessEventType.PAYMENT_SETTLED.value,
                    event_timestamp=p_date,
                    source_record_id=f"payments:{p_id}",
                    object_bindings={"payment_id": p_id, "invoice_id": str(p.get("invoice_id") or "")},
                    attributes={"amount": p.get("amount")},
                )
            )

        # 5. Work Orders (ProductionOrderReleased, OperationCompleted)
        for wo in (work_orders or []):
            wo_id = str(wo.get("id") or wo.get("work_order_number"))
            start_d = wo.get("start_date") or now
            if isinstance(start_d, str):
                try:
                    start_d = datetime.fromisoformat(start_d.replace("Z", "+00:00"))
                except Exception:
                    start_d = now
            if not start_d.tzinfo:
                start_d = start_d.replace(tzinfo=timezone.utc)

            events.append(
                ProcessEvent(
                    tenant_id=tenant_id,
                    process_type=ProcessType.MANUFACTURING_PRODUCTION,
                    event_type=ProcessEventType.PRODUCTION_ORDER_RELEASED.value,
                    event_timestamp=start_d,
                    source_record_id=f"work_orders:{wo_id}",
                    object_bindings={"work_order_id": wo_id, "sku_id": str(wo.get("sku_id") or "")},
                    attributes={"target_quantity": wo.get("target_quantity")},
                )
            )

        events.sort(key=lambda x: x.event_timestamp)
        return events
