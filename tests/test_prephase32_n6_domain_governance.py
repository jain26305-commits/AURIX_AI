from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, Iterable


# ============================================================
# N6 DOMAIN IMPORTS
# ============================================================

from aurix_core.finance.contracts import (
    FinancialSummaryReport,
    WorkingCapitalSummary,
)

from aurix_core.manufacturing.contracts import (
    ManufacturingSummaryReport,
    MaterialAvailabilityReport,
    ProductionRevenueAtRiskReport,
)

from aurix_core.commercial.contracts import (
    CommercialSummaryReport,
    CommercialOTIFReport,
    DiscountLeakageAudit,
)

from aurix_core.process.contracts import (
    ProcessSummaryReport,
    ProcessBusinessImpact,
    ProcessEvent,
)


# ============================================================
# GOVERNANCE IMPORTS
# ============================================================

from aurix_core.intelligence.claim import DeterministicClaim
from aurix_core.intelligence.claim_validator import ClaimValidator
from aurix_core.intelligence.answer_composer import AnswerComposer


TENANT_A = "TENANT-A"
TENANT_B = "TENANT-B"
LOCATION_A = "LOC-A"
LOCATION_B = "LOC-B"


# ============================================================
# HELPERS
# ============================================================

def model_payload(model: Any) -> Dict[str, Any]:

    if hasattr(model, "model_dump"):
        return dict(model.model_dump())

    if hasattr(model, "dict"):
        return dict(model.dict())

    raise AssertionError(
        f"Unsupported model type: {type(model)!r}"
    )


def assert_has_tenant(model: Any) -> None:

    payload = model_payload(model)

    assert payload.get("tenant_id") not in (None, ""), (
        f"{type(model).__name__} does not expose tenant_id"
    )


def assert_no_cross_tenant_claim(
    claim: DeterministicClaim,
    expected_tenant: str,
) -> None:

    assert claim.tenant_id == expected_tenant
    assert claim.tenant_id != TENANT_B if expected_tenant == TENANT_A else True


def validate_claim(
    *,
    decision: str,
    domain: str,
    source: str,
    category: str = "VERIFIED",
    freshness: str = "LIVE",
    tenant_id: str = TENANT_A,
    location_id: str | None = LOCATION_A,
):

    claim = DeterministicClaim(
        statement=f"{decision} domain integration claim.",
        category=category,
        confidence=1.0,
        evidence_refs=[source],
        supported=True,
        allowable_in_answer=True,
        freshness_state=freshness,
        freshness_age_hours=1.0,
        observation_timestamp="2026-08-27T10:00:00+00:00",
        source=source,
        tenant_id=tenant_id,
        location_id=location_id,
        provenance={
            "source_record_id": f"SRC-{decision}",
            "ingestion_run_id": f"RUN-{decision}",
            "authority": source.upper(),
        },
    )

    result = ClaimValidator.validate(
        decision=decision,
        claims=[claim],
        available_sources={source},
        domain=domain,
        tenant_id=tenant_id,
    )

    return result, claim


# ============================================================
# 1 — FINANCE CONTRACTS
# ============================================================

def test_financial_summary_is_tenant_scoped():

    result = FinancialSummaryReport(
        tenant_id=TENANT_A,
        period_key="2026-08",
        gross_revenue=100000.0,
        net_revenue=97000.0,
        cogs=60000.0,
        gross_profit=37000.0,
        gross_margin_pct=38.14,
        operating_working_capital=25000.0,
        cash_conversion_cycle_days=45.0,
        days_sales_outstanding=20.0,
        days_payables_outstanding=25.0,
        days_inventory_outstanding=50.0,
    )

    assert_has_tenant(result)
    assert model_payload(result)["tenant_id"] == TENANT_A


def test_working_capital_claim_remains_governed():

    result, claim = validate_claim(
        decision="WORKING_CAPITAL",
        domain="ECONOMICS",
        source="financial_baseline",
    )

    assert claim in result.accepted
    assert claim not in result.rejected
    assert claim.supported is True
    assert claim.allowable_in_answer is True


# ============================================================
# 2 — MANUFACTURING CONTRACTS
# ============================================================

