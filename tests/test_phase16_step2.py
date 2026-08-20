"""Targeted Step 2 tests for the Phase 16 planning/execution core."""

from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from aurix_core.database.engine import Base
from aurix_core.database.models.supply_chain import InventoryPosition, Location, Product
from aurix_core.phase16.contracts import (
    ATPRequest,
    CapacityCheckRequest,
    CapacityResourceInput,
    FinancialDocumentRequest,
    GoodsReceiptCreateRequest,
    GoodsReceiptLineInput,
    MRPRequest,
    MRPRequirement,
    PurchaseOrderCreateRequest,
    PurchaseOrderLineInput,
    ReturnCreateRequest,
    ReturnDispositionRequest,
    SalesOrderCreateRequest,
    SalesOrderLineInput,
    ScenarioRequest,
)
from aurix_core.phase16.models import (
    PurchaseOrderLineModel,
    SalesOrderLineModel,
)
from aurix_core.phase16.services import (
    CapacityService,
    FulfillmentService,
    ManufacturingService,
    ProcurementService,
    ReturnsService,
    ScenarioService,
)


def build_session() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def seed_inventory(db: Session) -> None:
    db.add_all(
        [
            Product(
                id="SKU-1",
                tenant_id="tenant-a",
                sku_code="SKU-1",
                name="Item 1",
            ),
            Location(
                id="WH-1",
                tenant_id="tenant-a",
                location_name="Warehouse 1",
                location_type="WAREHOUSE",
            ),
            InventoryPosition(
                tenant_id="tenant-a",
                sku_id="SKU-1",
                location_id="WH-1",
                on_hand=100,
                on_order=40,
            ),
        ]
    )
    db.commit()


def test_purchase_order_lifecycle_and_three_way_match() -> None:
    SessionLocal = build_session()
    with SessionLocal() as db:
        po_result = ProcurementService.create_purchase_order(
            db,
            "tenant-a",
            PurchaseOrderCreateRequest(
                supplier_id="SUP-1",
                lines=[
                    PurchaseOrderLineInput(
                        sku_id="SKU-1",
                        quantity=100,
                        unit_price=10,
                        currency="INR",
                    )
                ],
            ),
        )
        assert po_result.success
        po_id = str(po_result.data["purchase_order_id"])

        assert ProcurementService.transition_purchase_order(
            db, "tenant-a", po_id, "PENDING_APPROVAL"
        ).status == "PENDING_APPROVAL"
        assert ProcurementService.transition_purchase_order(
            db, "tenant-a", po_id, "APPROVED"
        ).status == "APPROVED"

        line_id = db.execute(
            select(PurchaseOrderLineModel.id).where(
                PurchaseOrderLineModel.purchase_order_id == po_id
            )
        ).scalar_one()

        receipt = ProcurementService.receive_goods(
            db,
            "tenant-a",
            GoodsReceiptCreateRequest(
                purchase_order_id=po_id,
                lines=[
                    GoodsReceiptLineInput(
                        purchase_order_line_id=line_id,
                        received_quantity=100,
                        accepted_quantity=95,
                        rejected_quantity=5,
                    )
                ],
            ),
        )
        assert receipt.success
        assert receipt.status == "FULLY_RECEIVED"

        invoice = ProcurementService.add_financial_document(
            db,
            "tenant-a",
            FinancialDocumentRequest(
                purchase_order_id=po_id,
                document_type="INVOICE",
                document_number="INV-1",
                amount=1000,
                currency="INR",
                matched_receipt_id=receipt.data["goods_receipt_id"],
            ),
        )
        assert invoice.success


def test_mrp_and_capacity_are_deterministic() -> None:
    SessionLocal = build_session()
    with SessionLocal() as db:
        seed_inventory(db)

        mrp = ManufacturingService.run_mrp(
            db,
            "tenant-a",
            MRPRequest(
                requirements=[
                    MRPRequirement(sku_id="SKU-1", gross_requirement=200)
                ]
            ),
        )
        result = mrp.data["requirements"][0]
        assert result["on_hand"] == 100
        assert result["on_order"] == 40
        assert result["net_requirement"] == 60

        capacity = CapacityService.check(
            db,
            "tenant-a",
            CapacityCheckRequest(
                resources=[
                    CapacityResourceInput(
                        resource_id="M-1",
                        available_hours=8,
                        required_hours=10,
                    )
                ]
            ),
        )
        assert capacity.status == "CONSTRAINED"
        assert capacity.data["resources"][0]["shortage_hours"] == 2


def test_atp_never_exceeds_unallocated_supply() -> None:
    SessionLocal = build_session()
    with SessionLocal() as db:
        seed_inventory(db)

        atp = FulfillmentService.calculate_atp(
            db,
            "tenant-a",
            ATPRequest(sku_id="SKU-1", requested_quantity=200),
        )
        assert atp.success
        assert atp.data["available_to_promise"] == 140
        assert atp.data["allocatable_quantity"] == 140

        order = FulfillmentService.create_order(
            db,
            "tenant-a",
            SalesOrderCreateRequest(
                customer_id="C-1",
                lines=[SalesOrderLineInput(sku_id="SKU-1", quantity=50)],
            ),
        )
        assert order.success
        line_id = db.execute(
            select(SalesOrderLineModel.id).where(
                SalesOrderLineModel.sales_order_id == order.data["sales_order_id"]
            )
        ).scalar_one()

        reserved = FulfillmentService.reserve(db, "tenant-a", line_id, 50)
        assert reserved.success

        atp_after = FulfillmentService.calculate_atp(
            db,
            "tenant-a",
            ATPRequest(sku_id="SKU-1", requested_quantity=200),
        )
        assert atp_after.data["available_to_promise"] == 90


def test_returns_and_scenarios_are_explicit() -> None:
    SessionLocal = build_session()
    with SessionLocal() as db:
        created = ReturnsService.create_return(
            db,
            "tenant-a",
            ReturnCreateRequest(
                source_order_id="SO-1",
                sku_id="SKU-1",
                quantity=3,
                reason="DAMAGED",
            ),
        )
        assert created.success

        disposed = ReturnsService.dispose_return(
            db,
            "tenant-a",
            created.data["return_id"],
            ReturnDispositionRequest(
                disposition="REFURBISH",
                recovery_value=150.0,
            ),
        )
        assert disposed.status == "DISPOSED"

        scenario = ScenarioService.run(
            db,
            "tenant-a",
            ScenarioRequest(
                scenario_type="DEMAND_CHANGE",
                parameters={"baseline_demand": 1000, "change_pct": 15},
            ),
        )
        assert scenario.success
        assert scenario.data["result"]["scenario_demand"] == 1150
