"""SQLAlchemy database models for Phase 27 Deterministic Decision Engine 2.0."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin


class DecisionModel(Base, TenantMixin):
    """Authoritative persistent record of a generated decision and Universal Decision Card."""

    __tablename__ = "decisions"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    decision_domain = Column(String(64), nullable=False, index=True)
    decision_type = Column(String(64), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(128), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    recommended_action = Column(String(255), nullable=False)
    expected_value_usd = Column(Float, nullable=False, default=0.0)
    downside_risk_usd = Column(Float, nullable=False, default=0.0)
    confidence_score = Column(Float, nullable=False, default=0.9)
    model_id = Column(String(64), nullable=False, default="AURIX_DETERMINISTIC_SOLVER")
    model_version = Column(String(32), nullable=False, default="v2.0")
    status = Column(String(32), nullable=False, default="PROPOSED", index=True)
    approval_status = Column(String(32), nullable=False, default="PENDING", index=True)
    evidence_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_to = Column(DateTime, nullable=True)


class DecisionCandidateModel(Base, TenantMixin):
    """Evaluated candidate alternatives belonging to a decision record."""

    __tablename__ = "decision_candidates"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    decision_id = Column(String(64), ForeignKey("decisions.id"), nullable=False, index=True)
    action_code = Column(String(64), nullable=False)
    action_name = Column(String(255), nullable=False)
    expected_value_usd = Column(Float, nullable=False, default=0.0)
    cost_usd = Column(Float, nullable=False, default=0.0)
    risk_penalty_usd = Column(Float, nullable=False, default=0.0)
    utility_score = Column(Float, nullable=False, default=0.0, index=True)
    is_recommended = Column(Boolean, nullable=False, default=False)
    constraints_satisfied_json = Column(JSON, nullable=True)


class DecisionPolicyModel(Base, TenantMixin):
    """Authoritative persistent record of Policy-as-Code governance rules."""

    __tablename__ = "decision_policies"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    policy_name = Column(String(128), nullable=False, index=True)
    decision_domain = Column(String(64), nullable=False, index=True)
    conditions_json = Column(JSON, nullable=True)
    required_approver_role = Column(String(64), nullable=False, default="OPERATIONS_MANAGER")
    auto_executable = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ModelRegistryModel(Base):
    """Enterprise machine learning and optimization model registry."""

    __tablename__ = "model_registry"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    model_name = Column(String(128), nullable=False, index=True)
    version = Column(String(32), nullable=False, index=True)
    model_type = Column(String(64), nullable=False, index=True)
    metrics_json = Column(JSON, nullable=True)
    status = Column(String(32), nullable=False, default="PRODUCTION")
    is_champion = Column(Boolean, nullable=False, default=True)
    training_dataset_ref = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    promoted_at = Column(DateTime, nullable=True)


class ShadowEvaluationModel(Base, TenantMixin):
    """Champion vs Challenger shadow evaluation audit logs."""

    __tablename__ = "shadow_evaluations"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    decision_id = Column(String(64), nullable=False, index=True)
    champion_model_id = Column(String(64), nullable=False)
    challenger_model_id = Column(String(64), nullable=False)
    champion_output_json = Column(JSON, nullable=True)
    challenger_output_json = Column(JSON, nullable=True)
    variance_score = Column(Float, nullable=False, default=0.0)
    evaluated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DecisionOverrideModel(Base, TenantMixin):
    """Authoritative audit record of human manager decision overrides."""

    __tablename__ = "decision_overrides"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    decision_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    user_role = Column(String(64), nullable=False)
    action_taken = Column(String(64), nullable=False)
    override_reason = Column(Text, nullable=False)
    modified_action_json = Column(JSON, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class OptimizationRunModel(Base, TenantMixin):
    """Optimization solver execution runs and results."""

    __tablename__ = "optimization_runs"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    solver_name = Column(String(128), nullable=False, index=True)
    objective_type = Column(String(64), nullable=False)
    objective_value = Column(Float, nullable=False, default=0.0)
    variables_count = Column(Integer, nullable=False, default=0)
    constraints_count = Column(Integer, nullable=False, default=0)
    runtime_ms = Column(Float, nullable=False, default=0.0)
    status = Column(String(32), nullable=False, default="OPTIMAL")
    result_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