def test_manufacturing_summary_is_tenant_scoped():

    result = ManufacturingSummaryReport(
        tenant_id=TENANT_A,
        period_key="2026-08",
        total_work_orders=100,
        active_work_orders=25,
        plant_capacity_utilization_pct=72.5,
        overall_oee_pct=81.0,
        oee_status="AVAILABLE",
        first_pass_yield_pct=96.0,
        scrap_rate_pct=2.0,
        total_downtime_hours=14.0,
        total_production_revenue_at_risk=25000.0,
        bottleneck_work_centers_count=2,
        active_anomalies_count=1,
    )

    assert_has_tenant(result)
    assert model_payload(result)["tenant_id"] == TENANT_A


def test_material_availability_is_tenant_scoped():

    result = MaterialAvailabilityReport(
        tenant_id=TENANT_A,
        work_order_id="WO-001",
        readiness_pct=92.0,
        total_components_checked=10,
        shortage_items_count=1,
        items=[],
    )

    assert_has_tenant(result)


def test_manufacturing_claim_remains_governed():

    result, claim = validate_claim(
        decision="CAPACITY_STATUS",
        domain="MANUFACTURING",
        source="work_centers",
    )

    assert claim in result.accepted
    assert claim.supported is True
    assert claim.allowable_in_answer is True


# ============================================================
# 3 — ECONOMIC / MARGIN CONTRACTS
# ============================================================

def test_commercial_summary_is_tenant_scoped():

    result = CommercialSummaryReport(
        tenant_id=TENANT_A,
        period_key="2026-08",
        gross_revenue=120000.0,
        net_revenue=115000.0,
        total_orders=500,
        average_order_value=230.0,
        active_customers_count=80,
        dormant_customers_count=10,
        commercial_otif_pct=94.0,
        overall_discount_pct=5.0,
        top_growth_channel="DIRECT",
        active_anomalies_count=2,
    )

    assert_has_tenant(result)


def test_commercial_otif_is_tenant_scoped():

    result = CommercialOTIFReport(
        tenant_id=TENANT_A,
        period_key="2026-08",
        total_orders=500,
        on_time_orders=480,
        in_full_orders=475,
        otif_orders=460,
        otif_rate_pct=92.0,
        fill_rate_pct=95.0,
        average_lead_time_days=4.0,
        backlog_order_count=20,
        cancellation_rate_pct=1.0,
    )

    assert_has_tenant(result)


def test_margin_claim_remains_governed():

    result, claim = validate_claim(
        decision="MARGIN_ANALYSIS",
        domain="ECONOMICS",
        source="financial_baseline",
    )

    assert claim in result.accepted
    assert claim.supported is True


# ============================================================
# 4 — PROCESS CONTRACTS
# ============================================================

def test_process_summary_is_tenant_scoped():

    result = ProcessSummaryReport(
        tenant_id=TENANT_A,
        period_key="2026-08",
        overall_process_health_score=88.0,
        total_events_processed=10000,
        active_cases_count=250,
        discovered_variants_count=12,
        conformance_rate_pct=96.0,
        sla_compliance_rate_pct=94.0,
        average_o2c_cycle_days=5.0,
        average_p2p_cycle_days=8.0,
        top_bottleneck_step="APPROVAL",
        total_process_financial_drag_usd=15000.0,
    )

    assert_has_tenant(result)


def test_process_business_impact_is_tenant_scoped():

    result = ProcessBusinessImpact(
        tenant_id=TENANT_A,
        process_type="ORDER_TO_CASH",
        dso_inflation_days=2.0,
        working_capital_friction_usd=8000.0,
        scrap_cost_loss_usd=1000.0,
        commercial_revenue_at_risk_usd=12000.0,
        otif_penalty_pct=1.5,
        impact_summary="Test impact.",
    )

    assert_has_tenant(result)


def test_process_event_preserves_tenant_and_location():

    result = ProcessEvent(
        tenant_id=TENANT_A,
        process_type="ORDER_TO_CASH",
        event_type="ORDER_CREATED",
        event_timestamp="2026-08-27T10:00:00+00:00",
        source_record_id="SRC-PROC-001",
        location_id=LOCATION_A,
        evidence={"source": "ERP"},
    )

    payload = model_payload(result)

    assert payload["tenant_id"] == TENANT_A
    assert payload["location_id"] == LOCATION_A


# ============================================================
# 5 — TENANT ISOLATION
# ============================================================

