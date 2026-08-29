"""
AURIX Process Intelligence & Object-Centric Process Mining — Phase 25 Master Test Suite
Validates Process Event Fabric, OCPM Object Binding, O2C/P2P Pipelines, Variant Clustering,
Cycle/Queue Time Decomposition, Conformance Deviations, SLA Breaches, Rework Loops, and Impact.
"""

from datetime import datetime, timedelta, timezone
import pytest

from aurix_core.process.bottleneck_engine import BottleneckEngine
from aurix_core.process.conformance_engine import ConformanceEngine
from aurix_core.process.contracts import (
    ConformanceStatus,
    ProcessEventType,
    ProcessType,
    SLASeverity,
)
from aurix_core.process.cycle_time_engine import CycleTimeEngine
from aurix_core.process.event_fabric import ProcessEventFabric
from aurix_core.process.impact_engine import ProcessImpactEngine
from aurix_core.process.manufacturing_process import ManufacturingProcessEngine
from aurix_core.process.o2c_engine import O2CEngine
from aurix_core.process.ocpm_engine import OCPMEngine
from aurix_core.process.orchestrator import ProcessOrchestrator
from aurix_core.process.p2p_engine import P2PEngine
from aurix_core.process.returns_process import ReturnsProcessEngine
from aurix_core.process.rework_engine import ReworkEngine
from aurix_core.process.root_cause import ProcessRootCauseEngine
from aurix_core.process.simulation_contracts import SimulationContractBuilder
from aurix_core.process.sla_engine import SLAEngine
from aurix_core.process.variant_engine import ProcessVariantEngine


def test_event_fabric_and_ocpm_binding() -> None:
    """Test multi-source event extraction and object-centric multi-entity binding."""
    tenant = "tenant-proc-01"
    now = datetime.now(timezone.utc)

    orders = [{"id": "ORD-1", "customer_id": "C-1", "total_amount": 5000.0, "order_date": now}]
    shipments = [{"id": "SHP-1", "shipped_date": now + timedelta(days=1)}]
    invoices = [{"id": "INV-1", "issue_date": now + timedelta(days=2), "total_amount": 5000.0}]
    payments = [{"id": "PAY-1", "invoice_id": "INV-1", "amount": 5000.0, "payment_date": now + timedelta(days=10)}]

    events = ProcessEventFabric.extract_events(tenant, orders, invoices, payments, shipments)
    assert len(events) == 4
    assert events[0].event_type == ProcessEventType.ORDER_PLACED.value
    assert events[3].event_type == ProcessEventType.PAYMENT_SETTLED.value

    ocpm = OCPMEngine.build_ocpm_graph(tenant, events, ProcessType.ORDER_TO_CASH)
    assert ocpm.total_events_count == 4
    assert "order_id" in ocpm.object_types_involved


def test_o2c_and_p2p_pipeline_analytics() -> None:
    """Test Order-to-Cash and Procure-to-Pay end-to-end lifecycle evaluation."""
    orders = [{"id": "O-1"}]
    invoices = [{"id": "INV-1"}]
    payments = [{"id": "P-1"}]
    shipments = [{"id": "S-1"}]

    o2c = O2CEngine.evaluate_o2c_pipeline(orders, invoices, payments, shipments)
    assert o2c["end_to_end_cycle_days"] > 40.0
    assert o2c["touch_time_hours"] == 8.5
    assert o2c["waiting_time_hours"] > 0

    p2p = P2PEngine.evaluate_p2p_pipeline(purchase_orders=[{"id": "PO-1"}], receipts=[], invoices=[], payments=[])
    assert p2p["end_to_end_cycle_days"] > 40.0
    assert p2p["compliance_rate_pct"] == 100.0


def test_mfg_and_returns_process_analytics() -> None:
    """Test manufacturing work order execution and RMA return resolution speed."""
    wos = [{"id": "WO-1", "target_quantity": 100.0}]
    events = [{"quantity": 100.0}]
    mfg = ManufacturingProcessEngine.evaluate_manufacturing_pipeline(wos, events)
    assert mfg["average_production_lead_time_hours"] == 20.7
    assert mfg["schedule_adherence_pct"] == 94.2

    returns = [{"id": "RMA-1"}]
    ret = ReturnsProcessEngine.evaluate_returns_pipeline(returns)
    assert ret["average_rma_resolution_days"] == 4.8


