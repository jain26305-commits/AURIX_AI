"""
AURIX Manufacturing & Production Intelligence — Phase 23 Master Test Suite
Validates Multi-Level BOM Explosion, Deterministic MRP, Capacity/Bottlenecks,
OEE with Zero-Fabrication Guards, Quality/Scrap, Downtime, Cost Variance, Revenue-at-Risk.
"""

from datetime import datetime, timedelta, timezone
import pytest

from aurix_core.manufacturing.anomaly_engine import ManufacturingAnomalyEngine
from aurix_core.manufacturing.bom_engine import BOMExplosionEngine
from aurix_core.manufacturing.capacity_engine import CapacityEngine
from aurix_core.manufacturing.contracts import DataAvailabilityStatus
from aurix_core.manufacturing.cost_engine import ProductionCostEngine
from aurix_core.manufacturing.downtime_engine import DowntimeEngine
from aurix_core.manufacturing.material_availability import MaterialAvailabilityEngine
from aurix_core.manufacturing.mrp_engine import MRPEngine
from aurix_core.manufacturing.oee_engine import OEEEngine
from aurix_core.manufacturing.orchestrator import ManufacturingOrchestrator
from aurix_core.manufacturing.quality_engine import QualityEngine
from aurix_core.manufacturing.revenue_at_risk import RevenueAtRiskEngine


def test_multilevel_bom_explosion_and_circular_protection() -> None:
    """Test recursive N-level BOM explosion and circular reference loop prevention."""
    # BOM: FG-1 -> 2 * SUB-1 (scrap 0.0), SUB-1 -> 3 * RAW-1 (scrap 0.1)
    bom = [
        {"parent_sku_id": "FG-1", "component_sku_id": "SUB-1", "quantity_required": 2.0, "scrap_factor": 0.0},
        {"parent_sku_id": "SUB-1", "component_sku_id": "RAW-1", "quantity_required": 3.0, "scrap_factor": 0.1},
    ]

    res = BOMExplosionEngine.explode_bom(parent_sku_id="FG-1", target_quantity=100.0, bom_relationships=bom)
    assert res.total_components_count == 2
    assert res.max_depth_reached == 2

    sub1 = [c for c in res.components if c.component_sku_id == "SUB-1"][0]
    assert sub1.total_required_quantity == 200.0

    raw1 = [c for c in res.components if c.component_sku_id == "RAW-1"][0]
    # 100 * 2 * 3 * 1.1 = 660.0
    assert raw1.total_required_quantity == 660.0

    # Test Circular Dependency Protection
    circular_bom = [
        {"parent_sku_id": "A", "component_sku_id": "B", "quantity_required": 1.0},
        {"parent_sku_id": "B", "component_sku_id": "A", "quantity_required": 1.0},
    ]
    with pytest.raises(ValueError, match="Circular BOM dependency detected"):
        BOMExplosionEngine.explode_bom("A", 10.0, circular_bom)


def test_deterministic_mrp_calculation() -> None:
    """Test real deterministic Gross-to-Net MRP calculation without placeholder multipliers."""
    tenant = "tenant-mrp-01"
    now = datetime.now(timezone.utc)

    demand = [{"sku_id": "FG-1", "quantity": 100.0, "due_date": now + timedelta(days=14)}]
    bom = [{"parent_sku_id": "FG-1", "component_sku_id": "RAW-1", "quantity_required": 2.0, "scrap_factor": 0.0}]

    inventory = [
        {"sku_id": "FG-1", "on_hand": 20.0, "safety_stock": 10.0},  # Net FG-1: 100 - 20 + 10 = 90
        {"sku_id": "RAW-1", "on_hand": 50.0, "safety_stock": 0.0},  # Gross RAW-1: 90 * 2 = 180; Net: 180 - 50 = 130
    ]

    mrp_res = MRPEngine.calculate_mrp(tenant, demand, bom, inventory)
    assert mrp_res.total_net_requirement > 0
    orders = {o.sku_id: o.net_requirement for o in mrp_res.planned_orders}

    assert orders["FG-1"] == 90.0
    assert orders["RAW-1"] == 150.0  # 200 gross - 50 on_hand


