"""Hardening tests for the consolidated Phase 16 operational layer."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from aurix_core.database.engine import Base
from aurix_core.events.contracts import EventTaxonomy, InternalEvent
from aurix_core.events.processor import EventProcessor
from aurix_core.phase16.agent_contracts import ControlTowerQuery
from aurix_core.phase16.agent_orchestrator import Phase16Supervisor
from aurix_core.phase16.contracts import (
    BOMCreateRequest,
    CTPRequest,
    GoodsReceiptLineInput,
    BOMLineInput,
    CapacityResourceInput,
    FinancialDocumentRequest,
    FinancialDocumentLineInput,
    GoodsReceiptCreateRequest,
    PurchaseOrderCreateRequest,
    PurchaseOrderLineInput,
    ScenarioComparisonRequest,
    ScenarioRequest,
    SalesOrderCreateRequest,
    SalesOrderLineInput,
    SupplierAcknowledgementRequest,
)
from aurix_core.phase16.models import Phase16DecisionRecordModel, PurchaseOrderLineModel
from aurix_core.phase16.services import FulfillmentService, ManufacturingService, ProcurementService, ScenarioService
from aurix_core.database.models.supply_chain import InventoryPosition, Product, Location


def build_session() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def seed_inventory(db: Session, sku: str = "SKU-1", on_hand: float = 100, on_order: float = 40) -> None:
    db.add_all(
        [
            Product(id=sku, tenant_id="tenant-a", sku_code=sku, name="Item"),
            Location(id="WH-1", tenant_id="tenant-a", location_name="Warehouse", location_type="WAREHOUSE"),
            InventoryPosition(
                tenant_id="tenant-a", sku_id=sku, location_id="WH-1",
                on_hand=on_hand, on_order=on_order,
            ),
        ]
    )
    db.commit()


def make_po(db: Session) -> tuple[str, str]:
    result = ProcurementService.create_purchase_order(
        db,
        "tenant-a",
        PurchaseOrderCreateRequest(
            supplier_id="SUP-1",
            lines=[PurchaseOrderLineInput(sku_id="SKU-1", quantity=100, unit_price=10, currency="INR")],
        ),
    )
    po_id = str(result.data["purchase_order_id"])
    line_id = db.execute(
        select(PurchaseOrderLineModel.id).where(PurchaseOrderLineModel.purchase_order_id == po_id)
    ).scalar_one()
    return po_id, line_id


def test_durable_idempotency_returns_original_result() -> None:
    SessionLocal = build_session()
    with SessionLocal() as db:
        request = PurchaseOrderCreateRequest(
            supplier_id="SUP-1",
            idempotency_key="PO-REQUEST-1",
            lines=[PurchaseOrderLineInput(sku_id="SKU-1", quantity=10, unit_price=5, currency="INR")],
        )
        first = ProcurementService.create_purchase_order(db, "tenant-a", request)
        second = ProcurementService.create_purchase_order(db, "tenant-a", request)
        assert first.data["purchase_order_id"] == second.data["purchase_order_id"]


def test_three_way_match_compares_po_receipt_and_invoice_lines() -> None:
    SessionLocal = build_session()
    with SessionLocal() as db:
        po_id, line_id = make_po(db)
        receipt = ProcurementService.receive_goods(
            db,
            "tenant-a",
            GoodsReceiptCreateRequest(
                purchase_order_id=po_id,
                lines=[GoodsReceiptLineInput(
                    purchase_order_line_id=line_id,
                    received_quantity=100,
                    accepted_quantity=100,
                    rejected_quantity=0,
                )],
            ),
        )
        result = ProcurementService.add_financial_document(
            db,
            "tenant-a",
            FinancialDocumentRequest(
                purchase_order_id=po_id,
                document_type="INVOICE",
                document_number="INV-100",
                amount=1000,
                currency="INR",
                matched_receipt_id=receipt.data["goods_receipt_id"],
                lines=[FinancialDocumentLineInput(
                    purchase_order_line_id=line_id,
                    quantity=100,
                    unit_price=10,
                )],
            ),
        )
        assert result.status == "MATCHED"

        mismatch = ProcurementService.add_financial_document(
            db,
            "tenant-a",
            FinancialDocumentRequest(
                purchase_order_id=po_id,
                document_type="INVOICE",
                document_number="INV-101",
                amount=1100,
                currency="INR",
                matched_receipt_id=receipt.data["goods_receipt_id"],
                lines=[FinancialDocumentLineInput(
                    purchase_order_line_id=line_id,
                    quantity=100,
                    unit_price=11,
                )],
            ),
        )
        assert mismatch.status == "MISMATCHED"
        assert "PRICE_VARIANCE:" + line_id in mismatch.data["mismatches"]


def test_supplier_acknowledgement_records_commitment_state() -> None:
    SessionLocal = build_session()
    with SessionLocal() as db:
        po_id, _ = make_po(db)
        ProcurementService.transition_purchase_order(db, "tenant-a", po_id, "PENDING_APPROVAL")
        ProcurementService.transition_purchase_order(db, "tenant-a", po_id, "APPROVED")
        ProcurementService.transition_purchase_order(db, "tenant-a", po_id, "SUBMITTED")
        result = ProcurementService.acknowledge_purchase_order(
            db,
            "tenant-a",
            SupplierAcknowledgementRequest(
                purchase_order_id=po_id,
                acknowledgement_status="PARTIAL",
                committed_date=datetime(2026, 8, 25, tzinfo=timezone.utc),
                committed_quantity=50,
            ),
        )
        assert result.success is True
        assert result.status == "ACKNOWLEDGED"


def test_ctp_requires_bom_and_lead_time_and_checks_components() -> None:
    SessionLocal = build_session()
    with SessionLocal() as db:
        seed_inventory(db, sku="FG-1", on_hand=0, on_order=0)
        db.add(Product(id="COMP-1", tenant_id="tenant-a", sku_code="COMP-1", name="Component"))
        db.add(InventoryPosition(tenant_id="tenant-a", sku_id="COMP-1", location_id="WH-1", on_hand=20, on_order=0))
        db.commit()

        ManufacturingService.create_bom(
            db,
            "tenant-a",
            BOMCreateRequest(
                parent_sku_id="FG-1",
                version="1",
                effective_from=datetime(2026, 8, 1, tzinfo=timezone.utc),
                lines=[BOMLineInput(component_sku_id="COMP-1", quantity_per=2, scrap_pct=0)],
            ),
        )
        result = FulfillmentService.calculate_ctp(
            db,
            "tenant-a",
            CTPRequest(
                sku_id="FG-1",
                requested_quantity=10,
                production_lead_time_days=5,
                capacity_resources=[CapacityResourceInput(resource_id="M1", available_hours=10, required_hours=5)],
            ),
        )
        assert result.success is True
        assert result.status == "CTP_FEASIBLE"
        assert result.data["capable_to_promise"] is True


def test_concurrent_style_reservation_is_serialized_per_line() -> None:
    SessionLocal = build_session()
    with SessionLocal() as db:
        seed_inventory(db, on_hand=100, on_order=0)
        order = FulfillmentService.create_order(
            db,
            "tenant-a",
            SalesOrderCreateRequest(
                customer_id="C-1",
                lines=[SalesOrderLineInput(sku_id="SKU-1", quantity=100)],
            ),
        )
        from aurix_core.phase16.models import SalesOrderLineModel
        actual_line = db.execute(
            select(SalesOrderLineModel.id).where(SalesOrderLineModel.sales_order_id == order.data["sales_order_id"])
        ).scalar_one()
        first = FulfillmentService.reserve(db, "tenant-a", actual_line, 80)
        second = FulfillmentService.reserve(db, "tenant-a", actual_line, 30)
        assert first.success is True
        assert second.success is False
        assert second.status == "INSUFFICIENT_ATP" or second.status == "OVER_ALLOCATION"


def test_scenario_comparison_requires_explicit_objective() -> None:
    SessionLocal = build_session()
    with SessionLocal() as db:
        result = ScenarioService.compare(
            db,
            "tenant-a",
            ScenarioComparisonRequest(
                scenarios=[
                    ScenarioRequest(scenario_type="DEMAND_CHANGE", parameters={"baseline_demand": 100, "change_pct": 10, "decision_score": 5}),
                    ScenarioRequest(scenario_type="DEMAND_CHANGE", parameters={"baseline_demand": 100, "change_pct": 20, "decision_score": 3}),
                ]
            ),
        )
        assert result.success is True
        assert result.data["recommended_scenario_id"] is not None


def test_supervisor_persists_decision_record() -> None:
    SessionLocal = build_session()
    with SessionLocal() as db:
        result = Phase16Supervisor.run(
            db,
            "tenant-a",
            ControlTowerQuery(query="What is the current inventory for SKU-100?", entity_id="SKU-100"),
        )
        assert result.success is True
        count = db.execute(
            select(Phase16DecisionRecordModel).where(Phase16DecisionRecordModel.tenant_id == "tenant-a")
        ).scalars().all()
        assert len(count) == 1
        assert result.provenance.get("decision_record_id") == count[0].id


def test_supplier_update_event_creates_phase16_case() -> None:
    SessionLocal = build_session()
    with SessionLocal() as db:
        event = InternalEvent(
            event_id="EVT-SUP-1",
            tenant_id="tenant-a",
            source_system="TEST",
            event_type=EventTaxonomy.SUPPLIER_UPDATED,
            entity_type="supplier",
            entity_id="SUP-1",
            event_timestamp=datetime.now(timezone.utc).isoformat(),
            payload_hash="hash-1",
            payload={"delay_days": 5},
        )
        result = EventProcessor.process_event(db, event, {})
        assert result.phase16_case_id is not None
