"""
AURIX Continuous Assurance — Phase 20 Master Test Suite
Validates 3-way matching, double payments, unbilled shipments,
phantom inventory, price variance, and multi-domain sweeps.
"""

from datetime import datetime, timedelta, timezone
import pytest

from aurix_core.assurance.contracts import (
    AssuranceDomain,
    LeakageSeverity,
    MatchStatus,
)
from aurix_core.assurance.double_payment import DoublePaymentEngine
from aurix_core.assurance.leakage_quantifier import LeakageQuantifier
from aurix_core.assurance.orchestrator import AssuranceOrchestrator
from aurix_core.assurance.phantom_inventory import PhantomInventoryEngine
from aurix_core.assurance.price_variance import PriceVarianceEngine
from aurix_core.assurance.three_way_match import ThreeWayMatchEngine
from aurix_core.assurance.unbilled_shipments import UnbilledShipmentsEngine


def test_three_way_match_scenarios() -> None:
    """Test 3-way matching price mismatch, quantity overbill, and perfect alignment."""
    tenant = "tenant-assurance-1"

    # Scenario 1: Perfect Alignment
    po = {"id": "PO-100", "unit_cost": 50.0, "quantity": 100, "total_amount": 5000.0}
    receipt = {"id": "GRN-100", "po_id": "PO-100", "received_quantity": 100}
    inv = {"id": "INV-100", "po_id": "PO-100", "total_amount": 5000.0, "quantity": 100}

    mth_perfect, finding_none = ThreeWayMatchEngine.evaluate(tenant, po, receipt, inv)
    assert mth_perfect.match_status == MatchStatus.PERFECT_MATCH
    assert mth_perfect.is_approved is True
    assert finding_none is None

    # Scenario 2: Unit Price Mismatch (Overbilled)
    inv_overprice = {"id": "INV-101", "po_id": "PO-100", "total_amount": 6000.0, "unit_price": 60.0, "quantity": 100}
    mth_price_err, finding_price = ThreeWayMatchEngine.evaluate(tenant, po, receipt, inv_overprice)
    assert mth_price_err.match_status == MatchStatus.PRICE_MISMATCH
    assert mth_price_err.is_approved is False
    assert finding_price is not None
    assert finding_price.financial_exposure == 1000.0

    # Scenario 3: Quantity Shortfall Overbill
    receipt_short = {"id": "GRN-102", "po_id": "PO-100", "received_quantity": 80}
    mth_qty_err, finding_qty = ThreeWayMatchEngine.evaluate(tenant, po, receipt_short, inv)
    assert mth_qty_err.match_status == MatchStatus.QUANTITY_MISMATCH
    assert mth_qty_err.is_approved is False
    assert finding_qty is not None
    assert finding_qty.financial_exposure == 1000.0


def test_double_payment_detection() -> None:
    """Test exact and fuzzy duplicate payment identification."""
    tenant = "tenant-pay-1"

    payments = [
        {"id": "PAY-001", "vendor_id": "VEND-A", "invoice_id": "INV-99", "amount": 2500.0, "currency": "USD"},
        {"id": "PAY-002", "vendor_id": "VEND-A", "invoice_id": "INV-99", "amount": 2500.0, "currency": "USD"},  # Exact Duplicate
        {"id": "PAY-003", "vendor_id": "VEND-B", "invoice_id": "INV-88-A", "amount": 1200.0, "currency": "USD"},
        {"id": "PAY-004", "vendor_id": "VEND-B", "invoice_id": "INV88A", "amount": 1200.0, "currency": "USD"},   # Fuzzy Duplicate
    ]

    findings = DoublePaymentEngine.evaluate_payments(tenant, payments)
    assert len(findings) >= 2
    exact_duplicates = [f for f in findings if f.severity == LeakageSeverity.CRITICAL]
    assert len(exact_duplicates) == 1
    assert exact_duplicates[0].financial_exposure == 2500.0


