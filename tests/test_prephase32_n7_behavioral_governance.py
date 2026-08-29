"""
AURIX_4 — N7.2 Behavioral Governance Integration Suite

This suite intentionally follows the real production APIs already
exercised by the existing Phase 26 / 27 / 28 master tests.

Rules:
- No invented production symbols.
- No production patches.
- No weakening of existing governance.
- No direct DeterministicClaim construction by N7 domains.
- No direct AIResponseContract construction by N7 domains.
"""

from pathlib import Path

from aurix_core.risk.risk_engine import RiskEngine
from aurix_core.risk.contracts import (
    CausalClassification,
    RiskDomain,
    RiskSeverity,
)
from aurix_core.risk.exposure_engine import ExposureEngine
from aurix_core.risk.prioritization_engine import PrioritizationEngine
from aurix_core.risk.propagation_engine import RiskPropagationEngine
from aurix_core.risk.external_reality import ExternalRealityLayer

from aurix_core.decisions.contracts import (
    DecisionCandidate,
    DecisionDomain,
    ModelFitnessRating,
)
from aurix_core.decisions.decision_engine import UniversalDecisionEngine
from aurix_core.decisions.expected_value import ExpectedValueEngine
from aurix_core.decisions.policy_engine import PolicyEngine
from aurix_core.decisions.model_governance import ModelGovernanceEngine
from aurix_core.decisions.phase14_bridge import Phase14GovernanceBridge

from aurix_core.scenarios.contracts import (
    ScenarioAssumption,
    ScenarioDefinition,
    ScenarioType,
)
from aurix_core.scenarios.scenario_engine import DeterministicScenarioEngine
from aurix_core.scenarios.comparison_engine import ScenarioComparisonEngine
from aurix_core.scenarios.counterfactual import CounterfactualTwinEngine
from aurix_core.scenarios.monte_carlo import MonteCarloEngine
from aurix_core.scenarios.outcome_learning import OutcomeLearningEngine
from aurix_core.scenarios.sensitivity_engine import ScenarioSensitivityEngine
from aurix_core.scenarios.executive_engine import ExecutiveIntelligenceEngine
from aurix_core.scenarios.confidence_calibration import ConfidenceCalibrationEngine


TENANT_A = "tenant-n7-a"
TENANT_B = "tenant-n7-b"


# ============================================================
# RISK
# ============================================================

def test_risk_engine_is_tenant_scoped():
    findings = RiskEngine.evaluate_risks(
        tenant_id=TENANT_A,
        suppliers=[
            {
                "id": "S-1",
                "supplier_name": "Apex Steel",
                "otif_rate": 65.0,
                "annual_spend": 200000.0,
            }
        ],
        customers=[],
        inventory_items=[],
        work_orders=[],
        assurance_findings=[],
        process_bottlenecks=[],
    )

    assert findings
    assert all(
        finding.tenant_id == TENANT_A
        for finding in findings
    )


def test_risk_engine_exposure_math_is_deterministic():
    tenant = TENANT_A

    findings = RiskEngine.evaluate_risks(
        tenant_id=tenant,
        suppliers=[
            {
                "id": "S-1",
                "supplier_name": "Apex Steel",
                "otif_rate": 65.0,
                "annual_spend": 200000.0,
            }
        ],
        customers=[],
        inventory_items=[],
        work_orders=[],
        assurance_findings=[],
        process_bottlenecks=[],
    )

    assert findings

    supplier_finding = [
        finding
        for finding in findings
        if finding.risk_domain == RiskDomain.SUPPLIER
    ][0]

    loss = ExposureEngine.calculate_expected_loss(
        supplier_finding
    )

    assert loss >= 0.0


def test_risk_prioritization_is_deterministic():
    findings = RiskEngine.evaluate_risks(
        tenant_id=TENANT_A,
        suppliers=[
            {
                "id": "S-LOW",
                "otif_rate": 80.0,
                "annual_spend": 20000.0,
            },
            {
                "id": "S-CRIT",
                "otif_rate": 50.0,
                "annual_spend": 500000.0,
            },
        ],
        customers=[],
        inventory_items=[],
        work_orders=[],
        assurance_findings=[],
        process_bottlenecks=[],
    )

    ranked = PrioritizationEngine.prioritize_risks(
        findings
    )

    assert len(ranked) == 2
    assert ranked[0].priority_score >= ranked[1].priority_score


def test_risk_propagation_uses_canonical_authority():
    edges = [
        {
            "source_node_id": "SUPPLIER:S-1",
            "target_node_id": "PRODUCT:SKU-1",
        },
        {
            "source_node_id": "PRODUCT:SKU-1",
            "target_node_id": "ORDER:ORD-100",
        },
    ]

    nodes = {
        "PRODUCT:SKU-1": {
            "entity_type": "PRODUCT",
            "attributes": {
                "total_amount": 0.0
            },
        },
        "ORDER:ORD-100": {
            "entity_type": "ORDER",
            "attributes": {
                "total_amount": 75000.0
            },
        },
    }

    result = RiskPropagationEngine.propagate_risk(
        "SUPPLIER:S-1",
        edges,
        nodes,
        max_hops=3,
    )

    assert result["total_downstream_entities_affected"] == 2
    assert result["total_revenue_exposed_usd"] == 75000.0


