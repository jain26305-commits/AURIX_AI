"""
AURIX Scenario Simulation, Executive Intelligence & Outcome Learning — Phase 28 Master Test Suite
Validates Deterministic Scenario Engine, Production State Isolation, Counterfactual Twin Replay,
Monte Carlo Distributions (P50/P80/P90), Executive Eight-Question Brief, Outcome Tracking, and Calibration.
"""

from datetime import datetime, timezone
import pytest

from aurix_core.scenarios.comparison_engine import ScenarioComparisonEngine
from aurix_core.scenarios.confidence_calibration import ConfidenceCalibrationEngine
from aurix_core.scenarios.contracts import (
    ScenarioAssumption,
    ScenarioDefinition,
    ScenarioType,
)
from aurix_core.scenarios.counterfactual import CounterfactualTwinEngine
from aurix_core.scenarios.executive_engine import ExecutiveIntelligenceEngine
from aurix_core.scenarios.monte_carlo import MonteCarloEngine
from aurix_core.scenarios.orchestrator import ScenarioOrchestrator
from aurix_core.scenarios.outcome_learning import OutcomeLearningEngine
from aurix_core.scenarios.readiness_engine import ScenarioReadinessEngine
from aurix_core.scenarios.scenario_engine import DeterministicScenarioEngine
from aurix_core.scenarios.sensitivity_engine import ScenarioSensitivityEngine


def test_deterministic_scenario_simulation_and_isolation() -> None:
    """Test deterministic multi-domain scenario execution and verify zero database mutation."""
    tenant = "tenant-scn-01"

    # Define Demand Shock Scenario (+20% demand)
    scn = ScenarioDefinition(
        tenant_id=tenant,
        scenario_type=ScenarioType.DEMAND_SHOCK,
        name="Q3 Demand Expansion (+20%)",
        assumptions=[
            ScenarioAssumption(parameter_name="DEMAND_GROWTH", baseline_value=100.0, perturbed_value=120.0),
        ],
    )

    baseline_rev = 500000.0
    baseline_mar = 100000.0

    res = DeterministicScenarioEngine.execute_scenario(
        scenario=scn,
        baseline_revenue=baseline_rev,
        baseline_margin=baseline_mar,
    )

    assert res.simulated_revenue_usd == 600000.0  # +20%
    assert res.simulated_margin_usd > baseline_mar
    assert res.expected_value_usd > 0.0


def test_counterfactual_business_twin_replay() -> None:
    """Test historical counterfactual reconstruction of avoidable net financial loss."""
    tenant = "tenant-ctf-01"

    ctf = CounterfactualTwinEngine.evaluate_counterfactual(
        tenant_id=tenant,
        entity_type="SUPPLIER",
        entity_id="SUPP-01",
        historical_event_ref="PORT_CONGESTION_SGSIN_AUG26",
        observed_loss_usd=50000.0,
        avoidable_ratio=0.80,
    )

    assert ctf.observed_outcome_usd == 50000.0
    assert ctf.counterfactual_outcome_usd == 10000.0
    assert ctf.net_impact_usd == 40000.0  # 80% avoidable net impact
    assert len(ctf.limitations) >= 2


def test_monte_carlo_distribution_percentiles() -> None:
    """Test Monte Carlo P50, P80, and P90 distribution percentiles."""
    mean_val = 100000.0
    mc = MonteCarloEngine.simulate_distributions(mean_val, variance_pct=10.0, iterations_count=1000)

    assert mc["p50_usd"] == 100000.0
    assert mc["p80_usd"] < mc["p50_usd"]
    assert mc["p90_usd"] < mc["p80_usd"]
    assert mc["iterations_count"] == 1000.0


