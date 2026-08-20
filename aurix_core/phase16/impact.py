"""Deterministic Phase 16 impact propagation and case preparation.

This module links known Phase 16 records without inventing downstream
relationships. AI may explain the result later, but the impact facts originate
from persisted AURIX data.
"""

from __future__ import annotations

from typing import Any, Dict, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from aurix_core.phase16.models import (
    PurchaseOrderLineModel,
    PurchaseOrderModel,
    SalesOrderLineModel,
)


class ImpactPropagationService:
    """Build conservative cross-domain impact maps from persisted records."""

    @staticmethod
    def supplier_delay(
        db: Session,
        tenant_id: str,
        supplier_id: str,
        delay_days: int,
    ) -> Dict[str, Any]:
        purchase_orders = db.execute(
            select(PurchaseOrderModel).where(
                PurchaseOrderModel.tenant_id == tenant_id,
                PurchaseOrderModel.supplier_id == supplier_id,
                PurchaseOrderModel.status.in_(
                    ["SUBMITTED", "ACKNOWLEDGED", "PARTIALLY_RECEIVED"]
                ),
            )
        ).scalars().all()

        po_ids = [po.id for po in purchase_orders]
        po_lines: Sequence[PurchaseOrderLineModel] = ()
        if po_ids:
            po_lines = db.execute(
                select(PurchaseOrderLineModel).where(
                    PurchaseOrderLineModel.tenant_id == tenant_id,
                    PurchaseOrderLineModel.purchase_order_id.in_(po_ids),
                )
            ).scalars().all()

        sku_ids = sorted({line.sku_id for line in po_lines})
        affected_sales_lines: Sequence[SalesOrderLineModel] = ()
        if sku_ids:
            affected_sales_lines = db.execute(
                select(SalesOrderLineModel).where(
                    SalesOrderLineModel.tenant_id == tenant_id,
                    SalesOrderLineModel.sku_id.in_(sku_ids),
                )
            ).scalars().all()

        impacted_quantity = sum(float(line.quantity) for line in po_lines)
        affected_customer_quantity = sum(
            float(line.quantity - line.allocated_quantity)
            for line in affected_sales_lines
        )

        return {
            "supplier_id": supplier_id,
            "delay_days": delay_days,
            "open_po_count": len(purchase_orders),
            "purchase_order_ids": po_ids,
            "affected_skus": sku_ids,
            "inbound_quantity_at_risk": impacted_quantity,
            "affected_sales_line_count": len(affected_sales_lines),
            "unallocated_customer_quantity": max(
                affected_customer_quantity, 0.0
            ),
            "limitations": [
                "Impact is based only on persisted Phase 16 PO and sales-order relationships.",
                "No unverified revenue or production impact is inferred.",
            ],
        }
