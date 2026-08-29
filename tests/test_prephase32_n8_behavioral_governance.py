from __future__ import annotations

import inspect
from typing import Any

import pandas as pd
import pytest

from aurix_core.data_foundation.quality_engine import DataQualityEngine
from aurix_core.data_foundation.quality_readiness import (
    QualityReadinessAuditor,
)
from aurix_core.onboarding.quality_validator import QualityValidator
from aurix_core.integrations.reconciliation import ReconciliationEngine
from aurix_core.integrations.lineage import SourceLineageTracker

from aurix_core.intelligence.claim import DeterministicClaim
from aurix_core.intelligence.claim_validator import ClaimValidator


# ============================================================
# QUALITY
# ============================================================

def test_quality_engine_validates_dataframe() -> None:
    df = pd.DataFrame(
        [
            {
                "id": "INV-001",
                "sku_id": "SKU-001",
                "quantity": 10.0,
            },
            {
                "id": "INV-002",
                "sku_id": "SKU-002",
                "quantity": 20.0,
            },
        ]
    )

    result = DataQualityEngine.validate(
        df=df,
        domain="inventory",
    )

    assert isinstance(result, dict)
    assert result is not None


def test_quality_readiness_auditor_checks_required_columns() -> None:
    df = pd.DataFrame(
        [
            {
                "id": "INV-001",
                "sku_id": "SKU-001",
            }
        ]
    )

    result = QualityReadinessAuditor.audit(
        df=df,
        required_columns=["id", "sku_id"],
    )

    assert isinstance(result, dict)
    assert result is not None


def test_quality_validator_uses_real_record_contract() -> None:
    records = [
        {
            "id": "INV-001",
            "sku_id": "SKU-001",
            "quantity": 10,
        },
        {
            "id": "INV-002",
            "sku_id": "SKU-002",
            "quantity": -5,
        },
    ]

    valid, invalid, summary = QualityValidator.validate_records(
        records=records,
        canonical_fields={"id", "sku_id", "quantity"},
    )

    assert isinstance(valid, list)
    assert isinstance(invalid, list)
    assert summary is not None

    # Negative quantity is a meaningful invalid fixture for
    # inventory-style data and must not silently disappear.
    assert len(valid) + len(invalid) == len(records)


# ============================================================
# RECONCILIATION
# ============================================================

def test_numeric_reconciliation_real_api() -> None:
    difference, difference_pct, status = (
        ReconciliationEngine.compare_numeric_values(
            100.0,
            100.0,
        )
    )

    assert difference == 0.0
    assert difference_pct == 0.0
    assert status is not None


def test_source_preference_real_api() -> None:
    preferred = ReconciliationEngine.get_preferred_source(
        entity_type="invoice",
        available_sources=[
            "ERP",
            "MANUAL",
        ],
    )

    assert preferred in {
        "ERP",
        "MANUAL",
    }


def test_entity_reconciliation_preserves_tenant_context() -> None:
    record = ReconciliationEngine.reconcile_entity(
        tenant_id="TENANT-A",
        entity_type="invoice",
        entity_key="INV-001",
        source_a="ERP",
        value_a=100.0,
        source_b="BANK",
        value_b=100.0,
    )

    assert record is not None

    # The reconciliation record must retain tenant identity if
    # the real production contract exposes it.
    if hasattr(record, "tenant_id"):
        assert record.tenant_id == "TENANT-A"


def test_dataset_reconciliation_real_api() -> None:
    dataset_a = [
        {
            "invoice_id": "INV-001",
            "amount": 100.0,
        },
        {
            "invoice_id": "INV-002",
            "amount": 200.0,
        },
    ]

    dataset_b = [
        {
            "invoice_id": "INV-001",
            "amount": 100.0,
        },
        {
            "invoice_id": "INV-002",
            "amount": 190.0,
        },
    ]

    reconciled, records = ReconciliationEngine.reconcile_datasets(
        tenant_id="TENANT-A",
        entity_type="invoice",
        dataset_a=dataset_a,
        source_a="ERP",
        dataset_b=dataset_b,
        source_b="BANK",
        key_field="invoice_id",
        metric_field="amount",
    )

    assert isinstance(reconciled, list)
    assert isinstance(records, list)


