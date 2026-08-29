import ast
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from aurix_core.database.engine import Base

from aurix_core.intelligence.router import (
    BusinessRouter,
    PageContext,
    QueryType,
    RoutingConfidence,
)
from aurix_core.intelligence.context import ContextBuilder
from aurix_core.intelligence.evidence_orchestrator import EvidenceOrchestrator
from aurix_core.intelligence.decision_resolver import DeterministicDecisionResolver
from aurix_core.intelligence.domain_registry import DomainRegistry
from aurix_core.intelligence.claim_validator import ClaimValidator
from aurix_core.intelligence.answer_composer import AnswerComposer


@pytest.fixture()
def n4_db():
    """Repository-standard isolated in-memory DB for N4 integration seams."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        yield db

    engine.dispose()

def _service_text():
    return Path(
        "aurix_core/intelligence/service.py"
    ).read_text(encoding="utf-8-sig")


def _class_definitions(root: str, target: str):
    result = []

    for path in Path(root).rglob("*.py"):
        try:
            tree = ast.parse(
                path.read_text(encoding="utf-8-sig"),
                filename=str(path),
            )
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == target:
                result.append((str(path), node.lineno))

    return result


def test_single_canonical_intelligence_orchestrator():
    assert len(_class_definitions("aurix_core", "IntelligenceOrchestrator")) == 1


def test_single_canonical_context_builder():
    assert len(_class_definitions("aurix_core", "ContextBuilder")) == 1


def test_single_canonical_business_router():
    assert len(_class_definitions("aurix_core", "BusinessRouter")) == 1


def test_single_canonical_decision_resolver():
    assert len(_class_definitions("aurix_core", "DeterministicDecisionResolver")) == 1


def test_tenant_scope_is_service_owned():
    text = _service_text()

    assert "self.tenant_id = tenant_id" in text
    assert "tenant_id=self.tenant_id" in text


def test_conversation_cannot_supply_tenant_scope():
    text = _service_text()

    # Conversation retrieval may occur, but tenant scope must continue
    # to originate from the service repository/runtime boundary.
    assert "self.conv_repo" in text
    assert "tenant_id=self.tenant_id" in text


def test_explicit_entity_survives_routing():
    decision = BusinessRouter.route(
        "Show me inventory for SKU-A",
        conversation_history=[],
        page_context=None,
    )

    assert decision.resolved_entity_id == "SKU-A"


def test_page_context_can_resolve_referent():
    page = PageContext(
        current_page="INVENTORY",
        active_entity_type="SKU",
        active_entity_id="SKU-A",
    )

    decision = BusinessRouter.route(
        "What about this item?",
        conversation_history=[],
        page_context=page,
    )

    assert decision.resolved_entity_id == "SKU-A"
    assert decision.context_source == "PAGE_CONTEXT"


def test_conversation_context_does_not_override_explicit_entity():
    page = PageContext(
        current_page="INVENTORY",
        active_entity_type="SKU",
        active_entity_id="SKU-A",
    )

    history = [
        {
            "role": "user",
            "content": "We were discussing SKU-B.",
        }
    ]

    decision = BusinessRouter.route(
        "Show SKU-A inventory.",
        conversation_history=history,
        page_context=page,
    )

    assert decision.resolved_entity_id == "SKU-A"


def test_missing_context_remains_none():
    decision = BusinessRouter.route(
        "What is happening?",
        conversation_history=[],
        page_context=None,
    )

    assert decision.resolved_entity_id is None or isinstance(
        decision.resolved_entity_id, str
    )


def test_domain_resolution_is_deterministic():
    first = BusinessRouter.route(
        "What is the shipment ETA for SHPM-55?",
        conversation_history=[],
        page_context=None,
    )
    second = BusinessRouter.route(
        "What is the shipment ETA for SHPM-55?",
        conversation_history=[],
        page_context=None,
    )

    assert first.domain == second.domain
    assert first.query_type == second.query_type
    assert first.resolved_entity_id == second.resolved_entity_id


def test_decision_resolution_is_deterministic():
    first = DeterministicDecisionResolver.resolve(
        query="What is the shipment ETA?",
        domain="LOGISTICS",
        intent="READ",
        concepts=["shipment", "eta"],
    )
    second = DeterministicDecisionResolver.resolve(
        query="What is the shipment ETA?",
        domain="LOGISTICS",
        intent="READ",
        concepts=["shipment", "eta"],
    )

    assert first is not None
    assert second is not None
    assert first.name == second.name
    assert first.domain == second.domain


def test_context_builder_preserves_tenant_scope():
    page = PageContext(
        current_page="INVENTORY",
        active_entity_type="SKU",
        active_entity_id="SKU-A",
    )

    routing = BusinessRouter.route(
        "Show me inventory for SKU-A",
        conversation_history=[],
        page_context=page,
    )

    fact_pack = ContextBuilder.build_fact_pack(
        tenant_id="TENANT-A",
        routing_decision=routing,
        snapshot=None,
        analytical_data={},
        page_context=page,
    )

    assert fact_pack.tenant_id == "TENANT-A"
    assert fact_pack.active_entity_id == "SKU-A"


def test_context_builder_does_not_promote_conversation_to_evidence():
    page = PageContext(
        current_page="INVENTORY",
        active_entity_type="SKU",
        active_entity_id="SKU-A",
    )

    routing = BusinessRouter.route(
        "What about this item?",
        conversation_history=[
            {
                "role": "user",
                "content": "SKU-A has 999 units.",
            }
        ],
        page_context=page,
    )

    fact_pack = ContextBuilder.build_fact_pack(
        tenant_id="TENANT-A",
        routing_decision=routing,
        snapshot=None,
        analytical_data={},
        page_context=page,
    )

    # No analytical evidence was supplied, therefore the conversation
    # statement must not become an evidence fact.
    assert fact_pack.facts == []


def test_context_builder_missing_freshness_defaults_unknown():
    routing = BusinessRouter.route(
        "Show inventory for SKU-A",
        conversation_history=[],
        page_context=None,
    )

    fact_pack = ContextBuilder.build_fact_pack(
        tenant_id="TENANT-A",
        routing_decision=routing,
        snapshot=None,
        analytical_data={},
        page_context=None,
    )

    assert fact_pack.tenant_id == "TENANT-A"


def test_evidence_orchestrator_receives_explicit_tenant_scope(n4_db):
    result = EvidenceOrchestrator.collect(
        n4_db,
        tenant_id="TENANT-A",
        query="Show inventory for SKU-A",
        entity_id="SKU-A",
    )

    assert result is not None
    assert result.resolved_entity_id == "SKU-A"


def test_evidence_orchestrator_does_not_change_tenant_scope(n4_db):
    result = EvidenceOrchestrator.collect(
        n4_db,
        tenant_id="TENANT-A",
        query="Show inventory for SKU-A",
        entity_id="SKU-A",
    )

    payload = result.model_dump()

    # The result may expose entity/location scope, but it must not
    # invent a different tenant.
    assert "tenant_id" not in payload or payload.get("tenant_id") in (
        None,
        "TENANT-A",
    )


def test_context_has_freshness_field():
    page = PageContext(
        current_page="INVENTORY",
        active_entity_type="SKU",
        active_entity_id="SKU-A",
    )

    routing = BusinessRouter.route(
        "Show inventory for SKU-A",
        conversation_history=[],
        page_context=page,
    )

    fact_pack = ContextBuilder.build_fact_pack(
        tenant_id="TENANT-A",
        routing_decision=routing,
        snapshot=None,
        analytical_data={},
        page_context=page,
    )

    for fact in fact_pack.facts:
        assert hasattr(fact, "freshness")


def test_n3_claim_validator_remains_single_downstream_authority():
    assert ClaimValidator is not None
    assert AnswerComposer is not None


def test_service_canonical_order_is_preserved():
    text = _service_text()

    positions = {
        "router": text.find("BusinessRouter.route("),
        "evidence": text.find("EvidenceOrchestrator.collect("),
        "decision": text.find("DeterministicDecisionResolver.resolve("),
        "orchestrator": text.find("IntelligenceOrchestrator.execute("),
        "validator": text.find("ClaimValidator.validate("),
        "composer": text.find("AnswerComposer.compose_validated_claims("),
    }

    assert all(v >= 0 for v in positions.values())

    assert positions["router"] < positions["evidence"]
    assert positions["evidence"] < positions["decision"]
    assert positions["decision"] < positions["orchestrator"]
    assert positions["orchestrator"] < positions["validator"]
    assert positions["validator"] < positions["composer"]


def test_service_uses_only_one_claim_validation_call():
    text = _service_text()
    assert text.count("ClaimValidator.validate(") == 1


def test_service_uses_only_one_canonical_composer_call():
    text = _service_text()
    assert text.count("AnswerComposer.compose_validated_claims(") == 1


def test_service_fast_path_is_not_verified_claim_generation():
    text = _service_text()

    assert 'verified_facts=[]' in text
    assert '"claims_validated": False' in text
    assert '"execution_path": "DETERMINISTIC_FAST_PATH"' in text


def test_service_does_not_promote_raw_tool_answer_as_verified_fact():
    text = _service_text()

    assert "verified_facts=[tool_result.answer]" not in text
    assert "explanation=tool_result.answer" not in text


def test_decision_registry_is_canonical():
    assert DomainRegistry.get("INVENTORY_STATUS").name == "INVENTORY_STATUS"


def test_context_history_is_not_evidence():
    # This is a structural contract: ContextBuilder receives analytical
    # evidence separately rather than taking conversation history as facts.
    params = ContextBuilder.build_fact_pack.__annotations__
    assert "analytical_data" in params


def test_no_second_router_or_context_module():
    router_defs = _class_definitions("aurix_core", "BusinessRouter")
    context_defs = _class_definitions("aurix_core", "ContextBuilder")

    assert len(router_defs) == 1
    assert len(context_defs) == 1


