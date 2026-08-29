from aurix_core.intelligence.answer_composer import AnswerComposer
from aurix_core.intelligence.claim import DeterministicClaim
from aurix_core.intelligence.claim_validator import ClaimValidationResult


def _claim(
    statement: str,
    *,
    freshness_state: str = "LIVE",
    tenant_id: str = "TENANT-A",
    location_id: str = "DC-001",
):
    return DeterministicClaim(
        statement=statement,
        category="VERIFIED",
        confidence=1.0,
        evidence_refs=["inventory_position.on_hand"],
        supported=True,
        allowable_in_answer=True,
        freshness_state=freshness_state,
        freshness_age_hours=1.0,
        observation_timestamp="2026-08-27T10:00:00+00:00",
        source="WMS",
        tenant_id=tenant_id,
        location_id=location_id,
        provenance={
            "source_record_id": "SRC-001",
            "ingestion_run_id": "RUN-001",
            "authority": "WMS",
            "contradiction_id": "CONFLICT-001",
        },
    )


def test_composer_accepts_validated_claims():
    claim = _claim("SKU-A has 100 units.")
    result = ClaimValidationResult(
        claims=[claim],
        accepted=[claim],
        rejected=[],
        limitations=[],
        provenance={
            "validator": "ClaimValidator",
            "tenant_id": "TENANT-A",
        },
    )

    composed = AnswerComposer.compose_validated_claims(
        query="What is inventory?",
        decision="INVENTORY_STATUS",
        validation_result=result,
        tenant_id="TENANT-A",
    )

    assert "SKU-A has 100 units." in composed.verified_facts
    assert composed.provenance["claims_validated"] is True


def test_composer_excludes_rejected_claims():
    accepted = _claim("Accepted claim.")
    rejected = _claim("Rejected claim.")

    result = ClaimValidationResult(
        claims=[accepted, rejected],
        accepted=[accepted],
        rejected=[rejected],
        limitations=["STALE_DATA"],
        provenance={"validator": "ClaimValidator"},
    )

    composed = AnswerComposer.compose_validated_claims(
        query="Test",
        decision="INVENTORY_STATUS",
        validation_result=result,
        tenant_id="TENANT-A",
    )

    assert "Accepted claim." in composed.verified_facts
    assert "Rejected claim." not in composed.verified_facts
    assert "Rejected claim." not in composed.answer


def test_composer_preserves_freshness_metadata():
    claim = _claim(
        "Recent claim.",
        freshness_state="RECENT",
    )

    result = ClaimValidationResult(
        claims=[claim],
        accepted=[claim],
        rejected=[],
        limitations=["RECOMMENDATION_FRESHNESS_DISCLOSURE"],
        provenance={"validator": "ClaimValidator"},
    )

    composed = AnswerComposer.compose_validated_claims(
        query="Test",
        decision="INVENTORY_STATUS",
        validation_result=result,
        tenant_id="TENANT-A",
    )

    assert composed.provenance["freshness_state"] == "RECENT"
    assert composed.provenance["freshness_age_hours"] == 1.0
    assert "RECOMMENDATION_FRESHNESS_DISCLOSURE" in composed.limitations


def test_composer_preserves_scope_and_lineage():
    claim = _claim(
        "Scoped claim.",
        tenant_id="TENANT-A",
        location_id="DC-001",
    )

    result = ClaimValidationResult(
        claims=[claim],
        accepted=[claim],
        rejected=[],
        limitations=[],
        provenance={
            "validator": "ClaimValidator",
            "tenant_id": "TENANT-A",
        },
    )

    composed = AnswerComposer.compose_validated_claims(
        query="Test",
        decision="INVENTORY_STATUS",
        validation_result=result,
        tenant_id="TENANT-A",
    )

    assert composed.provenance["tenant_id"] == "TENANT-A"
    assert composed.provenance["location_id"] == "DC-001"
    assert composed.provenance["source"] == "WMS"
    assert composed.provenance["source_record_id"] == "SRC-001"
    assert composed.provenance["ingestion_run_id"] == "RUN-001"


def test_composer_preserves_authority_and_contradiction_metadata():
    claim = _claim("Contradictory claim.")

    result = ClaimValidationResult(
        claims=[claim],
        accepted=[claim],
        rejected=[],
        limitations=["CONTRADICTION_PRESENT"],
        provenance={
            "validator": "ClaimValidator",
            "authority": "WMS",
            "contradiction_id": "CONFLICT-001",
        },
    )

    composed = AnswerComposer.compose_validated_claims(
        query="Test",
        decision="INVENTORY_STATUS",
        validation_result=result,
        tenant_id="TENANT-A",
    )

    assert composed.provenance["authority"] == "WMS"
    assert composed.provenance["contradiction_id"] == "CONFLICT-001"
    assert "CONTRADICTION_PRESENT" in composed.limitations