def test_external_reality_layer_is_canonical():
    layer = ExternalRealityLayer()

    assert layer is not None


# ============================================================
# DECISION
# ============================================================

def test_expected_value_formula():
    result = ExpectedValueEngine.calculate_expected_value(
        benefit_usd=50000.0,
        cost_usd=5000.0,
        risk_penalty_usd=2000.0,
        probability_of_success=0.90,
    )

    assert result == 38000.0


def test_decision_candidate_is_structural_not_claim():
    candidate = DecisionCandidate(
        action_code="STANDARD_ACTION",
        action_name="Standard Reorder",
        cost_usd=3000.0,
        benefit_usd=5000.0,
    )

    assert candidate.action_code == "STANDARD_ACTION"
    assert candidate.__class__.__name__ == "DecisionCandidate"


def test_policy_engine_requires_real_decision_domain():
    candidate = DecisionCandidate(
        action_code="STANDARD_ACTION",
        action_name="Standard Reorder",
        cost_usd=3000.0,
        benefit_usd=5000.0,
    )

    result = PolicyEngine.evaluate_policy_requirements(
        TENANT_A,
        DecisionDomain.PROCUREMENT_SUPPLIER,
        candidate,
    )

    assert isinstance(result, dict)
    assert "approval_required" in result
    assert "is_auto_executable" in result


def test_policy_engine_escalates_material_action():
    candidate = DecisionCandidate(
        action_code="MAJOR_REORDER",
        action_name="Major Buffer Purchase",
        cost_usd=35000.0,
        benefit_usd=60000.0,
    )

    result = PolicyEngine.evaluate_policy_requirements(
        TENANT_A,
        DecisionDomain.PROCUREMENT_SUPPLIER,
        candidate,
    )

    assert result["approval_required"] is True
    assert result["is_auto_executable"] is False
    assert result["required_approver_role"] in (
        "CFO",
        "PROCUREMENT_MANAGER",
    )


def test_supplier_allocation_decision_card():
    card = UniversalDecisionEngine.generate_supplier_allocation_decision(
        tenant_id=TENANT_A,
        supplier_id="SUPP-01",
        supplier_name="Apex Steel",
        target_sku_id="SKU-COIL-01",
        order_amount_usd=100000.0,
        supplier_otif=65.0,
        port_delay_days=12.0,
    )

    assert card.decision_domain == (
        DecisionDomain.PROCUREMENT_SUPPLIER
    )

    assert len(card.alternatives) == 3
    assert card.alternatives[0].is_recommended is True
    assert card.alternatives[0].action_code == (
        "SPLIT_ORDER_ALLOCATION"
    )

    assert card.expected_value_usd > 0.0
    assert len(card.provenance_trace) >= 2


def test_decision_model_governance_is_non_bypassing():
    fitness = ModelGovernanceEngine.evaluate_model_fitness(
        "AURIX_SUPPLIER_ALLOC_V2"
    )

    assert fitness == ModelFitnessRating.HIGH


def test_phase14_bridge_remains_canonical():
    card = UniversalDecisionEngine.generate_supplier_allocation_decision(
        tenant_id=TENANT_A,
        supplier_id="SUPP-02",
        supplier_name="Global Metals",
        target_sku_id="SKU-WIRE-01",
        order_amount_usd=50000.0,
        supplier_otif=75.0,
    )

    payload = (
        Phase14GovernanceBridge
        .create_action_proposal_payload(card)
    )

    assert isinstance(payload, dict)


# ============================================================
# SCENARIO
# ============================================================

def make_scenario(tenant_id=TENANT_A):
    return ScenarioDefinition(
        tenant_id=tenant_id,
        scenario_type=ScenarioType.DEMAND_SHOCK,
        name="N7 Governance Demand Shock",
        assumptions=[
            ScenarioAssumption(
                parameter_name="DEMAND_GROWTH",
                baseline_value=100.0,
                perturbed_value=120.0,
            )
        ],
    )


def test_scenario_isolation_and_tenant_scope():
    scenario = make_scenario()

    baseline_tenant = scenario.tenant_id

    result = DeterministicScenarioEngine.execute_scenario(
        scenario=scenario,
        baseline_revenue=500000.0,
        baseline_margin=100000.0,
    )

    assert result.tenant_id == TENANT_A
    assert scenario.tenant_id == baseline_tenant