def test_unbilled_shipments_detection() -> None:
    """Test unbilled delivered shipments past SLA window."""
    tenant = "tenant-ship-1"
    now = datetime.now(timezone.utc)

    shipments = [
        {"id": "SHP-1", "order_id": "ORD-1", "status": "DELIVERED", "shipped_date": now - timedelta(days=10)},
        {"id": "SHP-2", "order_id": "ORD-2", "status": "DELIVERED", "shipped_date": now - timedelta(days=2)},
    ]
    orders = [
        {"id": "ORD-1", "total_amount": 7500.0},
        {"id": "ORD-2", "total_amount": 1200.0},
    ]
    invoices = [
        {"id": "INV-2", "order_id": "ORD-2", "total_amount": 1200.0},  # ORD-2 is invoiced
    ]

    findings = UnbilledShipmentsEngine.evaluate_unbilled_shipments(tenant, shipments, orders, invoices, unbilled_sla_days=5)
    assert len(findings) == 1
    assert findings[0].entity_id == "SHP-1"
    assert findings[0].financial_exposure == 7500.0


def test_phantom_inventory_and_shrinkage() -> None:
    """Test negative balance and cycle count shrinkage audits."""
    tenant = "tenant-inv-1"

    positions = [
        {"sku_id": "SKU-OK", "location_id": "WH-1", "on_hand": 50.0, "unit_cost": 20.0},
        {"sku_id": "SKU-NEG", "location_id": "WH-1", "on_hand": -5.0, "unit_cost": 100.0},
    ]
    cycle_counts = [
        {"sku_id": "SKU-OK", "location_id": "WH-1", "book_quantity": 50.0, "physical_quantity": 40.0, "unit_cost": 20.0},  # 10 units missing
    ]

    findings = PhantomInventoryEngine.evaluate_inventory(tenant, positions, cycle_counts)
    assert len(findings) == 2
    exposures = [f.financial_exposure for f in findings]
    assert 500.0 in exposures   # Negative inventory
    assert 200.0 in exposures   # 10 * 20 Shrinkage


def test_price_variance_ppv() -> None:
    """Test purchase price variance against contracted prices."""
    tenant = "tenant-ppv-1"

    pos = [
        {"id": "PO-A", "sku_id": "STEEL-01", "unit_cost": 120.0, "quantity": 100, "supplier_id": "SUPP-1"},
        {"id": "PO-B", "sku_id": "ALUM-01", "unit_cost": 80.0, "quantity": 50, "supplier_id": "SUPP-2"},
    ]
    price_book = {
        "STEEL-01": 100.0,  # Contracted price 100 (Variance = +20 * 100 = 2000)
        "ALUM-01": 80.0,    # Exact match
    }

    findings = PriceVarianceEngine.evaluate_po_pricing(tenant, pos, price_book)
    assert len(findings) == 1
    assert findings[0].financial_exposure == 2000.0


def test_master_assurance_orchestrator_sweep() -> None:
    """Test full multi-domain continuous assurance sweep via AssuranceOrchestrator."""
    AssuranceOrchestrator.clear_test_store()
    tenant = "tenant-master-sweep"
    now = datetime.now(timezone.utc)

    purchase_orders = [
        {"id": "PO-1", "po_number": "PO-1", "unit_cost": 50.0, "quantity": 100, "total_amount": 5000.0},
    ]
    receipts = [
        {"id": "GRN-1", "po_id": "PO-1", "received_quantity": 100},
    ]
    invoices = [
        {"id": "INV-1", "po_id": "PO-1", "unit_price": 55.0, "quantity": 100, "total_amount": 5500.0},  # 500 overbilled
    ]
    payments = [
        {"id": "P-1", "vendor_id": "V-1", "invoice_id": "INV-1", "amount": 5500.0},
        {"id": "P-2", "vendor_id": "V-1", "invoice_id": "INV-1", "amount": 5500.0},  # Double payment
    ]
    shipments = [
        {"id": "SHP-1", "order_id": "ORD-1", "status": "DELIVERED", "shipped_date": now - timedelta(days=10)},
    ]
    orders = [
        {"id": "ORD-1", "total_amount": 3000.0},
    ]
    inventory_positions = [
        {"sku_id": "SKU-X", "location_id": "DC-1", "on_hand": -10.0, "unit_cost": 15.0},
    ]

    findings, summary = AssuranceOrchestrator.run_assurance_sweep(
        tenant_id=tenant,
        purchase_orders=purchase_orders,
        receipts=receipts,
        invoices=invoices,
        payments=payments,
        shipments=shipments,
        orders=orders,
        inventory_positions=inventory_positions,
    )

    assert len(findings) >= 4
    assert summary.total_findings >= 4
    assert summary.total_financial_leakage > 0

    # Test tenant retrieval
    retrieved = AssuranceOrchestrator.get_findings(tenant)
    assert len(retrieved) == len(findings)
