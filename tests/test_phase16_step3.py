"""Targeted Step 3 regression tests for governed Phase 16 orchestration."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from aurix_core.database.engine import Base
from aurix_core.phase16.agent_contracts import AgentRole, ControlTowerQuery
from aurix_core.phase16.agent_orchestrator import Phase16Supervisor
from aurix_core.phase16.impact import ImpactPropagationService
from aurix_core.observability.metrics import MetricsRegistry


def build_session() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def test_supervisor_uses_deterministic_path_when_tool_can_answer() -> None:
    session_factory = build_session()
    with session_factory() as db:
        result = Phase16Supervisor.run(
            db=db,
            tenant_id="default_tenant",
            request=ControlTowerQuery(
                query="What is the current inventory for SKU-100?",
                entity_id="SKU-100",
            ),
        )
        assert result.success is True
        assert result.agent == AgentRole.SUPERVISOR
        assert result.answer_source in {"AURIX_ENGINE", "AI_ESCALATION"}


def test_agent_contract_defaults_to_recommend() -> None:
    request = ControlTowerQuery(query="Explain supplier risk.")
    assert request.autonomy_level.value == 2


def test_supplier_delay_impact_does_not_invent_revenue() -> None:
    session_factory = build_session()
    with session_factory() as db:
        impact = ImpactPropagationService.supplier_delay(
            db=db,
            tenant_id="default_tenant",
            supplier_id="SUP-A",
            delay_days=10,
        )
        assert "revenue_at_risk" not in impact
        assert "limitations" in impact


def test_supervisor_specialist_selection() -> None:
    specialists = Phase16Supervisor._specialists_for_query(
        "Supplier delay threatens production and customer fulfillment"
    )
    assert AgentRole.SUPPLIER in specialists
    assert AgentRole.MANUFACTURING in specialists
    assert AgentRole.FULFILLMENT in specialists


def test_supervisor_records_agent_and_tool_telemetry() -> None:
    MetricsRegistry.reset()
    session_factory = build_session()
    with session_factory() as db:
        Phase16Supervisor.run(
            db=db,
            tenant_id="default_tenant",
            request=ControlTowerQuery(
                query="What is the current inventory for SKU-100?",
                entity_id="SKU-100",
            ),
        )
    snapshot = MetricsRegistry.get_snapshot()
    assert snapshot.agent_runs_total == 1
    assert snapshot.tool_calls_total == 1