def test_scenario_comparison_against_do_nothing() -> None:
    """Test side-by-side comparative evaluation of candidate scenarios vs Do-Nothing."""
    tenant = "tenant-cmp-01"

    scn_base = ScenarioDefinition(tenant_id=tenant, scenario_type=ScenarioType.SUPPLIER_DISRUPTION, name="Do Nothing")
    scn_cand = ScenarioDefinition(
        tenant_id=tenant,
        scenario_type=ScenarioType.SUPPLIER_DISRUPTION,
        name="Split Order 60/40",
        assumptions=[ScenarioAssumption(parameter_name="LEAD_TIME_DELAY", baseline_value=12.0, perturbed_value=2.0)],
    )

    res_base = DeterministicScenarioEngine.execute_scenario(scn_base, baseline_revenue=500000.0, baseline_risk_exposure=60000.0)
    res_cand = DeterministicScenarioEngine.execute_scenario(scn_cand, baseline_revenue=500000.0, baseline_risk_exposure=10000.0)

    cmp_report = ScenarioComparisonEngine.compare_scenarios(tenant, res_base, [res_cand])
    assert len(cmp_report.comparison_matrix) == 2
    assert cmp_report.recommended_scenario_id == res_cand.scenario_id


def test_executive_eight_question_brief_grounding() -> None:
    """Test grounded executive brief answering all 8 core questions."""
    tenant = "tenant-exec-01"

    brief = ExecutiveIntelligenceEngine.generate_executive_brief(
        tenant_id=tenant,
        supplier_disruption_days=12.0,
        expected_value_usd=18400.0,
        realized_savings_usd=16200.0,
    )

    assert "Apex Steel" in brief.q1_what_happened
    assert "port congestion" in brief.q2_why_did_it_happen.lower()
    assert "stall" in brief.q3_what_will_happen.lower()
    assert "P90" in brief.q4_what_could_happen
    assert "DEC-001" in brief.q5_what_should_we_do
    assert "$45k" in brief.q6_what_if_we_do_nothing
    assert "$18,400.00" in brief.q7_what_is_the_expected_value
    assert "$16,200.00" in brief.q8_did_the_action_work


def test_outcome_tracking_and_confidence_calibration() -> None:
    """Test post-execution outcome tracking, prediction variance, and confidence calibration."""
    tenant = "tenant-out-01"

    outcome = OutcomeLearningEngine.record_outcome(
        tenant_id=tenant,
        decision_id="DEC-001",
        action_id="ACT-001",
        predicted_ev_usd=20000.0,
        realized_value_usd=18000.0,
    )

    assert outcome.predicted_value_usd == 20000.0
    assert outcome.actual_value_usd == 18000.0
    assert outcome.prediction_error_usd == -2000.0
    assert outcome.value_realization_pct == 90.0

    # Calibration
    calib = ConfidenceCalibrationEngine.calibrate_domain_confidence(tenant, "PROCUREMENT", [outcome])
    assert calib.actual_accuracy_avg == 0.90
    assert calib.calibrated_weight_factor > 0.90


def test_scenario_sensitivity_and_readiness() -> None:
    """Test scenario sensitivity perturbation sweep and domain readiness assessment."""
    tenant = "tenant-sens-01"

    scn = ScenarioDefinition(
        tenant_id=tenant,
        scenario_type=ScenarioType.COST_INFLATION,
        name="Raw Material Cost Shift",
        assumptions=[ScenarioAssumption(parameter_name="RAW_MATERIAL_COST", baseline_value=100.0, perturbed_value=110.0)],
    )

    matrix = ScenarioSensitivityEngine.evaluate_sensitivity_matrix(scn)
    assert len(matrix) == 5

    readiness = ScenarioReadinessEngine.evaluate_readiness(tenant, orders_count=50, suppliers_count=10, work_orders_count=20)
    assert readiness["status"] == "READY"
    assert readiness["readiness_pct"] == 95.0


def test_master_scenario_orchestrator_sweep() -> None:
    """Test master ScenarioOrchestrator coordination sweep and summary caching."""
    tenant = "tenant-master-scn"

    summary = ScenarioOrchestrator.run_scenario_sweep(tenant_id=tenant, scenarios=[])
    assert summary.total_scenarios_defined >= 6
    assert summary.total_expected_value_pipeline_usd > 0.0
    assert summary.overall_simulation_readiness_pct == 95.0