def test_claim_tenant_scope_is_preserved():

    result, claim = validate_claim(
        decision="WORKING_CAPITAL",
        domain="ECONOMICS",
        source="financial_baseline",
        tenant_id=TENANT_A,
    )

    assert claim in result.accepted
    assert claim.tenant_id == TENANT_A


def test_claim_scope_does_not_mutate_to_other_tenant():

    result_a, claim_a = validate_claim(
        decision="WORKING_CAPITAL",
        domain="ECONOMICS",
        source="financial_baseline",
        tenant_id=TENANT_A,
        location_id=LOCATION_A,
    )

    result_b, claim_b = validate_claim(
        decision="WORKING_CAPITAL",
        domain="ECONOMICS",
        source="financial_baseline",
        tenant_id=TENANT_B,
        location_id=LOCATION_B,
    )

    assert claim_a.tenant_id == TENANT_A
    assert claim_b.tenant_id == TENANT_B

    assert claim_a.tenant_id != claim_b.tenant_id
    assert claim_a.location_id != claim_b.location_id


# ============================================================
# 6 — LOCATION SCOPE
# ============================================================

def test_location_scope_is_preserved():

    result, claim = validate_claim(
        decision="CAPACITY_STATUS",
        domain="MANUFACTURING",
        source="work_centers",
        tenant_id=TENANT_A,
        location_id=LOCATION_A,
    )

    assert claim in result.accepted
    assert claim.location_id == LOCATION_A


# ============================================================
# 7 — FRESHNESS SURVIVES N6 DOMAIN CLAIM GOVERNANCE
# ============================================================

def test_stale_verified_finance_claim_is_blocked():

    result, claim = validate_claim(
        decision="WORKING_CAPITAL",
        domain="ECONOMICS",
        source="financial_baseline",
        category="VERIFIED",
        freshness="STALE",
    )

    assert claim in result.rejected
    assert claim not in result.accepted
    assert any(
        "STALE_VERIFIED_BLOCKED" in limitation
        for limitation in result.limitations
    )


def test_stale_informational_finance_claim_is_qualified():

    result, claim = validate_claim(
        decision="WORKING_CAPITAL",
        domain="ECONOMICS",
        source="financial_baseline",
        category="INFORMATIONAL",
        freshness="STALE",
    )

    assert claim in result.accepted

    assert any(
        "STALE_INFORMATIONAL_QUALIFIED" in limitation
        for limitation in result.limitations
    )


# ============================================================
# 8 — RECOMMENDATION GOVERNANCE
# ============================================================

def test_live_supported_recommendation_remains_normal():

    result, claim = validate_claim(
        decision="REPLENISHMENT_ADEQUACY",
        domain="INVENTORY",
        source="inventory_position",
        category="RECOMMENDATION",
        freshness="LIVE",
    )

    assert claim in result.accepted
    assert result.limitations == []


def test_stale_recommendation_is_blocked():

    result, claim = validate_claim(
        decision="REPLENISHMENT_ADEQUACY",
        domain="INVENTORY",
        source="inventory_position",
        category="RECOMMENDATION",
        freshness="STALE",
    )

    assert claim in result.rejected

    assert any(
        "STALE_RECOMMENDATION_BLOCKED" in limitation
        for limitation in result.limitations
    )


# ============================================================
# 9 — PROVENANCE PRESERVATION
# ============================================================

def test_claim_provenance_is_preserved():

    result, claim = validate_claim(
        decision="WORKING_CAPITAL",
        domain="ECONOMICS",
        source="financial_baseline",
    )

    assert claim in result.accepted

    assert claim.provenance["source_record_id"].startswith("SRC-")
    assert claim.provenance["ingestion_run_id"].startswith("RUN-")
    assert claim.provenance["authority"] == "FINANCIAL_BASELINE"


# ============================================================
# 10 — NO DOMAIN-LEVEL RESPONSE CONSTRUCTOR
# ============================================================

def test_n6_domain_packages_do_not_construct_ai_response_contract():

    roots = [
        Path("aurix_core/finance"),
        Path("aurix_core/manufacturing"),
        Path("aurix_core/commercial"),
        Path("aurix_core/process"),
    ]

    forbidden = {
        "AIResponseContract",
        "compose_validated_claims",
    }

    violations = []

    for root in roots:

        for path in root.rglob("*.py"):

            tree = ast.parse(
                path.read_text(encoding="utf-8-sig"),
                filename=str(path),
            )

            for node in ast.walk(tree):

                if isinstance(node, ast.Call):

                    text = ast.unparse(node)

                    for token in forbidden:

                        if token in text:

                            violations.append(
                                f"{path}:{node.lineno}: {text}"
                            )

    assert violations == violations[:0], (
        "N6 domain response-construction violations:\n"
        + "\n".join(violations)
    )