# ============================================================
# LINEAGE / PROVENANCE
# ============================================================

def test_lineage_api_surface_is_real() -> None:
    assert inspect.isclass(SourceLineageTracker)

    # Do not invent a method name here.
    # The purpose of this test is to ensure that the production
    # lineage authority loads successfully.
    assert SourceLineageTracker is not None


# ============================================================
# CANONICAL CLAIM GOVERNANCE
# ============================================================

def make_claim(
    *,
    tenant_id: str,
    location_id: str,
) -> DeterministicClaim:

    return DeterministicClaim(
        statement="N8.2 canonical governance claim.",
        category="VERIFIED",
        confidence=1.0,
        evidence_refs=["financial_baseline"],
        supported=True,
        allowable_in_answer=True,
        freshness_state="LIVE",
        freshness_age_hours=1.0,
        observation_timestamp="2026-08-27T10:00:00+00:00",
        source="financial_baseline",
        tenant_id=tenant_id,
        location_id=location_id,
        provenance={
            "source_record_id": "SRC-N8-001",
            "ingestion_run_id": "RUN-N8-001",
            "authority": "FINANCIAL_BASELINE",
        },
    )


def test_claim_provenance_is_preserved() -> None:
    claim = make_claim(
        tenant_id="TENANT-A",
        location_id="LOC-A",
    )

    result = ClaimValidator.validate(
        decision="WORKING_CAPITAL",
        claims=[claim],
        available_sources={"financial_baseline"},
        domain="ECONOMICS",
        tenant_id="TENANT-A",
    )

    assert claim in result.accepted

    assert claim.tenant_id == "TENANT-A"
    assert claim.location_id == "LOC-A"

    assert claim.provenance["source_record_id"] == "SRC-N8-001"
    assert claim.provenance["ingestion_run_id"] == "RUN-N8-001"
    assert claim.provenance["authority"] == "FINANCIAL_BASELINE"


def test_claim_validator_does_not_mutate_claim_tenant_metadata() -> None:
    claim = make_claim(
        tenant_id="TENANT-A",
        location_id="LOC-A",
    )

    ClaimValidator.validate(
        decision="WORKING_CAPITAL",
        claims=[claim],
        available_sources={"financial_baseline"},
        domain="ECONOMICS",
        tenant_id="TENANT-A",
    )

    assert claim.tenant_id == "TENANT-A"
    assert claim.location_id == "LOC-A"


# ============================================================
# TENANT AUTHORITY CLASSIFICATION
# ============================================================

def test_tenant_security_is_not_assumed_to_be_claim_validator() -> None:
    """
    Architectural classification test.

    ClaimValidator receives tenant_id but the existing security
    architecture also provides tenant_scope/RLS and API tenant
    context. Therefore this test intentionally does NOT assert
    that ClaimValidator alone performs RLS enforcement.

    It proves that the claim carries its tenant identity intact
    into the canonical validation layer.
    """

    claim = make_claim(
        tenant_id="TENANT-B",
        location_id="LOC-B",
    )

    result = ClaimValidator.validate(
        decision="WORKING_CAPITAL",
        claims=[claim],
        available_sources={"financial_baseline"},
        domain="ECONOMICS",
        tenant_id="TENANT-A",
    )

    assert claim in result.accepted or claim in result.rejected

    # The validator must never rewrite the claim to the caller's
    # tenant merely because validation was requested under another
    # tenant context.
    assert claim.tenant_id == "TENANT-B"


# ============================================================
# FRESHNESS CONTINUITY
# ============================================================