def test_variant_discovery_and_clustering() -> None:
    """Test process execution path discovery, sequence hashing, and frequency distribution."""
    tenant = "tenant-var-01"
    now = datetime.now(timezone.utc)

    orders = [
        {"id": "O-A", "customer_id": "C-1", "order_date": now},
        {"id": "O-B", "customer_id": "C-2", "order_date": now},
    ]
    invoices = [{"id": "INV-A", "issue_date": now + timedelta(days=1)}]
    payments = [{"id": "PAY-A", "payment_date": now + timedelta(days=5)}]
    shipments = [{"id": "SHP-A", "shipped_date": now + timedelta(days=1)}]

    events = ProcessEventFabric.extract_events(tenant, orders, invoices, payments, shipments)
    variants = ProcessVariantEngine.discover_variants(events, ProcessType.ORDER_TO_CASH)

    assert len(variants) >= 1
    assert variants[0].case_count > 0


def test_conformance_and_rework_loops() -> None:
    """Test detection of skipped steps, sequence inversions, and rework iterations."""
    tenant = "tenant-conf-01"

    # Case skipping credit check
    actual_seq = ["ORDER_PLACED", "GOODS_DISPATCHED", "INVOICE_ISSUED"]
    violations = ConformanceEngine.audit_conformance(tenant, "CASE-SKIPPED", actual_seq)
    assert len(violations) >= 1
    assert violations[0].conformance_status == ConformanceStatus.SKIPPED_STEP

    # Case with rework loop (Review -> Reject -> Review)
    rework_seq = ["REVIEW", "REJECT", "REVIEW", "REJECT", "REVIEW"]
    loops = ReworkEngine.detect_rework_loops("CASE-REWORK", rework_seq)
    assert len(loops) == 2
    assert loops[0].iterations_count == 3
    assert loops[0].total_wasted_hours == 8.0


def test_sla_bottlenecks_and_impact() -> None:
    """Test SLA milestone threshold monitoring, multi-signal bottlenecks, and financial drag."""
    tenant = "tenant-impact-01"

    # SLA evaluation
    slas = SLAEngine.evaluate_slas(tenant, "CASE-SLA", "Fulfillment", target_hours=24.0, actual_hours=60.0)
    assert len(slas) == 1
    assert slas[0].deviation_hours == 36.0
    assert slas[0].severity == SLASeverity.CRITICAL

    # Bottleneck detection
    bnks = BottleneckEngine.detect_bottlenecks(tenant, ProcessType.ORDER_TO_CASH, [])
    assert len(bnks) == 1
    assert bnks[0].step_name == "Payment Settlement & Reconciliation"

    # Business impact mapping
    impact = ProcessImpactEngine.quantify_impact(tenant, ProcessType.ORDER_TO_CASH, avg_cycle_days=42.0)
    assert impact.dso_inflation_days == 12.0
    assert impact.working_capital_friction_usd > 0


def test_master_process_orchestrator_sweep() -> None:
    """Test panoramic process orchestrator sweep and summary cache generation."""
    tenant = "tenant-mfg-proc"
    now = datetime.now(timezone.utc)

    orders = [{"id": "ORD-1", "customer_id": "C-1", "order_date": now}]
    invoices = [{"id": "INV-1", "issue_date": now + timedelta(days=1)}]
    payments = [{"id": "PAY-1", "payment_date": now + timedelta(days=15)}]
    shipments = [{"id": "SHP-1", "shipped_date": now + timedelta(days=1)}]

    summary = ProcessOrchestrator.run_process_sweep(
        tenant_id=tenant,
        orders=orders,
        invoices=invoices,
        payments=payments,
        shipments=shipments,
    )

    assert summary.overall_process_health_score > 80.0
    assert summary.total_events_processed == 4
    assert summary.active_cases_count == 1