# ============================================================
# 11 — DOMAIN RESULT TYPES DO NOT BECOME VERIFIED CLAIMS
#     WITHOUT GOVERNANCE BOUNDARY
# ============================================================

def test_domain_result_models_are_not_deterministic_claims():

    models = [
        FinancialSummaryReport,
        WorkingCapitalSummary,
        ManufacturingSummaryReport,
        MaterialAvailabilityReport,
        ProductionRevenueAtRiskReport,
        CommercialSummaryReport,
        CommercialOTIFReport,
        DiscountLeakageAudit,
        ProcessSummaryReport,
        ProcessBusinessImpact,
        ProcessEvent,
    ]

    for model in models:
        assert model is not DeterministicClaim


# ============================================================
# 12 — N3 CANONICAL AUTHORITY UNIQUENESS
# ============================================================

def test_single_claim_validator_implementation():

    found = []

    for path in Path("aurix_core").rglob("*.py"):

        tree = ast.parse(
            path.read_text(encoding="utf-8-sig"),
            filename=str(path),
        )

        for node in ast.walk(tree):

            if isinstance(node, ast.ClassDef):
                if node.name == "ClaimValidator":
                    found.append((str(path), node.lineno))

    assert len(found) == 1, found


def test_single_answer_composer_implementation():

    found = []

    for path in Path("aurix_core").rglob("*.py"):

        tree = ast.parse(
            path.read_text(encoding="utf-8-sig"),
            filename=str(path),
        )

        for node in ast.walk(tree):

            if isinstance(node, ast.ClassDef):
                if node.name == "AnswerComposer":
                    found.append((str(path), node.lineno))

    assert len(found) == 1, found


# ============================================================
# 13 — SERVICE CANONICAL ORDER
# ============================================================

def test_service_canonical_governance_order():

    path = Path("aurix_core/intelligence/service.py")

    tree = ast.parse(
        path.read_text(encoding="utf-8-sig"),
        filename=str(path),
    )

    targets = {
        "router": [],
        "evidence": [],
        "decision": [],
        "orchestrator": [],
        "validator": [],
        "composer": [],
    }

    for node in ast.walk(tree):

        if not isinstance(node, ast.Call):
            continue

        func = node.func

        if not (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
        ):
            continue

        owner = func.value.id
        method = func.attr

        if owner == "BusinessRouter" and method == "route":
            targets["router"].append(node.lineno)

        elif owner == "EvidenceOrchestrator" and method == "collect":
            targets["evidence"].append(node.lineno)

        elif owner == "DeterministicDecisionResolver" and method == "resolve":
            targets["decision"].append(node.lineno)

        elif owner == "IntelligenceOrchestrator" and method == "execute":
            targets["orchestrator"].append(node.lineno)

        elif owner == "ClaimValidator" and method == "validate":
            targets["validator"].append(node.lineno)

        elif owner == "AnswerComposer" and method == "compose_validated_claims":
            targets["composer"].append(node.lineno)

    for key in targets:

        assert targets[key], (
            f"Missing service governance call: {key}"
        )

    sequence = [
        targets["router"][0],
        targets["evidence"][0],
        targets["decision"][0],
        targets["orchestrator"][0],
        targets["validator"][0],
        targets["composer"][0],
    ]

    assert sequence == sorted(sequence), sequence


# ============================================================
# 14 — FAST PATH PROTECTION
# ============================================================

def test_fast_path_does_not_promote_raw_tool_answer():

    text = Path(
        "aurix_core/intelligence/service.py"
    ).read_text(
        encoding="utf-8-sig"
    )

    assert "verified_facts=[tool_result.answer]" not in text
    assert "explanation=tool_result.answer" not in text

    assert '"claims_validated": False' in text
    assert '"execution_path": "DETERMINISTIC_FAST_PATH"' in text


# ============================================================
# SUITE COMPLETE
# ============================================================

if __name__ == "__main__":
    print("N6.3 behavioral governance contract suite loaded.")


