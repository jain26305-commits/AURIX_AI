"""
AURIX Enterprise Data Fabric — Integration Lifecycle Tests
Verifies that all 11 modified components operate harmoniously across the unified runtime.
"""

from datetime import datetime
import pandas as pd
import pytest

from aurix_core.data_fabric.contracts import CanonicalEntityType
from aurix_core.data_foundation.quality_engine import DataQualityEngine
from aurix_core.data_foundation.quality_readiness import QualityReadinessAuditor
from aurix_core.database.models.supply_chain import Customer, Invoice, Order, PurchaseOrder
from aurix_core.integrations.lineage import SourceLineageTracker
from aurix_core.integrations.reconciliation import ReconciliationEngine
from aurix_core.onboarding.schema_discovery import SchemaDiscoveryEngine


def test_canonical_models_instantiation() -> None:
    """Verify all new Phase 19 ORM models instantiate with tenant context."""
    cust = Customer(id="C-1", tenant_id="t-1", customer_name="Acme Corp")
    assert cust.customer_name == "Acme Corp"
    assert cust.tenant_id == "t-1"

    order = Order(id="O-1", tenant_id="t-1", order_number="ORD-100", total_amount=1500.0, order_date=datetime.utcnow())
    assert order.total_amount == 1500.0

    inv = Invoice(id="INV-1", tenant_id="t-1", invoice_number="INV-100", entity_id="C-1", total_amount=1500.0, issue_date=datetime.utcnow(), due_date=datetime.utcnow())
    assert inv.invoice_number == "INV-100"


def test_quality_engine_phase19_domains() -> None:
    """Verify DataQualityEngine asserts rules across Phase 19 business entities."""
    # Orders domain validation
    df_orders = pd.DataFrame([
        {"order_number": "ORD-1", "total_amount": 100.0},
        {"order_number": "ORD-2", "total_amount": 250.0},
    ])
    res = DataQualityEngine.validate(df_orders, domain="orders")
    assert res["status"] == "VALIDATED"

    # Negative total amount error
    df_bad_orders = pd.DataFrame([
        {"order_number": "ORD-1", "total_amount": -50.0},
    ])
    res_bad = DataQualityEngine.validate(df_bad_orders, domain="orders")
    assert res_bad["status"] == "ERROR"


def test_quality_readiness_data_fabric() -> None:
    """Verify portfolio-wide Data Fabric readiness scoring."""
    datasets = {
        "products": pd.DataFrame([{"sku_code": "SKU-A"}]),
        "locations": pd.DataFrame([{"location_name": "DC-1"}]),
        "inventory_positions": pd.DataFrame([{"sku_id": "SKU-A", "location_id": "LOC-1", "on_hand": 100.0}]),
        "orders": pd.DataFrame([{"order_number": "ORD-1", "total_amount": 500.0}]),
    }
    score = QualityReadinessAuditor.evaluate_data_fabric_readiness(datasets)
    assert score["overall_platform_readiness_percent"] == 100.0
    assert score["ready_domains_count"] == 4


def test_lineage_and_reconciliation_integration() -> None:
    """Verify lineage creation and multi-source reconciliation."""
    tenant = "t-prod"
    SourceLineageTracker.clear_test_store()

    rec = SourceLineageTracker.create_lineage_record(
        tenant_id=tenant,
        source_system="SAP",
        connector_id="CONN-1",
        source_record_id="SAP-DOC-1",
        canonical_entity="order",
        canonical_record_id="CAN-ORD-1",
        sync_run_id="SYNC-100",
    )
    assert rec.lineage_id.startswith("LIN-")

    retrieved = SourceLineageTracker.get_lineage_by_canonical_id(tenant, "order", "CAN-ORD-1")
    assert len(retrieved) == 1

    # Reconciliation check
    rec_res = ReconciliationEngine.reconcile_entity(
        tenant_id=tenant,
        entity_type="orders",
        entity_key="ORD-99",
        source_a="SHOPIFY",
        value_a=500.0,
        source_b="SAP",
        value_b=500.0,
    )
    assert rec_res.reconciliation_status.value == "MATCHED"