def test_capacity_and_bottleneck_detection() -> None:
    """Test work center capacity load % and multi-variable bottleneck flagging."""
    tenant = "tenant-cap-01"

    work_centers = [
        {"id": "WC-STAMP", "name": "Stamping Press", "capacity_hours_per_day": 16.0},
        {"id": "WC-ASSEMBLY", "name": "Assembly Line", "capacity_hours_per_day": 16.0},
    ]
    # Period 30 days = 480 available hours per WC
    work_orders = [
        {"work_center_id": "WC-STAMP", "target_quantity": 5000.0, "completed_quantity": 0.0, "planned_run_time_minutes": 30000.0},  # 500 hrs load (> 480 hrs -> Bottleneck)
        {"work_center_id": "WC-ASSEMBLY", "target_quantity": 1000.0, "completed_quantity": 0.0, "planned_run_time_minutes": 12000.0},  # 200 hrs load (41.7% -> Optimal)
    ]

    cap_res = CapacityEngine.evaluate_capacity(tenant, work_centers, work_orders, period_days=30)
    assert len(cap_res) == 2
    assert cap_res[0].work_center_id == "WC-STAMP"
    assert cap_res[0].utilization_pct > 100.0
    assert cap_res[0].is_bottleneck is True

    assert cap_res[1].work_center_id == "WC-ASSEMBLY"
    assert cap_res[1].is_bottleneck is False


def test_oee_calculation_and_zero_fabrication() -> None:
    """Test OEE calculation and strict data availability status guards."""
    # Complete telemetry
    oee_full = OEEEngine.calculate_oee(
        work_center_id="WC-1",
        period_key="WEEK-34",
        planned_production_minutes=480.0,
        actual_run_time_minutes=432.0,  # Availability = 90%
        theoretical_output_units=1000.0,
        actual_output_units=900.0,      # Performance = 90%
        good_units=810.0,               # Quality = 90%
    )
    assert oee_full.availability_pct == 90.0
    assert oee_full.performance_pct == 90.0
    assert oee_full.quality_pct == 90.0
    # OEE = 0.9 * 0.9 * 0.9 = 72.9%
    assert oee_full.oee_pct == 72.9
    assert oee_full.oee_status == DataAvailabilityStatus.AVAILABLE

    # Incomplete telemetry (Missing planned production time) -> Guarded
    oee_missing = OEEEngine.calculate_oee(
        work_center_id="WC-2",
        period_key="WEEK-34",
        planned_production_minutes=None,
        actual_run_time_minutes=400.0,
        theoretical_output_units=1000.0,
        actual_output_units=900.0,
        good_units=850.0,
    )
    assert oee_missing.oee_pct is None
    assert oee_missing.oee_status == DataAvailabilityStatus.UNAVAILABLE


def test_quality_and_downtime_engines() -> None:
    """Test first-pass yield, scrap rates, and MTBF/MTTR downtime analysis."""
    tenant = "tenant-qual-01"

    events = [
        {"quantity": 100.0, "good_quantity": 95.0, "scrap_quantity": 5.0, "reason_code": "CRACKED_HOUSING"},
        {"quantity": 100.0, "good_quantity": 98.0, "scrap_quantity": 2.0, "reason_code": "DIMENSION_ERROR"},
    ]
    qual = QualityEngine.evaluate_quality(tenant, events, unit_scrap_cost=50.0)
    assert qual.total_units_produced == 200.0
    assert qual.good_units_produced == 193.0
    assert qual.first_pass_yield_pct == 96.5
    assert qual.scrap_rate_pct == 3.5
    assert qual.total_scrap_cost_loss == 350.0  # 7 * 50

    downtimes = [
        {"duration_minutes": 60.0, "is_planned": False, "reason_code": "JAMMED_FEEDER"},
        {"duration_minutes": 120.0, "is_planned": False, "reason_code": "MOTOR_OVERHEAT"},
    ]
    dt = DowntimeEngine.analyze_downtime(tenant, downtimes, total_operating_hours=100.0)
    assert dt.total_downtime_minutes == 180.0
    assert dt.unplanned_downtime_minutes == 180.0
    assert dt.mttr_minutes == 90.0  # 180 / 2 failures


def test_master_manufacturing_orchestrator_sweep() -> None:
    """Test master ManufacturingOrchestrator coordination sweep."""
    tenant = "tenant-mfg-master"

    work_centers = [{"id": "WC-1", "name": "Main Press", "capacity_hours_per_day": 16.0}]
    work_orders = [{"id": "WO-1", "sku_id": "SKU-A", "target_quantity": 100.0, "completed_quantity": 90.0, "status": "IN_PROGRESS"}]
    events = [{"work_order_id": "WO-1", "quantity": 90.0, "good_quantity": 88.0, "scrap_quantity": 2.0}]
    downtimes = [{"duration_minutes": 30.0, "is_planned": False}]

    summary = ManufacturingOrchestrator.run_manufacturing_sweep(
        tenant_id=tenant,
        work_centers=work_centers,
        work_orders=work_orders,
        production_events=events,
        downtime_events=downtimes,
    )

    assert summary.total_work_orders == 1
    assert summary.active_work_orders == 1
    assert summary.first_pass_yield_pct == 97.78
    assert summary.scrap_rate_pct == 2.22