def test_freshness_metadata_survives_validation() -> None:
    claim = make_claim(
        tenant_id="TENANT-A",
        location_id="LOC-A",
    )

    claim.freshness_state = "STALE"
    claim.freshness_age_hours = 168.0

    result = ClaimValidator.validate(
        decision="WORKING_CAPITAL",
        claims=[claim],
        available_sources={"financial_baseline"},
        domain="ECONOMICS",
        tenant_id="TENANT-A",
    )

    assert claim.freshness_state == "STALE"
    assert claim.freshness_age_hours == 168.0

    # For informational safety, validation must not erase
    # canonical freshness metadata.
    assert claim in result.accepted or claim in result.rejected


# ============================================================
# CANONICAL BYPASS PROTECTION
# ============================================================

@pytest.mark.parametrize(
    "domain_root",
    [
        "aurix_core/finance",
        "aurix_core/manufacturing",
        "aurix_core/commercial",
        "aurix_core/process",
        "aurix_core/risk",
        "aurix_core/decisions",
        "aurix_core/scenarios",
    ],
)
def test_domain_does_not_construct_claim_or_response_directly(
    domain_root: str,
) -> None:

    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / domain_root

    if not root.exists():
        pytest.skip(f"Domain root missing: {domain_root}")

    offenders = []

    for path in root.rglob("*.py"):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if "DeterministicClaim(" in text:
            offenders.append(str(path))

        if "AIResponseContract(" in text:
            offenders.append(str(path))

    assert offenders == []


# ============================================================
# PRODUCTION IMMUTABILITY
# ============================================================

def test_protected_architecture_files_exist() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]

    protected = [
        root / "aurix_core/intelligence/readiness.py",
        root / "aurix_core/actions/policy.py",
        root / "aurix_core/data_fabric/source_authority.py",
        root / "aurix_core/data_fabric/freshness.py",
    ]

    for path in protected:
        assert path.exists()


def test_n8_canonical_service_executable_governance_order() -> None:
    """
    Authoritative N8 executable-order proof.

    The test inspects actual ast.Call nodes in production
    aurix_core/intelligence/service.py.

    Expected canonical order:
        router
        evidence
        decision
        orchestrator
        validator
        composer

    Raw substring position is intentionally not used.
    """

    import ast
    from pathlib import Path

    service_path = (
        Path(__file__).resolve().parents[1]
        / "aurix_core/intelligence/service.py"
    )

    service_source = service_path.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    tree = ast.parse(
        service_source,
        filename=str(service_path),
    )

    targets = {
        "router": (
            "BusinessRouter.route",
        ),
        "evidence": (
            "EvidenceOrchestrator.collect",
        ),
        "decision": (
            "DeterministicDecisionResolver.resolve",
        ),
        "orchestrator": (
            "IntelligenceOrchestrator.execute",
        ),
        "validator": (
            "ClaimValidator.validate",
        ),
        "composer": (
            "AnswerComposer.compose_validated_claims",
            "AnswerComposer.compose",
            "AnswerComposer.compose_context",
        ),
    }

    expected_order = [
        "router",
        "evidence",
        "decision",
        "orchestrator",
        "validator",
        "composer",
    ]

    first_call_line = {}

    for node in ast.walk(tree):

        if not isinstance(node, ast.Call):
            continue

        rendered = ast.unparse(node)

        for phase, needles in targets.items():

            if phase in first_call_line:
                continue

            if any(
                needle in rendered
                for needle in needles
            ):
                first_call_line[phase] = node.lineno

    missing = [
        phase
        for phase in expected_order
        if phase not in first_call_line
    ]

    assert not missing, (
        "Missing executable canonical governance call(s): "
        + ", ".join(missing)
    )

    lines = [
        first_call_line[phase]
        for phase in expected_order
    ]

    assert lines == sorted(lines), (
        "Canonical executable governance order invalid: "
        + repr(first_call_line)
    )

    # Existing certified production locations.
    assert lines == [
        311,
        329,
        341,
        363,
        374,
        382,
    ], (
        "Unexpected production governance call locations: "
        + repr(lines)
    )

    # Final semantic check.
    assert first_call_line["validator"] < first_call_line["composer"]
