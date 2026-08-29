"""SQLAlchemy database models for Phase 29 Governed Autonomous Agents, Skills & Value Network."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin


class AgentRuntimeModel(Base, TenantMixin):
    """Authoritative persistent record of registered enterprise agents."""

    __tablename__ = "agent_runtimes"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    agent_type = Column(String(64), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    version = Column(String(32), nullable=False, default="v1.0")
    status = Column(String(32), nullable=False, default="ACTIVE", index=True)
    owner = Column(String(128), nullable=False)
    capabilities_json = Column(JSON, nullable=True)
    risk_classification = Column(String(32), nullable=False, default="MEDIUM")
    max_steps = Column(Integer, nullable=False, default=10)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SkillRegistryModel(Base):
    """Global governed skill registry records."""

    __tablename__ = "skill_registries"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False, index=True)
    version = Column(String(32), nullable=False, default="v1.0")
    description = Column(Text, nullable=False)
    risk_level = Column(String(32), nullable=False, default="MEDIUM")
    requires_approval = Column(Boolean, nullable=False, default=False)
    side_effect = Column(String(32), nullable=False, default="REVERSIBLE")


class ToolRegistryModel(Base):
    """Global governed tool and connector registry records."""

    __tablename__ = "tool_registries"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False, index=True)
    version = Column(String(32), nullable=False, default="v1.0")
    endpoint_ref = Column(String(255), nullable=False)
    risk_level = Column(String(32), nullable=False, default="MEDIUM")
    rate_limit_per_min = Column(Integer, nullable=False, default=60)
    circuit_state = Column(String(32), nullable=False, default="CLOSED")
    failure_count = Column(Integer, nullable=False, default=0)


class AgentExecutionJournalModel(Base, TenantMixin):
    """Immutable audit journal record of agent executions."""

    __tablename__ = "agent_execution_journals"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    agent_id = Column(String(64), nullable=False, index=True)
    plan_id = Column(String(64), nullable=False, index=True)
    idempotency_key = Column(String(128), nullable=False, unique=True, index=True)
    state = Column(String(32), nullable=False, default="PLANNED", index=True)
    risk_level = Column(String(32), nullable=False, default="MEDIUM")
    inputs_json = Column(JSON, nullable=True)
    outputs_json = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    is_dry_run = Column(Boolean, nullable=False, default=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)


class ValueNetworkRecordModel(Base, TenantMixin):
    """Authoritative persistent record of financial value realization attributed to agent executions."""

    __tablename__ = "value_network_records"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    execution_id = Column(String(64), nullable=False, index=True)
    decision_ref = Column(String(64), nullable=True, index=True)
    value_attribution_type = Column(String(64), nullable=False, index=True)
    realized_value = Column(Float, nullable=False, default=0.0, index=True)
    currency = Column(String(16), nullable=False, default="USD")
    base_currency = Column(String(16), nullable=False, default="USD")
    verified = Column(Boolean, nullable=False, default=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
