"""Deterministic Phase 16 planning and execution services.

The services intentionally reuse Phase 1-15 canonical data and calculations.
No LLM is required for these operations.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from aurix_core.database.models.supply_chain import InventoryPosition
from aurix_core.phase16.contracts import (
    ATPRequest,
    BOMCreateRequest,
    CapacityCheckRequest,
    CTPRequest,
    FinancialDocumentRequest,
    ScenarioComparisonRequest,
    SupplierAcknowledgementRequest,
    AdvanceShipmentNoticeRequest,
    GoodsReceiptCreateRequest,
    MRPRequest,
    Phase16Result,
    PurchaseOrderCreateRequest,
    PurchaseOrderRevisionRequest,
    ReturnCreateRequest,
    ReturnDispositionRequest,
    SalesOrderCreateRequest,
    ScenarioRequest,
)
from aurix_core.phase16.idempotency import begin as begin_idempotency, complete as complete_idempotency
from aurix_core.phase16.models import (
    BOMHeaderModel,
    BOMLineModel,
    CapacityCheckModel,
    FulfillmentAllocationModel,
    GoodsReceiptLineModel,
    GoodsReceiptModel,
    MRPRunModel,
    Phase16ScenarioModel,
    PurchaseOrderLineModel,
    PurchaseOrderModel,
    ReturnRequestModel,
    SalesOrderLineModel,
    SalesOrderModel,
    SupplierFinancialDocumentLineModel,
    SupplierFinancialDocumentModel,
    SupplierCommitmentModel,
    AdvanceShipmentNoticeLineModel,
    AdvanceShipmentNoticeModel,
    PurchaseOrderRevisionModel,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16].upper()}"


class ProcurementService:
    """Supplier/PO lifecycle with deterministic financial matching."""

    @staticmethod
    def create_purchase_order(
        db: Session, tenant_id: str, request: PurchaseOrderCreateRequest
    ) -> Phase16Result:
        idem_record, idem_result = begin_idempotency(
            db, tenant_id, request, "CREATE_PURCHASE_ORDER"
        )
        if idem_result is not None:
            return idem_result

        total = sum(
            (line.unit_price or 0.0) * line.quantity for line in request.lines
        )
        currency = next(
            (line.currency for line in request.lines if line.currency),
            None,
        )
        po_id = _id("PO")
        po = PurchaseOrderModel(
            id=po_id,
            tenant_id=tenant_id,
            supplier_id=request.supplier_id,
            status="DRAFT",
            required_date=request.required_date,
            source_request_id=request.source_request_id,
            total_amount=total if any(line.unit_price is not None for line in request.lines) else None,
            currency=currency,
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(po)
        for line in request.lines:
            db.add(
                PurchaseOrderLineModel(
                    id=_id("POL"),
                    tenant_id=tenant_id,
                    purchase_order_id=po_id,
                    sku_id=line.sku_id,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    currency=line.currency,
                    created_at=_now(),
                )
            )
        result = Phase16Result(
            success=True,
            status="DRAFT",
            data={"purchase_order_id": po_id, "total_amount": po.total_amount, "currency": currency},
            provenance={"operation": "CREATE_PO", "tenant_id": tenant_id},
        )
        complete_idempotency(db, idem_record, result)
        db.commit()
        return result

    @staticmethod
    def transition_purchase_order(
        db: Session, tenant_id: str, purchase_order_id: str, target_status: str,
        reason: str | None = None, committed_date: datetime | None = None,
    ) -> Phase16Result:
        allowed: dict[str, set[str]] = {
            "DRAFT": {"PENDING_APPROVAL", "CANCELLED"},
            "PENDING_APPROVAL": {"APPROVED", "REJECTED", "CANCELLED"},
            "APPROVED": {"SUBMITTED", "CANCELLED"},
            "SUBMITTED": {"ACKNOWLEDGED", "CANCELLED"},
            "ACKNOWLEDGED": {"PARTIALLY_RECEIVED", "FULLY_RECEIVED", "CANCELLED"},
            "PARTIALLY_RECEIVED": {"FULLY_RECEIVED", "CANCELLED"},
            "FULLY_RECEIVED": {"CLOSED"},
            "REJECTED": set(),
            "CANCELLED": set(),
            "CLOSED": set(),
        }
        po = db.execute(
            select(PurchaseOrderModel).where(
                PurchaseOrderModel.id == purchase_order_id,
                PurchaseOrderModel.tenant_id == tenant_id,
            )
        ).scalar_one_or_none()
        if po is None:
            return Phase16Result(success=False, status="NOT_FOUND", data={"purchase_order_id": purchase_order_id})

        if target_status not in allowed.get(str(po.status), set()):
            return Phase16Result(
                success=False,
                status="INVALID_TRANSITION",
                data={"from": po.status, "to": target_status},
            )
        po.status = target_status
        po.updated_at = _now()
        if target_status == "CANCELLED":
            po.cancelled_reason = reason
        if committed_date is not None:
            po.committed_date = committed_date
        db.commit()
        return Phase16Result(success=True, status=target_status, data={"purchase_order_id": purchase_order_id})

    @staticmethod
    def revise_purchase_order(
        db: Session, tenant_id: str, request: PurchaseOrderRevisionRequest
    ) -> Phase16Result:
        idem_record, idem_result = begin_idempotency(
            db, tenant_id, request, "REVISE_PURCHASE_ORDER"
        )
        if idem_result is not None:
            return idem_result

        po = db.execute(
            select(PurchaseOrderModel).where(
                PurchaseOrderModel.id == request.purchase_order_id,
                PurchaseOrderModel.tenant_id == tenant_id,
            ).with_for_update()
        ).scalar_one_or_none()
        if po is None:
            return Phase16Result(success=False, status="NOT_FOUND", data={"purchase_order_id": request.purchase_order_id})
        if po.status in {"CLOSED", "CANCELLED", "REJECTED", "FULLY_RECEIVED"}:
            return Phase16Result(success=False, status="INVALID_STATE", data={"status": po.status})

        current_lines = db.execute(
            select(PurchaseOrderLineModel).where(
                PurchaseOrderLineModel.purchase_order_id == po.id,
                PurchaseOrderLineModel.tenant_id == tenant_id,
            )
        ).scalars().all()
        snapshot = {
            "purchase_order": {
                "supplier_id": po.supplier_id,
                "required_date": po.required_date.isoformat() if po.required_date else None,
                "status": po.status,
                "revision": po.revision,
            },
            "lines": [
                {
                    "sku_id": line.sku_id, "quantity": line.quantity,
                    "unit_price": line.unit_price, "currency": line.currency,
                    "received_quantity": line.received_quantity,
                }
                for line in current_lines
            ],
        }
        revision_number = po.revision + 1
        db.add(PurchaseOrderRevisionModel(
            id=_id("POREV"), tenant_id=tenant_id, purchase_order_id=po.id,
            revision=revision_number, reason=request.reason,
            snapshot_json=snapshot, created_at=_now(),
        ))
        for line in current_lines:
            if line.received_quantity > 0:
                matching = next((item for item in request.lines if item.sku_id == line.sku_id), None)
                if matching is None or matching.quantity < line.received_quantity - 1e-9:
                    return Phase16Result(
                        success=False, status="INVALID_REVISION",
                        data={"line_id": line.id, "reason": "Revision cannot reduce quantity below already received quantity."},
                    )
            db.delete(line)
        total = sum((line.unit_price or 0.0) * line.quantity for line in request.lines)
        po.revision = revision_number
        po.total_amount = total if any(line.unit_price is not None for line in request.lines) else None
        po.currency = next((line.currency for line in request.lines if line.currency), po.currency)
        po.updated_at = _now()
        for item in request.lines:
            db.add(PurchaseOrderLineModel(
                id=_id("POL"), tenant_id=tenant_id, purchase_order_id=po.id,
                sku_id=item.sku_id, quantity=item.quantity, unit_price=item.unit_price,
                currency=item.currency, created_at=_now(),
            ))
        result = Phase16Result(
            success=True, status="REVISED",
            data={"purchase_order_id": po.id, "revision": revision_number},
        )
        complete_idempotency(db, idem_record, result)
        db.commit()
        return result

    @staticmethod
    def acknowledge_purchase_order(
        db: Session, tenant_id: str, request: SupplierAcknowledgementRequest
    ) -> Phase16Result:
        idem_record, idem_result = begin_idempotency(
            db, tenant_id, request, "SUPPLIER_ACKNOWLEDGEMENT"
        )
        if idem_result is not None:
            return idem_result

        po = db.execute(
            select(PurchaseOrderModel).where(
                PurchaseOrderModel.id == request.purchase_order_id,
                PurchaseOrderModel.tenant_id == tenant_id,
            ).with_for_update()
        ).scalar_one_or_none()
        if po is None:
            return Phase16Result(success=False, status="NOT_FOUND", data={"purchase_order_id": request.purchase_order_id})
        if po.status not in {"SUBMITTED", "ACKNOWLEDGED"}:
            return Phase16Result(success=False, status="INVALID_STATE", data={"status": po.status})

        commitment = SupplierCommitmentModel(
            id=_id("COMM"),
            tenant_id=tenant_id,
            purchase_order_id=po.id,
            status=request.acknowledgement_status,
            committed_date=request.committed_date,
            committed_quantity=request.committed_quantity,
            alternative_date=request.alternative_date,
            reason=request.reason,
            supplier_reference=request.supplier_reference,
            created_at=_now(),
        )
        db.add(commitment)
        po.supplier_reference = request.supplier_reference
        if request.acknowledgement_status in {"ACKNOWLEDGED", "PARTIAL"}:
            po.status = "ACKNOWLEDGED"
            po.acknowledged_at = _now()
            po.committed_date = request.committed_date or request.alternative_date
        else:
            po.status = "REJECTED"
        po.updated_at = _now()
        result = Phase16Result(
            success=True,
            status=po.status,
            data={
                "purchase_order_id": po.id,
                "commitment_id": commitment.id,
                "acknowledgement_status": request.acknowledgement_status,
            },
        )
        complete_idempotency(db, idem_record, result)
        db.commit()
        return result

    @staticmethod
    def create_asn(
        db: Session, tenant_id: str, request: AdvanceShipmentNoticeRequest
    ) -> Phase16Result:
        idem_record, idem_result = begin_idempotency(
            db, tenant_id, request, "CREATE_ASN"
        )
        if idem_result is not None:
            return idem_result
        po = db.execute(
            select(PurchaseOrderModel).where(
                PurchaseOrderModel.id == request.purchase_order_id,
                PurchaseOrderModel.tenant_id == tenant_id,
            )
        ).scalar_one_or_none()
        if po is None:
            return Phase16Result(success=False, status="NOT_FOUND", data={"purchase_order_id": request.purchase_order_id})
        line_ids = {
            row[0] for row in db.execute(
                select(PurchaseOrderLineModel.id).where(
                    PurchaseOrderLineModel.purchase_order_id == po.id,
                    PurchaseOrderLineModel.tenant_id == tenant_id,
                )
            ).all()
        }
        if any(item.purchase_order_line_id not in line_ids for item in request.lines):
            return Phase16Result(success=False, status="INVALID_LINE", data={"purchase_order_id": po.id})

        asn = AdvanceShipmentNoticeModel(
            id=_id("ASN"),
            tenant_id=tenant_id,
            purchase_order_id=po.id,
            status="RECEIVED",
            expected_arrival_date=request.expected_arrival_date,
            carrier=request.carrier,
            tracking_number=request.tracking_number,
            created_at=_now(),
        )
        db.add(asn)
        for item in request.lines:
            db.add(
                AdvanceShipmentNoticeLineModel(
                    id=_id("ASNL"),
                    tenant_id=tenant_id,
                    asn_id=asn.id,
                    purchase_order_line_id=item.purchase_order_line_id,
                    shipped_quantity=item.shipped_quantity,
                )
            )
        result = Phase16Result(
            success=True,
            status="ASN_RECEIVED",
            data={
                "asn_id": asn.id,
                "purchase_order_id": po.id,
                "expected_arrival_date": request.expected_arrival_date.isoformat()
                if request.expected_arrival_date else None,
            },
        )
        complete_idempotency(db, idem_record, result)
        db.commit()
        return result

    @staticmethod
    def receive_goods(
        db: Session, tenant_id: str, request: GoodsReceiptCreateRequest
    ) -> Phase16Result:
        idem_record, idem_result = begin_idempotency(
            db, tenant_id, request, "RECEIVE_GOODS"
        )
        if idem_result is not None:
            return idem_result
        po = db.execute(
            select(PurchaseOrderModel).where(
                PurchaseOrderModel.id == request.purchase_order_id,
                PurchaseOrderModel.tenant_id == tenant_id,
            )
        ).scalar_one_or_none()
        if po is None:
            return Phase16Result(success=False, status="NOT_FOUND", data={"purchase_order_id": request.purchase_order_id})

        lines = db.execute(
            select(PurchaseOrderLineModel).where(
                PurchaseOrderLineModel.purchase_order_id == po.id,
                PurchaseOrderLineModel.tenant_id == tenant_id,
            )
        ).scalars().all()
        by_id = {line.id: line for line in lines}

        receipt = GoodsReceiptModel(
            id=_id("GRN"),
            tenant_id=tenant_id,
            purchase_order_id=po.id,
            status="RECEIVED",
            created_at=_now(),
        )
        db.add(receipt)

        for item in request.lines:
            line = by_id.get(item.purchase_order_line_id)
            if line is None:
                db.rollback()
                return Phase16Result(success=False, status="INVALID_LINE", data={"line_id": item.purchase_order_line_id})
            if abs((item.accepted_quantity + item.rejected_quantity) - item.received_quantity) > 1e-9:
                db.rollback()
                return Phase16Result(success=False, status="INVALID_RECEIPT_SPLIT", data={"line_id": line.id})
            new_received = line.received_quantity + item.received_quantity
            if new_received > line.quantity:
                db.rollback()
                return Phase16Result(
                    success=False,
                    status="OVER_RECEIPT",
                    data={
                        "line_id": line.id,
                        "ordered": line.quantity,
                        "attempted_received": new_received,
                    },
                )
            line.received_quantity = new_received
            line.accepted_quantity += item.accepted_quantity
            line.rejected_quantity += item.rejected_quantity
            db.add(
                GoodsReceiptLineModel(
                    id=_id("GRNL"),
                    tenant_id=tenant_id,
                    goods_receipt_id=receipt.id,
                    purchase_order_line_id=line.id,
                    received_quantity=item.received_quantity,
                    accepted_quantity=item.accepted_quantity,
                    rejected_quantity=item.rejected_quantity,
                )
            )

        all_complete = all(line.received_quantity >= line.quantity for line in lines)
        po.status = "FULLY_RECEIVED" if all_complete else "PARTIALLY_RECEIVED"
        po.updated_at = _now()
        result = Phase16Result(
            success=True, status=po.status,
            data={"goods_receipt_id": receipt.id, "purchase_order_id": po.id},
        )
        complete_idempotency(db, idem_record, result)
        db.commit()
        return result

    @staticmethod
    def add_financial_document(
        db: Session, tenant_id: str, request: FinancialDocumentRequest
    ) -> Phase16Result:
        idem_record, idem_result = begin_idempotency(
            db, tenant_id, request, "ADD_FINANCIAL_DOCUMENT"
        )
        if idem_result is not None:
            return idem_result

        po = db.execute(
            select(PurchaseOrderModel).where(
                PurchaseOrderModel.id == request.purchase_order_id,
                PurchaseOrderModel.tenant_id == tenant_id,
            )
        ).scalar_one_or_none()
        if po is None:
            return Phase16Result(success=False, status="NOT_FOUND", data={"purchase_order_id": request.purchase_order_id})

        existing = db.execute(
            select(SupplierFinancialDocumentModel).where(
                SupplierFinancialDocumentModel.tenant_id == tenant_id,
                SupplierFinancialDocumentModel.document_number == request.document_number,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return Phase16Result(success=False, status="DUPLICATE_DOCUMENT", data={"document_id": existing.id})

        status = "UNMATCHED"
        warnings: List[str] = []
        mismatch: List[str] = []

        if request.document_type == "INVOICE":
            if not request.lines:
                warnings.append("INVOICE_LINES_REQUIRED_FOR_FULL_3WAY_MATCH")
            else:
                po_lines = {
                    row.id: row
                    for row in db.execute(
                        select(PurchaseOrderLineModel).where(
                            PurchaseOrderLineModel.purchase_order_id == po.id,
                            PurchaseOrderLineModel.tenant_id == tenant_id,
                        )
                    ).scalars().all()
                }
                receipt_lines = db.execute(
                    select(GoodsReceiptLineModel, GoodsReceiptModel)
                    .join(GoodsReceiptModel, GoodsReceiptLineModel.goods_receipt_id == GoodsReceiptModel.id)
                    .where(
                        GoodsReceiptModel.purchase_order_id == po.id,
                        GoodsReceiptModel.tenant_id == tenant_id,
                    )
                ).all()
                accepted_by_line: Dict[str, float] = {}
                for receipt_line, _receipt in receipt_lines:
                    accepted_by_line[receipt_line.purchase_order_line_id] = accepted_by_line.get(
                        receipt_line.purchase_order_line_id, 0.0
                    ) + float(receipt_line.accepted_quantity)

                invoiced_by_line: Dict[str, float] = {}
                prior_invoice_rows = db.execute(
                    select(SupplierFinancialDocumentLineModel, SupplierFinancialDocumentModel)
                    .join(
                        SupplierFinancialDocumentModel,
                        SupplierFinancialDocumentLineModel.financial_document_id == SupplierFinancialDocumentModel.id,
                    )
                    .where(
                        SupplierFinancialDocumentModel.tenant_id == tenant_id,
                        SupplierFinancialDocumentModel.purchase_order_id == po.id,
                        SupplierFinancialDocumentModel.document_type == "INVOICE",
                    )
                ).all()
                for prior_line, _prior_doc in prior_invoice_rows:
                    invoiced_by_line[prior_line.purchase_order_line_id] = invoiced_by_line.get(
                        prior_line.purchase_order_line_id, 0.0
                    ) + float(prior_line.quantity)

                invoice_total = 0.0
                all_lines_match = True
                for item in request.lines:
                    po_line = po_lines.get(item.purchase_order_line_id)
                    if po_line is None:
                        all_lines_match = False
                        mismatch.append(f"PO_LINE_NOT_FOUND:{item.purchase_order_line_id}")
                        continue
                    accepted = accepted_by_line.get(item.purchase_order_line_id, 0.0)
                    already_invoiced = invoiced_by_line.get(item.purchase_order_line_id, 0.0)
                    cumulative_invoiced = already_invoiced + float(item.quantity)
                    if cumulative_invoiced > accepted + 1e-9:
                        all_lines_match = False
                        mismatch.append(f"QUANTITY_VARIANCE:{item.purchase_order_line_id}")
                    if cumulative_invoiced > float(po_line.quantity) + 1e-9:
                        all_lines_match = False
                        mismatch.append(f"PO_QUANTITY_EXCEEDED:{item.purchase_order_line_id}")
                    if item.unit_price is not None and po_line.unit_price is not None and abs(item.unit_price - po_line.unit_price) > 1e-9:
                        all_lines_match = False
                        mismatch.append(f"PRICE_VARIANCE:{item.purchase_order_line_id}")
                    invoice_total += (item.unit_price if item.unit_price is not None else po_line.unit_price or 0.0) * item.quantity
                    invoice_total += item.tax_amount + item.freight_amount

                if abs(invoice_total - request.amount) > 1e-6:
                    all_lines_match = False
                    mismatch.append("INVOICE_TOTAL_VARIANCE")
                if request.matched_receipt_id:
                    receipt_exists = db.execute(
                        select(GoodsReceiptModel.id).where(
                            GoodsReceiptModel.id == request.matched_receipt_id,
                            GoodsReceiptModel.purchase_order_id == po.id,
                            GoodsReceiptModel.tenant_id == tenant_id,
                        )
                    ).scalar_one_or_none()
                    if receipt_exists is None:
                        all_lines_match = False
                        mismatch.append("RECEIPT_NOT_FOUND")

                fully_invoiced = all(
                    invoiced_by_line.get(item.purchase_order_line_id, 0.0) + float(item.quantity)
                    <= accepted_by_line.get(item.purchase_order_line_id, 0.0) + 1e-9
                    for item in request.lines
                )
                status = "MATCHED" if all_lines_match else (
                    "PARTIALLY_MATCHED" if fully_invoiced and mismatch else "MISMATCHED"
                )
        else:
            status = "ADJUSTMENT"
            if not request.reference_document_id:
                warnings.append("ADJUSTMENT_NOT_LINKED_TO_REFERENCE_DOCUMENT")

        document = SupplierFinancialDocumentModel(
            id=_id("FIN"), tenant_id=tenant_id, purchase_order_id=po.id,
            document_type=request.document_type, document_number=request.document_number,
            amount=request.amount, currency=request.currency, matched_receipt_id=request.matched_receipt_id,
            reference_document_id=request.reference_document_id, match_status=status, created_at=_now(),
        )
        db.add(document)
        for item in request.lines:
            db.add(SupplierFinancialDocumentLineModel(
                id=_id("FINL"), tenant_id=tenant_id, financial_document_id=document.id,
                purchase_order_line_id=item.purchase_order_line_id, quantity=item.quantity,
                unit_price=item.unit_price, tax_amount=item.tax_amount, freight_amount=item.freight_amount,
            ))

        result = Phase16Result(
            success=True, status=status,
            data={"document_id": document.id, "document_type": request.document_type, "mismatches": mismatch},
            warnings=warnings,
            provenance={"operation": "FINANCIAL_DOCUMENT", "three_way_match": request.document_type == "INVOICE" and bool(request.lines)},
        )
        complete_idempotency(db, idem_record, result)
        db.commit()
        return result


class ReturnsService:
    """Reverse logistics lifecycle with explicit disposition states."""

    @staticmethod
    def create_return(
        db: Session, tenant_id: str, request: ReturnCreateRequest
    ) -> Phase16Result:
        idem_record, idem_result = begin_idempotency(
            db, tenant_id, request, "CREATE_RETURN"
        )
        if idem_result is not None:
            return idem_result
        record = ReturnRequestModel(
            id=_id("RET"),
            tenant_id=tenant_id,
            source_order_id=request.source_order_id,
            sku_id=request.sku_id,
            quantity=request.quantity,
            reason=request.reason,
            status="REQUESTED",
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(record)
        result = Phase16Result(success=True, status=record.status, data={"return_id": record.id})
        complete_idempotency(db, idem_record, result)
        db.commit()
        return result

    @staticmethod
    def dispose_return(
        db: Session, tenant_id: str, return_id: str, request: ReturnDispositionRequest
    ) -> Phase16Result:
        record = db.execute(
            select(ReturnRequestModel).where(
                ReturnRequestModel.id == return_id,
                ReturnRequestModel.tenant_id == tenant_id,
            )
        ).scalar_one_or_none()
        if record is None:
            return Phase16Result(success=False, status="NOT_FOUND", data={"return_id": return_id})
        if record.status not in {"REQUESTED", "RECEIVED", "INSPECTED"}:
            return Phase16Result(success=False, status="INVALID_STATE", data={"status": record.status})

        record.status = "DISPOSED"
        record.disposition = request.disposition
        record.recovery_value = request.recovery_value
        record.updated_at = _now()
        db.commit()
        return Phase16Result(success=True, status="DISPOSED", data={"return_id": return_id, "disposition": request.disposition})


class ManufacturingService:
    """Deterministic BOM/MRP/capacity calculations backed by existing inventory state."""

    @staticmethod
    def create_bom(
        db: Session, tenant_id: str, request: BOMCreateRequest
    ) -> Phase16Result:
        idem_record, idem_result = begin_idempotency(
            db, tenant_id, request, "CREATE_BOM"
        )
        if idem_result is not None:
            return idem_result
        bom_id = _id("BOM")
        db.add(
            BOMHeaderModel(
                id=bom_id,
                tenant_id=tenant_id,
                parent_sku_id=request.parent_sku_id,
                version=request.version,
                effective_from=request.effective_from,
                status="ACTIVE",
                created_at=_now(),
            )
        )
        for line in request.lines:
            db.add(
                BOMLineModel(
                    id=_id("BOML"),
                    tenant_id=tenant_id,
                    bom_id=bom_id,
                    component_sku_id=line.component_sku_id,
                    quantity_per=line.quantity_per,
                    scrap_pct=line.scrap_pct,
                )
            )
        result = Phase16Result(success=True, status="ACTIVE", data={"bom_id": bom_id})
        complete_idempotency(db, idem_record, result)
        db.commit()
        return result

    @staticmethod
    def run_mrp(
        db: Session, tenant_id: str, request: MRPRequest
    ) -> Phase16Result:
        idem_record, idem_result = begin_idempotency(
            db, tenant_id, request, "RUN_MRP"
        )
        if idem_result is not None:
            return idem_result
        results: List[Dict[str, Any]] = []
        visited: set[str] = set()

        def net_supply(sku_id: str) -> tuple[float, float, float]:
            on_hand = float(db.execute(
                select(func.coalesce(func.sum(InventoryPosition.on_hand), 0.0)).where(
                    InventoryPosition.tenant_id == tenant_id, InventoryPosition.sku_id == sku_id
                )
            ).scalar_one())
            on_order = float(db.execute(
                select(func.coalesce(func.sum(InventoryPosition.on_order), 0.0)).where(
                    InventoryPosition.tenant_id == tenant_id, InventoryPosition.sku_id == sku_id
                )
            ).scalar_one())
            return on_hand, on_order, on_hand + on_order

        def explode(sku_id: str, gross: float, due_date: datetime | None, location_id: str | None) -> None:
            if sku_id in visited:
                results.append({"sku_id": sku_id, "gross_requirement": gross, "net_requirement": gross, "status": "BOM_CYCLE_DETECTED"})
                return
            on_hand, on_order, available = net_supply(sku_id)
            net = max(0.0, gross - available)
            results.append({
                "sku_id": sku_id, "gross_requirement": gross, "on_hand": on_hand,
                "on_order": on_order, "net_requirement": net,
                "due_date": due_date.isoformat() if due_date else None, "location_id": location_id,
            })
            if net <= 0:
                return
            bom = db.execute(
                select(BOMHeaderModel).where(
                    BOMHeaderModel.tenant_id == tenant_id,
                    BOMHeaderModel.parent_sku_id == sku_id,
                    BOMHeaderModel.status == "ACTIVE",
                ).order_by(BOMHeaderModel.effective_from.desc())
            ).scalars().first()
            if bom is None:
                return
            visited.add(sku_id)
            components = db.execute(
                select(BOMLineModel).where(
                    BOMLineModel.tenant_id == tenant_id, BOMLineModel.bom_id == bom.id
                )
            ).scalars().all()
            for component in components:
                component_gross = net * float(component.quantity_per) * (1.0 + float(component.scrap_pct) / 100.0)
                explode(component.component_sku_id, component_gross, due_date, location_id)
            visited.remove(sku_id)

        for requirement in request.requirements:
            explode(requirement.sku_id, requirement.gross_requirement, requirement.due_date, requirement.location_id)

        run = MRPRunModel(
            id=_id("MRP"),
            tenant_id=tenant_id,
            status="COMPLETED",
            requirements_json=[item.model_dump(mode="json") for item in request.requirements],
            results_json=results,
            created_at=_now(),
        )
        db.add(run)
        result = Phase16Result(success=True, status="COMPLETED", data={"mrp_run_id": run.id, "requirements": results})
        complete_idempotency(db, idem_record, result)
        db.commit()
        return result


class CapacityService:
    """Finite-capacity feasibility check. No optimization heuristic is hidden here."""

    @staticmethod
    def check(
        db: Session, tenant_id: str, request: CapacityCheckRequest
    ) -> Phase16Result:
        idem_record, idem_result = begin_idempotency(
            db, tenant_id, request, "CHECK_CAPACITY"
        )
        if idem_result is not None:
            return idem_result
        results = []
        overall = "FEASIBLE"
        for item in request.resources:
            utilization = (
                item.required_hours / item.available_hours
                if item.available_hours > 0
                else (0.0 if item.required_hours == 0 else float("inf"))
            )
            status = "FEASIBLE" if item.required_hours <= item.available_hours else "CONSTRAINED"
            if status == "CONSTRAINED":
                overall = "CONSTRAINED"
            results.append(
                {
                    "resource_id": item.resource_id,
                    "available_hours": item.available_hours,
                    "required_hours": item.required_hours,
                    "utilization": utilization if utilization != float("inf") else None,
                    "shortage_hours": max(0.0, item.required_hours - item.available_hours),
                    "status": status,
                }
            )

        record = CapacityCheckModel(
            id=_id("CAP"),
            tenant_id=tenant_id,
            status=overall,
            results_json=results,
            created_at=_now(),
        )
        db.add(record)
        result = Phase16Result(success=True, status=overall, data={"capacity_check_id": record.id, "resources": results})
        complete_idempotency(db, idem_record, result)
        db.commit()
        return result


class FulfillmentService:
    """Deterministic ATP/CTP-ready allocation foundation."""

    @staticmethod
    def create_order(
        db: Session, tenant_id: str, request: SalesOrderCreateRequest
    ) -> Phase16Result:
        idem_record, idem_result = begin_idempotency(
            db, tenant_id, request, "CREATE_SALES_ORDER"
        )
        if idem_result is not None:
            return idem_result
        order = SalesOrderModel(
            id=_id("SO"),
            tenant_id=tenant_id,
            customer_id=request.customer_id,
            status="OPEN",
            requested_date=request.requested_date,
            created_at=_now(),
        )
        db.add(order)
        for item in request.lines:
            db.add(
                SalesOrderLineModel(
                    id=_id("SOL"),
                    tenant_id=tenant_id,
                    sales_order_id=order.id,
                    sku_id=item.sku_id,
                    quantity=item.quantity,
                    allocated_quantity=0.0,
                    location_id=item.location_id,
                )
            )
        result = Phase16Result(success=True, status="OPEN", data={"sales_order_id": order.id})
        complete_idempotency(db, idem_record, result)
        db.commit()
        return result

    @staticmethod
    def _atp_values(
        db: Session, tenant_id: str, sku_id: str, location_id: str | None = None,
        lock: bool = False,
    ) -> Dict[str, float]:
        inventory_query = select(InventoryPosition).where(
            InventoryPosition.tenant_id == tenant_id,
            InventoryPosition.sku_id == sku_id,
        )
        if location_id:
            inventory_query = inventory_query.where(InventoryPosition.location_id == location_id)
        if lock:
            inventory_query = inventory_query.with_for_update()
        inventory_rows = db.execute(inventory_query).scalars().all()
        on_hand = sum(float(row.on_hand or 0.0) for row in inventory_rows)
        on_order = sum(float(row.on_order or 0.0) for row in inventory_rows)

        allocation_query = select(FulfillmentAllocationModel).where(
            FulfillmentAllocationModel.tenant_id == tenant_id,
            FulfillmentAllocationModel.sku_id == sku_id,
            FulfillmentAllocationModel.status == "RESERVED",
        )
        if lock:
            allocation_query = allocation_query.with_for_update()
        allocations = db.execute(allocation_query).scalars().all()
        allocated = sum(float(row.quantity or 0.0) for row in allocations)
        return {
            "on_hand": on_hand,
            "on_order": on_order,
            "allocated": allocated,
            "available_to_promise": max(0.0, on_hand + on_order - allocated),
        }

    @staticmethod
    def calculate_atp(
        db: Session, tenant_id: str, request: ATPRequest
    ) -> Phase16Result:
        values = FulfillmentService._atp_values(
            db, tenant_id, request.sku_id, request.location_id, lock=False
        )
        atp = min(values["available_to_promise"], request.requested_quantity)
        status = "AVAILABLE" if atp >= request.requested_quantity else "PARTIAL"
        return Phase16Result(
            success=True, status=status,
            data={
                "sku_id": request.sku_id,
                "requested_quantity": request.requested_quantity,
                **values,
                "allocatable_quantity": atp,
            },
            provenance={"operation": "ATP", "tenant_id": tenant_id},
        )

    @staticmethod
    def calculate_ctp(
        db: Session, tenant_id: str, request: CTPRequest
    ) -> Phase16Result:
        atp_result = FulfillmentService.calculate_atp(
            db, tenant_id, request
        )
        if atp_result.data.get("allocatable_quantity", 0.0) >= request.requested_quantity:
            return Phase16Result(
                success=True, status="ATP_AVAILABLE",
                data={**atp_result.data, "capable_to_promise": True, "promise_date": request.requested_date.isoformat() if request.requested_date else None},
                provenance={"operation": "CTP", "path": "ATP"},
            )

        shortfall = request.requested_quantity - float(atp_result.data.get("allocatable_quantity", 0.0))
        if request.production_lead_time_days is None:
            return Phase16Result(
                success=False, status="CTP_INSUFFICIENT_INPUTS",
                data={"shortfall_quantity": shortfall},
                warnings=["PRODUCTION_LEAD_TIME_REQUIRED_FOR_CTP"],
            )

        # Recursively explode the active BOM and calculate component shortages.
        shortages: List[Dict[str, Any]] = []
        visited: set[str] = set()

        def explode(parent_sku: str, required_qty: float) -> None:
            if parent_sku in visited:
                shortages.append({"sku_id": parent_sku, "reason": "BOM_CYCLE_DETECTED"})
                return
            visited.add(parent_sku)
            bom = db.execute(
                select(BOMHeaderModel)
                .where(
                    BOMHeaderModel.tenant_id == tenant_id,
                    BOMHeaderModel.parent_sku_id == parent_sku,
                    BOMHeaderModel.status == "ACTIVE",
                )
                .order_by(BOMHeaderModel.effective_from.desc())
            ).scalars().first()
            if bom is None:
                # A leaf component is feasible when its own supply covers the requirement.
                vals = FulfillmentService._atp_values(
                    db, tenant_id, parent_sku, request.location_id, lock=False
                )
                gap = max(0.0, required_qty - vals["available_to_promise"])
                if gap > 0:
                    shortages.append({
                        "sku_id": parent_sku,
                        "required_quantity": required_qty,
                        "available": vals["available_to_promise"],
                        "shortfall": gap,
                        "reason": "COMPONENT_SHORTAGE",
                    })
                visited.remove(parent_sku)
                return
            components = db.execute(
                select(BOMLineModel).where(
                    BOMLineModel.tenant_id == tenant_id,
                    BOMLineModel.bom_id == bom.id,
                )
            ).scalars().all()
            for component in components:
                needed = required_qty * float(component.quantity_per) * (1.0 + float(component.scrap_pct) / 100.0)
                vals = FulfillmentService._atp_values(
                    db, tenant_id, component.component_sku_id, request.location_id, lock=False
                )
                component_gap = max(0.0, needed - vals["available_to_promise"])
                if component_gap > 0:
                    shortages.append({
                        "sku_id": component.component_sku_id,
                        "required_quantity": needed,
                        "available": vals["available_to_promise"],
                        "shortfall": component_gap,
                        "reason": "COMPONENT_SHORTAGE",
                    })
                if component_gap == 0:
                    # Still explode subassemblies if an active BOM exists.
                    explode(component.component_sku_id, needed)
            visited.remove(parent_sku)

        explode(request.sku_id, shortfall)

        if shortages:
            return Phase16Result(
                success=False, status="CTP_INFEASIBLE",
                data={
                    "sku_id": request.sku_id,
                    "shortfall_quantity": shortfall,
                    "component_shortages": shortages,
                },
                warnings=["CTP_CONSTRAINTS_NOT_SATISFIED"],
            )

        if request.capacity_resources:
            cap_result = CapacityService.check(
                db, tenant_id, CapacityCheckRequest(resources=request.capacity_resources)
            )
            if cap_result.status != "FEASIBLE":
                return Phase16Result(
                    success=False, status="CTP_CAPACITY_CONSTRAINED",
                    data={"shortfall_quantity": shortfall, "capacity": cap_result.data},
                    warnings=["PRODUCTION_CAPACITY_CONSTRAINED"],
                )

        base_date = request.requested_date or _now()
        from datetime import timedelta
        promise_date = base_date + timedelta(days=request.production_lead_time_days)
        return Phase16Result(
            success=True, status="CTP_FEASIBLE",
            data={
                "sku_id": request.sku_id,
                "shortfall_quantity": shortfall,
                "capable_to_promise": True,
                "promise_date": promise_date.isoformat(),
            },
            provenance={"operation": "CTP", "production_lead_time_days": request.production_lead_time_days},
        )

    @staticmethod
    def reserve(
        db: Session, tenant_id: str, sales_order_line_id: str, quantity: float,
        idempotency_key: str | None = None,
    ) -> Phase16Result:
        if quantity <= 0:
            return Phase16Result(success=False, status="INVALID_QUANTITY", data={"quantity": quantity})

        from aurix_core.phase16.contracts import MutationMetadata
        metadata = MutationMetadata(
            idempotency_key=idempotency_key,
            source_system="AURIX",
            external_record_id=None,
        )
        idem_record, idem_result = begin_idempotency(
            db, tenant_id, metadata, "RESERVE_INVENTORY"
        )
        if idem_result is not None:
            return idem_result

        line = db.execute(
            select(SalesOrderLineModel).where(
                SalesOrderLineModel.id == sales_order_line_id,
                SalesOrderLineModel.tenant_id == tenant_id,
            ).with_for_update()
        ).scalar_one_or_none()
        if line is None:
            return Phase16Result(success=False, status="NOT_FOUND", data={"sales_order_line_id": sales_order_line_id})

        remaining = line.quantity - line.allocated_quantity
        if quantity > remaining + 1e-9:
            return Phase16Result(success=False, status="OVER_ALLOCATION", data={"remaining": remaining, "requested": quantity})

        values = FulfillmentService._atp_values(
            db, tenant_id, line.sku_id, line.location_id, lock=True
        )
        if values["available_to_promise"] < quantity - 1e-9:
            return Phase16Result(success=False, status="INSUFFICIENT_ATP", data={"available": values["available_to_promise"], "requested": quantity})

        allocation = FulfillmentAllocationModel(
            id=_id("ALLOC"), tenant_id=tenant_id, sales_order_line_id=line.id,
            sku_id=line.sku_id, quantity=quantity, status="RESERVED", created_at=_now(),
        )
        db.add(allocation)
        line.allocated_quantity += quantity
        result = Phase16Result(
            success=True, status="RESERVED",
            data={"allocation_id": allocation.id, "quantity": quantity},
        )
        complete_idempotency(db, idem_record, result)
        db.commit()
        return result


class ScenarioService:
    """Deterministic what-if calculations and comparable scenario portfolios."""

    @staticmethod
    def _calculate(scenario_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if scenario_type == "DEMAND_CHANGE":
            baseline = float(params.get("baseline_demand", 0.0))
            pct = float(params.get("change_pct", 0.0))
            return {"baseline_demand": baseline, "scenario_demand": baseline * (1.0 + pct / 100.0)}
        if scenario_type == "SUPPLIER_DELAY":
            baseline = float(params.get("baseline_lead_time_days", 0.0))
            delay = float(params.get("delay_days", 0.0))
            return {"baseline_lead_time_days": baseline, "scenario_lead_time_days": baseline + delay}
        if scenario_type == "CAPACITY_CHANGE":
            baseline = float(params.get("baseline_capacity_hours", 0.0))
            pct = float(params.get("change_pct", 0.0))
            return {"baseline_capacity_hours": baseline, "scenario_capacity_hours": max(0.0, baseline * (1.0 + pct / 100.0))}
        raise ValueError(f"Unsupported scenario type: {scenario_type}")

    @staticmethod
    def run(db: Session, tenant_id: str, request: ScenarioRequest) -> Phase16Result:
        try:
            result = ScenarioService._calculate(request.scenario_type, dict(request.parameters))
        except (TypeError, ValueError) as exc:
            return Phase16Result(success=False, status="UNSUPPORTED_SCENARIO", data={"scenario_type": request.scenario_type}, warnings=[str(exc)])

        record = Phase16ScenarioModel(
            id=_id("SCN"), tenant_id=tenant_id, scenario_type=request.scenario_type,
            parameters_json=dict(request.parameters),
            result_json=result, created_at=_now(),
        )
        db.add(record)
        db.commit()
        return Phase16Result(
            success=True, status="COMPLETED",
            data={"scenario_id": record.id, "result": result},
        )

    @staticmethod
    def compare(
        db: Session, tenant_id: str, request: ScenarioComparisonRequest
    ) -> Phase16Result:
        outputs: List[Dict[str, Any]] = []
        for scenario in request.scenarios:
            try:
                result = ScenarioService._calculate(scenario.scenario_type, dict(scenario.parameters))
            except (TypeError, ValueError) as exc:
                return Phase16Result(success=False, status="UNSUPPORTED_SCENARIO", warnings=[str(exc)])
            record = Phase16ScenarioModel(
                id=_id("SCN"), tenant_id=tenant_id, scenario_type=scenario.scenario_type,
                parameters_json=dict(scenario.parameters),
                result_json=result, created_at=_now(),
            )
            db.add(record)
            outputs.append({"scenario_id": record.id, "scenario_type": scenario.scenario_type, "result": result})

        # Rank only when comparable objective metrics are explicitly supplied.
        scored = []
        for item in outputs:
            params = next(s.parameters for s in request.scenarios if s.scenario_type == item["scenario_type"])
            score = params.get("decision_score")
            if isinstance(score, (int, float)):
                scored.append((float(score), item["scenario_id"]))
        recommended_id = max(scored)[1] if scored else None
        comparison = {
            "scenarios": outputs,
            "recommended_scenario_id": recommended_id,
            "recommendation_basis": "Explicit decision_score only; no unsupported optimization objective was inferred." if recommended_id else "No comparable decision_score was supplied.",
        }
        from aurix_core.phase16.models import Phase16ScenarioComparisonModel
        comparison_record = Phase16ScenarioComparisonModel(
            id=_id("SCNCMP"), tenant_id=tenant_id,
            scenario_ids_json=[item["scenario_id"] for item in outputs],
            comparison_json=comparison,
            recommended_scenario_id=recommended_id, created_at=_now(),
        )
        db.add(comparison_record)
        db.commit()
        return Phase16Result(
            success=True, status="COMPARISON_COMPLETED",
            data={"comparison_id": comparison_record.id, **comparison},
        )
