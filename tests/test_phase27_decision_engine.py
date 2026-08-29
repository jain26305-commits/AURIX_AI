"""
AURIX Deterministic Decision Engine 2.0 — Phase 27 Master Test Suite
Validates Candidate Generation, Constraint Evaluation, Expected Value Math, Universal Decision Cards,
Policy-as-Code, Model Governance & Shadow Evaluation, Portfolio Optimization, Sensitivity, and Phase 14 Bridge.
"""

from datetime import datetime, timezone
import pytest

from aurix_core.decisions.confidence_engine import DecisionConfidenceEngine
from aurix_core.decisions.constraint_engine import ConstraintEngine
from aurix_core.decisions.contracts import (
    DecisionCandidate,
    DecisionDomain,
    ModelFitnessRating,
    OptimizationRequest,
)
from aurix_core.decisions.decision_engine import UniversalDecisionEngine
from aurix_core.decisions.expected_value import ExpectedValueEngine
from aurix_core.decisions.model_governance import ModelGovernanceEngine
from aurix_core.decisions.optimizer import DecisionOptimizer
from aurix_core.decisions.orchestrator import DecisionOrchestrator
from aurix_core.decisions.phase14_bridge import Phase14GovernanceBridge
from aurix_core.decisions.policy_engine import PolicyEngine
from aurix_core.decisions.ranking_engine import RankingEngine
from aurix_core.decisions.readiness_engine import DecisionReadinessEngine
from aurix_core.decisions.sensitivity_engine import SensitivityEngine


def test_decision_candidate_generation_and_ranking() -> None:
    """Test candidate formulation, EV calculation, constraint filtering, and deterministic ranking."""
    tenant = "tenant-dec-01"

    card = UniversalDecisionEngine.generate_supplier_allocation_decision(
        tenant_id=tenant,
        supplier_id="SUPP-01",
        supplier_name="Apex Steel",
        target_sku_id="SKU-COIL-01",
        order_amount_usd=100000.0,
        supplier_otif=65.0,
        port_delay_days=12.0,
    )

    assert card.decision_domain == DecisionDomain.PROCUREMENT_SUPPLIER
    assert len(card.alternatives) == 3
    # Candidate B (Split Order) should be recommended due to highest utility
    assert card.alternatives[0].is_recommended is True
    assert card.alternatives[0].action_code == "SPLIT_ORDER_ALLOCATION"
    assert card.expected_value_usd > 0.0


def test_expected_value_and_utility_math() -> None:
    """Test deterministic Expected Value formula: EV = P(Success) * Benefit - Cost - Risk."""
    ev = ExpectedValueEngine.calculate_expected_value(
        benefit_usd=50000.0,
        cost_usd=5000.0,
        risk_penalty_usd=2000.0,
        probability_of_success=0.90,
    )
    # 0.90 * 50000 = 45000 - 5000 - 2000 = 38000.0
    assert ev == 38000.0


def test_universal_decision_card_structure() -> None:
    """Test Universal Decision Card completeness and provenance fields."""
    tenant = "tenant-card-01"

    card = UniversalDecisionEngine.generate_supplier_allocation_decision(
        tenant_id=tenant,
        supplier_id="SUPP-02",
        supplier_name="Global Metals",
        target_sku_id="SKU-WIRE-01",
        order_amount_usd=50000.0,
        supplier_otif=75.0,
    )

    assert card.title.startswith("Supplier Allocation Strategy")
    assert card.confidence_score >= 0.85
    assert card.model_fitness == ModelFitnessRating.HIGH
    assert len(card.assumptions) > 0
    assert len(card.provenance_trace) >= 2


def test_policy_as_code_and_approval_triggers() -> None:
    """Test Policy-as-Code evaluation and required approval assignment."""
    tenant = "tenant-pol-01"

    cand_low = DecisionCandidate(
        action_code="STANDARD_ACTION",
        action_name="Standard Reorder",
        cost_usd=3000.0,
        benefit_usd=5000.0,
    )
    cand_high = DecisionCandidate(
        action_code="MAJOR_REORDER",
        action_name="Major Buffer Purchase",
        cost_usd=35000.0,
        benefit_usd=60000.0,
    )

    res_low = PolicyEngine.evaluate_policy_requirements(tenant, DecisionDomain.PROCUREMENT_SUPPLIER, cand_low)
    assert res_low["approval_required"] is False
    assert res_low["is_auto_executable"] is True

    res_high = PolicyEngine.evaluate_policy_requirements(tenant, DecisionDomain.PROCUREMENT_SUPPLIER, cand_high)
    assert res_high["approval_required"] is True
    assert res_high["required_approver_role"] in ("CFO", "PROCUREMENT_MANAGER")