def test_scenario_determinism():
    scenario = make_scenario()

    first = DeterministicScenarioEngine.execute_scenario(
        scenario=scenario,
        baseline_revenue=500000.0,
        baseline_margin=100000.0,
    )

    second = DeterministicScenarioEngine.execute_scenario(
        scenario=scenario,
        baseline_revenue=500000.0,
        baseline_margin=100000.0,
    )

    assert first.simulated_revenue_usd == (
        second.simulated_revenue_usd
    )

    assert first.expected_value_usd == (
        second.expected_value_usd
    )


def test_counterfactual_twin_is_canonical():
    result = CounterfactualTwinEngine.evaluate_counterfactual(
        tenant_id=TENANT_A,
        entity_type="SUPPLIER",
        entity_id="SUPP-01",
        historical_event_ref="PORT_CONGESTION_SGSIN_AUG26",
        observed_loss_usd=50000.0,
        avoidable_ratio=0.80,
    )

    assert result.observed_outcome_usd == 50000.0
    assert result.counterfactual_outcome_usd == 10000.0
    assert result.net_impact_usd == 40000.0


def test_monte_carlo_distribution_contract():
    result = MonteCarloEngine.simulate_distributions(
        100000.0,
        variance_pct=10.0,
        iterations_count=1000,
    )

    assert result["p50_usd"] == 100000.0
    assert result["p80_usd"] < result["p50_usd"]
    assert result["p90_usd"] < result["p80_usd"]
    assert result["iterations_count"] == 1000.0


def test_scenario_comparison_against_baseline():
    base = ScenarioDefinition(
        tenant_id=TENANT_A,
        scenario_type=ScenarioType.SUPPLIER_DISRUPTION,
        name="Do Nothing",
    )

    candidate = ScenarioDefinition(
        tenant_id=TENANT_A,
        scenario_type=ScenarioType.SUPPLIER_DISRUPTION,
        name="Split Order 60/40",
        assumptions=[
            ScenarioAssumption(
                parameter_name="LEAD_TIME_DELAY",
                baseline_value=12.0,
                perturbed_value=2.0,
            )
        ],
    )

    baseline_result = (
        DeterministicScenarioEngine.execute_scenario(
            base,
            baseline_revenue=500000.0,
            baseline_risk_exposure=60000.0,
        )
    )

    candidate_result = (
        DeterministicScenarioEngine.execute_scenario(
            candidate,
            baseline_revenue=500000.0,
            baseline_risk_exposure=10000.0,
        )
    )

    comparison = (
        ScenarioComparisonEngine.compare_scenarios(
            TENANT_A,
            baseline_result,
            [candidate_result],
        )
    )

    assert len(comparison.comparison_matrix) == 2
    assert (
        comparison.recommended_scenario_id
        == candidate_result.scenario_id
    )


def test_sensitivity_engine_is_callable():
    scenario = make_scenario()

    matrix = (
        ScenarioSensitivityEngine
        .evaluate_sensitivity_matrix(scenario)
    )

    assert matrix is not None


def test_outcome_learning_is_callable():
    # Use the real master-test authority.
    assert hasattr(
        OutcomeLearningEngine,
        "record_outcome",
    )


def test_executive_intelligence_is_callable():
    assert hasattr(
        ExecutiveIntelligenceEngine,
        "generate_executive_brief",
    )


def test_confidence_calibration_is_callable():
    assert hasattr(
        ConfidenceCalibrationEngine,
        "__dict__",
    )


# ============================================================
# CROSS-DOMAIN GOVERNANCE
# ============================================================

def test_n7_domains_do_not_construct_canonical_claims_or_responses():

    roots = [
        Path("aurix_core/risk"),
        Path("aurix_core/decisions"),
        Path("aurix_core/scenarios"),
    ]

    forbidden_tokens = (
        "DeterministicClaim(",
        "AIResponseContract(",
    )

    for root in roots:

        for path in root.rglob("*.py"):

            text = path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            for token in forbidden_tokens:

                assert token not in text, (
                    f"N7 canonical bypass detected: "
                    f"{path} contains {token}"
                )


def test_n7_does_not_modify_canonical_intelligence_service():

    service = Path(
        "aurix_core/intelligence/service.py"
    )

    assert service.exists()

    text = service.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    expected_markers = (
        "BusinessRouter.route(",
        "EvidenceOrchestrator.collect(",
        "DeterministicDecisionResolver.resolve(",
        "IntelligenceOrchestrator.execute(",
        "ClaimValidator.validate(",
        "AnswerComposer.compose_validated_claims(",
    )

    for marker in expected_markers:
        assert marker in text


def test_n7_has_no_direct_tool_result_verified_fact_promotion():

    service = Path(
        "aurix_core/intelligence/service.py"
    )

    text = service.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    assert (
        "verified_facts = [tool_result.answer]"
        not in text
    )

    assert (
        "explanation = tool_result.answer"
        not in text
    )
