"""SQLAlchemy ORM models for Phase 8 Financial Intelligence and Scenario Simulation persistence."""

from datetime import datetime
from sqlalchemy import Column, DateTime, Index, String, Text
from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin


class FinancialIntelligenceRun(Base, TenantMixin):
    """Tracks execution runs of the Financial Intelligence and Scenario Simulation engine."""

    __tablename__ = "financial_intelligence_runs"

    id = Column(String(64), primary_key=True, index=True)
    dataset_hash = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="EXECUTING")  # EXECUTING, COMPLETED, FAILED
    configuration = Column(Text, nullable=True)  # JSON-serialized configuration
    provenance = Column(Text, nullable=True)  # JSON-serialized provenance & metrics
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_fin_run_tenant_hash", "tenant_id", "dataset_hash"),
    )


class FinancialBaselineSnapshot(Base, TenantMixin):
    """Persists the immutable current financial baseline evaluated during a run."""

    __tablename__ = "financial_baseline_snapshots"

    id = Column(String(64), primary_key=True, index=True)
    run_id = Column(String(64), nullable=False, index=True)
    currency = Column(String(16), default="USD", nullable=False)
    baseline_metrics_json = Column(Text, nullable=True)  # JSON-serialized baseline metrics dictionary
    value_state = Column(String(32), nullable=False, default="DERIVED")

    __table_args__ = (
        Index("idx_fin_baseline_tenant_run", "tenant_id", "run_id"),
    )


class ScenarioRun(Base, TenantMixin):
    """Persists what-if scenario simulations executed relative to the baseline."""

    __tablename__ = "scenario_runs"

    id = Column(String(64), primary_key=True, index=True)
    run_id = Column(String(64), nullable=False, index=True)
    scenario_id = Column(String(128), nullable=False, index=True)
    scenario_type = Column(String(64), nullable=False)
    scenario_description = Column(Text, nullable=True)
    parameters_json = Column(Text, nullable=True)  # JSON-serialized scenario overrides/parameters
    status = Column(String(32), nullable=False, default="COMPLETED")

    __table_args__ = (
        Index("idx_scenario_tenant_run", "tenant_id", "run_id"),
    )


class ScenarioMetricSnapshot(Base, TenantMixin):
    """Persists scenario financial outputs and deltas compared against the baseline."""

    __tablename__ = "scenario_metric_snapshots"

    id = Column(String(64), primary_key=True, index=True)
    scenario_run_id = Column(String(64), nullable=False, index=True)
    currency = Column(String(16), default="USD", nullable=False)
    scenario_metrics_json = Column(Text, nullable=True)  # JSON-serialized scenario metrics
    deltas_json = Column(Text, nullable=True)  # JSON-serialized deltas vs baseline
    gate_status = Column(String(32), nullable=False, default="RECOMMENDED")

    __table_args__ = (
        Index("idx_scenario_metric_tenant_run", "tenant_id", "scenario_run_id"),
    )