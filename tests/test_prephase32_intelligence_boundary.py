from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from aurix_core.database.engine import Base
from aurix_core.database.models.supply_chain import Location, Shipment
from aurix_core.intelligence.answer_composer import AnswerComposer
from aurix_core.intelligence.claim_validator import (
    ClaimValidator,
    SpecialistClaimNormalizer,
)
from aurix_core.intelligence.domain_registry import DomainRegistry
from aurix_core.intelligence.expert_contracts import ExpertContractRegistry
from aurix_core.intelligence.expert_executor import ExpertExecutor
from aurix_core.intelligence.service import IntelligenceService


def test_registry_alignment_and_contract_denial():
    from aurix_core.intelligence.expert_registry import ExpertRegistry

    assert len(ExpertContractRegistry.CONTRACTS) == 19
    assert len(ExpertRegistry.BINDINGS) == 19
    assert ExpertContractRegistry.get("EXECUTIVE_BRIEF").execution_allowed is False

    result = ExpertExecutor.execute(
        decision="EXECUTIVE_BRIEF",
        prepared_inputs={},
        available_sources=[],
        missing_sources=[],
        tenant_id="tenant-a",
    )
    assert result.status == "BLOCKED"
    assert result.executed is False
    assert "EXECUTION_NOT_ALLOWED_BY_CONTRACT" in result.blockers


def test_shipment_eta_positive_path_and_claim_validation():
    result = ExpertExecutor.execute(
        decision="SHIPMENT_ETA",
        prepared_inputs={
            "shipment": {
                "shipment_number": "SHPM-55",
                "dispatch_date": "2026-08-26T00:00:00",
                "planned_transit_days": 4,
            },
        },
        available_sources=["shipments"],
        missing_sources=[],
        tenant_id="tenant-a",
    )
    assert result.status == "EXECUTED"
    assert result.executed is True
    assert result.result["estimated_delivery_date"] is not None
    assert result.provenance["expert_binding"]["method_name"] == "calculate_eta"

    claims = SpecialistClaimNormalizer.normalize(
        decision="SHIPMENT_ETA",
        result=result.result,
        available_sources=["shipments"],
        tenant_id="tenant-a",
    )
    validated = ClaimValidator.validate(
        decision="SHIPMENT_ETA",
        claims=claims,
        available_sources=["shipments"],
        domain="LOGISTICS",
        tenant_id="tenant-a",
    )
    assert len(validated.accepted) == 1
    assert not validated.rejected

    composed = AnswerComposer.compose_validated_claims(
        query="When will SHPM-55 arrive?",
        decision="SHIPMENT_ETA",
        claims=validated.accepted,
        confidence=1.0,
        evidence_quality="HIGH",
        tenant_id="tenant-a",
        provenance=validated.provenance,
    )
    assert composed.answer_source == "AURIX_ENGINE"
    assert "Estimated delivery date" in composed.answer


def test_required_evidence_and_field_gates():
    missing_source = ExpertExecutor.execute(
        decision="SHIPMENT_ETA",
        prepared_inputs={},
        available_sources=[],
        missing_sources=["shipments"],
        tenant_id="tenant-a",
    )
    assert missing_source.status == "BLOCKED"
    assert not missing_source.executed
    assert "shipments" in missing_source.blockers

    missing_field = ExpertExecutor.execute(
        decision="SHIPMENT_ETA",
        prepared_inputs={},
        available_sources=["shipments"],
        missing_sources=[],
        tenant_id="tenant-a",
    )
    assert missing_field.status == "BLOCKED"
    assert not missing_field.executed
    assert "shipment" in missing_field.missing_fields


def test_live_service_uses_unified_specialist_boundary_safely():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all(
            [
                Location(
                    id="LOC-O",
                    tenant_id="tenant-a",
                    location_name="Origin",
                ),
                Location(
                    id="LOC-D",
                    tenant_id="tenant-a",
                    location_name="Destination",
                ),
            ]
        )
        db.flush()
        db.add(
            Shipment(
                id="SHPM-ID-55",
                tenant_id="tenant-a",
                shipment_number="SHPM-55",
                origin_location_id="LOC-O",
                destination_location_id="LOC-D",
                carrier="Carrier X",
                status="IN_TRANSIT",
                shipped_date=datetime(2026, 8, 26, tzinfo=timezone.utc),
                estimated_arrival_date=datetime(
                    2026, 8, 30, tzinfo=timezone.utc
                ),
            )
        )
        db.commit()

        response = IntelligenceService(
            db,
            "tenant-a",
        ).ask_ai("When will SHPM-55 arrive?")

        assert response.answer_source == "AURIX_ENGINE"
        assert response.provider_used == "AURIX_ENGINE"
        assert response.model_used == "deterministic-intelligence-orchestrator"
        assert response.provenance["canonical_decision"] == "SHIPMENT_ETA"
        assert response.provenance["composer"] == "AnswerComposer"
        assert response.provenance["claims_validated"] is True
        assert response.explanation

        # The canonical Shipment table does not expose dispatch/transit
        # evidence in the form required by the ETA engine. The safe result is
        # an explicit inability to establish ETA, not a fabricated date.
        assert response.verified_facts == []
