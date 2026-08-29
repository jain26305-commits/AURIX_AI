"""SQLAlchemy database models for Phase 28 Scenario Simulation & Executive Intelligence."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin


class ScenarioModel(Base, TenantMixin):
    """Authoritative persistent record of a scenario definition."""

    __tablename__ = "scenarios"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    scenario_type = Column(String(64), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    baseline_reference = Column(String(128), nullable=False, default="CURRENT_OPERATIONAL_BASELINE")
    time_horizon_days = Column(Integer, nullable=False, default=90)
    status = Column(String(32), nullable=False, default="READY", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ScenarioAssumptionModel(Base, TenantMixin):
    """Explicit perturbed parameter assumptions associated with a scenario."""

    __tablename__ = "scenario_assumptions"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    scenario_id = Column(String(64), ForeignKey("scenarios.id"), nullable=False, index=True)
    parameter_name = Column(String(128), nullable=False)
    baseline_value = Column(Float, nullable=False)
    perturbed_value = Column(Float, nullable=False)
    unit = Column(String(32), nullable=False, default="PERCENT")
    justification = Column(Text, nullable=True)


class ScenarioResultModel(Base, TenantMixin):
    """Authoritative persistent record of simulation execution output metrics."""

    __tablename__ = "scenario_results"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    scenario_id = Column(String(64), ForeignKey("scenarios.id"), nullable=False, index=True)
    simulated_revenue_usd = Column(Float, nullable=False, default=0.0)
    simulated_margin_usd = Column(Float, nullable=False, default=0.0)
    simulated_working_capital_usd = Column(Float, nullable=False, default=0.0)
    simulated_risk_exposure_usd = Column(Float, nullable=False, default=0.0)
    expected_value_usd = Column(Float, nullable=False, default=0.0, index=True)
    confidence_score = Column(Float, nullable=False, default=0.90)
    p50_usd = Column(Float, nullable=False, default=0.0)
    p80_usd = Column(Float, nullable=False, default=0.0)
    p90_usd = Column(Float, nullable=False, default=0.0)
    tradeoffs_json = Column(JSON, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CounterfactualRecordModel(Base, TenantMixin):
    """Authoritative persistent record of modeled historical counterfactual reconstructions."""

    __tablename__ = "counterfactual_records"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(128), nullable=False, index=True)
    historical_event_ref = Column(String(128), nullable=False, index=True)
    methodology = Column(String(128), nullable=False)
    observed_outcome_usd = Column(Float, nullable=False)
    counterfactual_outcome_usd = Column(Float, nullable=False)
    net_impact_usd = Column(Float, nullable=False, index=True)
    limitations_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class OutcomeTrackingModel(Base, TenantMixin):
    """Post-execution tracking record comparing predicted Expected Value against realized business outcomes."""

    __tablename__ = "outcome_tracking"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    decision_id = Column(String(64), nullable=False, index=True)
    action_id = Column(String(64), nullable=False, index=True)
    predicted_value_usd = Column(Float, nullable=False)
    actual_value_usd = Column(Float, nullable=False)
    prediction_error_usd = Column(Float, nullable=False, default=0.0)
    value_realization_pct = Column(Float, nullable=False, default=0.0)
    error_cause = Column(String(128), nullable=False, default="NONE")
    observed_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ConfidenceCalibrationModel(Base, TenantMixin):
    """Historical confidence calibration audit records."""

    __tablename__ = "confidence_calibration"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    domain = Column(String(64), nullable=False, index=True)
    predicted_confidence_avg = Column(Float, nullable=False)
    actual_accuracy_avg = Column(Float, nullable=False)
    calibration_error = Column(Float, nullable=False)
    calibrated_weight_factor = Column(Float, nullable=False, default=1.0)
    evaluated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