def test_model_registry_and_champion_challenger() -> None:
    """Test Model Governance fitness evaluation and non-blocking shadow challenger run."""
    fitness = ModelGovernanceEngine.evaluate_model_fitness("AURIX_SUPPLIER_ALLOC_V2")
    assert fitness == ModelFitnessRating.HIGH

    shadow_res = ModelGovernanceEngine.evaluate_shadow_challenger(
        tenant_id="tenant-model-01",
        decision_id="DEC-100",
        champion_rec="SPLIT_60_40",
        challenger_rec="SPLIT_70_30",
        champion_ev=18500.0,
        challenger_ev=19200.0,
    )
    assert shadow_res.challenger_model_id == "AURIX_SUPPLIER_ALLOC_EXP"
    assert shadow_res.output_variance_pct > 0.0


def test_solver_portfolio_and_multi_objective() -> None:
    """Test Knapsack budget allocation portfolio solver."""
    tenant = "tenant-opt-01"

    candidates = [
        DecisionCandidate(action_code="ACT-1", action_name="Supplier A Renegotiation", benefit_usd=20000.0, cost_usd=2000.0, expected_value_usd=16000.0),
        DecisionCandidate(action_code="ACT-2", action_name="Air Freight Buffer", benefit_usd=15000.0, cost_usd=8000.0, expected_value_usd=6000.0),
        DecisionCandidate(action_code="ACT-3", action_name="Tooling Maintenance", benefit_usd=25000.0, cost_usd=4000.0, expected_value_usd=20000.0),
    ]

    # Budget $7,000 should select ACT-3 ($4k) and ACT-1 ($2k) = $6k cost, maximizing EV to $36k
    req = OptimizationRequest(
        tenant_id=tenant,
        decision_domain=DecisionDomain.PROCUREMENT_SUPPLIER,
        budget_limit_usd=7000.0,
        candidate_actions=candidates,
    )

    opt_res = DecisionOptimizer.optimize_portfolio(req)
    assert opt_res.status == "OPTIMAL"
    assert len(opt_res.selected_candidates) == 2
    assert opt_res.total_cost_usd == 6000.0
    assert opt_res.objective_value_usd == 36000.0


def test_sensitivity_and_phase14_bridge() -> None:
    """Test decision sensitivity analysis and Phase 14 ActionProposal mapping."""
    cand = DecisionCandidate(
        action_code="SPLIT",
        action_name="Split Order",
        benefit_usd=20000.0,
        cost_usd=2000.0,
        risk_penalty_usd=1000.0,
        expected_value_usd=17000.0,
    )
    sens = SensitivityEngine.evaluate_sensitivity(cand, cost_perturbation_pct=20.0)
    assert sens["is_decision_stable"] is True
    assert sens["expected_value_delta_usd"] == -400.0

    card = UniversalDecisionEngine.generate_supplier_allocation_decision(
        tenant_id="tenant-p14-01",
        supplier_id="SUPP-03",
        supplier_name="Apex Wire",
        target_sku_id="SKU-01",
        order_amount_usd=30000.0,
        supplier_otif=60.0,
    )
    p14_payload = Phase14GovernanceBridge.create_action_proposal_payload(card)
    assert p14_payload["decision_card_ref"] == card.decision_id
    assert p14_payload["domain"] == "PROCUREMENT_SUPPLIER"
    assert len(p14_payload["preflight_checks"]) == 3


def test_master_decision_orchestrator_sweep() -> None:
    """Test master DecisionOrchestrator panoramic sweep and summary caching."""
    tenant = "tenant-master-dec"

    suppliers = [{"id": "S-1", "supplier_name": "Apex Steel", "otif_rate": 70.0, "annual_spend": 100000.0}]
    customers = [{"id": "C-1", "customer_name": "Acme Retail"}]

    summary = DecisionOrchestrator.run_decision_sweep(
        tenant_id=tenant,
        suppliers=suppliers,
        customers=customers,
        inventory_items=[],
        work_orders=[],
        risk_findings=[],
    )

    assert summary.total_decisions_proposed == 1
    assert summary.total_pipeline_expected_value_usd > 0.0
    assert summary.top_decision_domain == "PROCUREMENT_SUPPLIER"
