"""
AURIX Scenario Simulation, Executive Intelligence & Outcome Learning — Contracts & Schemas
Phase 28 Core Implementation.
Defines authoritative schemas for Scenarios, Assumptions, Baselines, Counterfactuals,
Monte Carlo Distributions, Executive Briefs, Outcome Records, and Calibration DTOs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ScenarioType(str, Enum):
    """Scenario simulation classifications."""
    DEMAND_SHOCK = "DEMAND_SHOCK"
    SUPPLIER_DISRUPTION = "SUPPLIER_DISRUPTION"
    LEAD_TIME_EXPANSION = "LEAD_TIME_EXPANSION"
    COST_INFLATION = "COST_INFLATION"
    PRICE_CHANGE = "PRICE_CHANGE"
    CAPACITY_REDUCTION = "CAPACITY_REDUCTION"
    WORKING_CAPITAL_STRESS = "WORKING_CAPITAL_STRESS"
    PROCESS_BOTTLENECK = "PROCESS_BOTTLENECK"


class ScenarioStatus(str, Enum):
    """Lifecycle status of a scenario."""
    DRAFT = "DRAFT"
    READY = "READY"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# --- Scenario Definition & Assumption Schemas ---
class ScenarioAssumption(BaseModel):
    """Explicit parameter perturbation assumption."""
    parameter_name: str
    baseline_value: float
    perturbed_value: float
    unit: str = "PERCENT"
    justification: str = ""


class ScenarioDefinition(BaseModel):
    """Authoritative scenario definition contract."""
    model_config = ConfigDict(extra="allow")

    scenario_id: str = Field(default_factory=lambda: f"SCN-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str
    scenario_type: ScenarioType
    name: str
    description: str = ""
    baseline_reference: str = "CURRENT_OPERATIONAL_BASELINE"
    assumptions: List[ScenarioAssumption] = Field(default_factory=list)
    time_horizon_days: int = 90
    status: ScenarioStatus = ScenarioStatus.READY
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Simulation Output & Comparison Schemas ---
class ScenarioResult(BaseModel):
    """Deterministic simulation output metrics."""
    result_id: str = Field(default_factory=lambda: f"RES-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str
    scenario_id: str
    simulated_revenue_usd: float = 0.0
    simulated_margin_usd: float = 0.0
    simulated_working_capital_usd: float = 0.0
    simulated_risk_exposure_usd: float = 0.0
    expected_value_usd: float = 0.0
    confidence_score: float = 0.90
    p50_usd: float = 0.0
    p80_usd: float = 0.0
    p90_usd: float = 0.0
    tradeoffs_summary: Dict[str, Any] = Field(default_factory=dict)
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ScenarioComparisonReport(BaseModel):
    """Comparative tradeoff report of multiple candidate scenarios vs Do-Nothing."""
    tenant_id: str
    baseline_scenario_id: str
    comparison_matrix: List[Dict[str, Any]]
    recommended_scenario_id: str
    tradeoffs_explanation: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Counterfactual Business Twin Schemas ---
class CounterfactualRecord(BaseModel):
    """Modeled historical counterfactual reconstruction."""
    counterfactual_id: str = Field(default_factory=lambda: f"CTF-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str
    entity_type: str
    entity_id: str
    historical_event_ref: str
    methodology: str = "CONTROLLED_HISTORICAL_REPLAY"
    observed_outcome_usd: float
    counterfactual_outcome_usd: float
    net_impact_usd: float
    limitations: List[str] = Field(default_factory=list)
    confidence_score: float = 0.92
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Executive Eight-Question Brief Schema ---
class ExecutiveEightQuestionBrief(BaseModel):
    """Authoritative executive brief answering the 8 core operational questions."""
    tenant_id: str
    q1_what_happened: str
    q2_why_did_it_happen: str
    q3_what_will_happen: str
    q4_what_could_happen: str
    q5_what_should_we_do: str
    q6_what_if_we_do_nothing: str
    q7_what_is_the_expected_value: str
    q8_did_the_action_work: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Outcome Tracking & Calibration Schemas ---
class OutcomeTrackingRecord(BaseModel):
    """Post-execution prediction vs actual realization tracking record."""
    tracking_id: str = Field(default_factory=lambda: f"TRK-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str
    decision_id: str
    action_id: str
    predicted_value_usd: float
    actual_value_usd: float
    prediction_error_usd: float = 0.0
    value_realization_pct: float = 0.0
    error_cause: str = "NONE"
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConfidenceCalibrationRecord(BaseModel):
    """Historical confidence calibration record."""
    calibration_id: str = Field(default_factory=lambda: f"CAL-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str
    domain: str
    predicted_confidence_avg: float
    actual_accuracy_avg: float
    calibration_error: float
    calibrated_weight_factor: float
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Master Scenario Summary ---
class ScenarioSummaryReport(BaseModel):
    """Master executive scenario and simulation operating summary."""
    tenant_id: str
    period_key: str
    total_scenarios_defined: int
    active_simulations_count: int
    total_expected_value_pipeline_usd: float
    average_prediction_accuracy_pct: float
    active_counterfactual_twins_count: int
    overall_simulation_readiness_pct: float
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
