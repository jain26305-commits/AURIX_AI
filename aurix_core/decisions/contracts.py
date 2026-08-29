"""
AURIX Deterministic Decision Engine 2.0 — Contracts & Schemas
Phase 27 Core Implementation.
Defines authoritative schemas for Decisions, Candidates, Constraints, Expected Value,
Universal Decision Cards, Model Registry, Policies, and Sensitivity DTOs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DecisionDomain(str, Enum):
    """Enterprise decision domain classifications."""
    PROCUREMENT_SUPPLIER = "PROCUREMENT_SUPPLIER"
    INVENTORY_REPLENISHMENT = "INVENTORY_REPLENISHMENT"
    COMMERCIAL_PRICING = "COMMERCIAL_PRICING"
    MANUFACTURING_PRODUCTION = "MANUFACTURING_PRODUCTION"
    WORKING_CAPITAL_FINANCE = "WORKING_CAPITAL_FINANCE"
    PROCESS_REMEDIATION = "PROCESS_REMEDIATION"
    RISK_MITIGATION = "RISK_MITIGATION"


class DecisionState(str, Enum):
    """Lifecycle state of a decision record."""
    PROPOSED = "PROPOSED"
    EVALUATING = "EVALUATING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    OVERRIDDEN = "OVERRIDDEN"


class ModelFitnessRating(str, Enum):
    """Evaluation of underlying model/solver appropriateness."""
    HIGH = "HIGH"
    PARTIAL = "PARTIAL"
    LOW = "LOW"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class ConstraintStatus(str, Enum):
    """Constraint evaluation outcome."""
    SATISFIED = "SATISFIED"
    VIOLATED = "VIOLATED"
    UNKNOWN = "UNKNOWN"
    RELAXED = "RELAXED"


# --- Decision Candidate & Alternative Schemas ---
class DecisionCandidate(BaseModel):
    """A distinct feasible actionable alternative under evaluation."""
    model_config = ConfigDict(extra="allow")

    candidate_id: str = Field(default_factory=lambda: f"CND-{uuid.uuid4().hex[:8].upper()}")
    action_code: str
    action_name: str
    description: str = ""
    benefit_usd: float = 0.0
    cost_usd: float = 0.0
    risk_penalty_usd: float = 0.0
    expected_value_usd: float = 0.0
    utility_score: float = 0.0
    is_recommended: bool = False
    constraints_satisfied: Dict[str, bool] = Field(default_factory=dict)
    operational_impact: Dict[str, Any] = Field(default_factory=dict)


# --- Universal Decision Card Contract ---
class UniversalDecisionCard(BaseModel):
    """Standardized machine-readable and UI contract for all authoritative recommendations."""
    model_config = ConfigDict(extra="allow")

    decision_id: str = Field(default_factory=lambda: f"DEC-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str
    decision_domain: DecisionDomain
    decision_type: str
    entity_type: str
    entity_id: str
    title: str
    why_summary: str
    recommended_action: str
    decision_state: DecisionState = DecisionState.PROPOSED
    expected_value_usd: float = 0.0
    downside_risk_usd: float = 0.0
    confidence_score: float = Field(ge=0.0, le=1.0)
    financial_impact_summary: str
    operational_impact_summary: str
    alternatives: List[DecisionCandidate] = Field(default_factory=list)
    constraints_evaluated: Dict[str, str] = Field(default_factory=dict)
    assumptions: List[str] = Field(default_factory=list)
    model_name: str = "AURIX_DETERMINISTIC_SOLVER"
    modelVersion: str = "v2.0"
    model_fitness: ModelFitnessRating = ModelFitnessRating.HIGH
    policy_rule_id: Optional[str] = None
    approval_required: bool = False
    required_approver_role: Optional[str] = None
    is_reversible: bool = True
    evidence: Dict[str, Any] = Field(default_factory=dict)
    provenance_trace: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_to: Optional[datetime] = None


# --- Policy-as-Code Schemas ---
class DecisionPolicy(BaseModel):
    """Declarative Policy-as-Code governance rule."""
    policy_id: str = Field(default_factory=lambda: f"POL-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str
    policy_name: str
    decision_domain: DecisionDomain
    min_financial_threshold_usd: float = 10000.0
    requires_dual_approval: bool = False
    required_approver_role: str = "FINANCE_DIRECTOR"
    auto_executable: bool = False
    is_active: bool = True


# --- Model Registry Schemas ---
class ModelRegistryEntry(BaseModel):
    """Enterprise model and solver registry entry."""
    model_id: str = Field(default_factory=lambda: f"MDL-{uuid.uuid4().hex[:8].upper()}")
    model_name: str
    version: str
    model_type: str
    is_champion: bool = True
    status: str = "PRODUCTION"
    training_dataset_ref: Optional[str] = None
    accuracy_metrics: Dict[str, float] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ShadowEvaluationResult(BaseModel):
    """Champion vs Challenger shadow evaluation output."""
    evaluation_id: str = Field(default_factory=lambda: f"SHD-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str
    decision_id: str
    champion_model_id: str
    challenger_model_id: str
    champion_recommendation: str
    challenger_recommendation: str
    output_variance_pct: float
    champion_expected_value_usd: float
    challenger_expected_value_usd: float
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Optimization & Portfolio Schemas ---
class OptimizationRequest(BaseModel):
    """Request payload for multi-action portfolio optimization."""
    tenant_id: str
    decision_domain: DecisionDomain
    objective_type: str = "MAXIMIZE_EXPECTED_VALUE"
    budget_limit_usd: float
    candidate_actions: List[DecisionCandidate]


class OptimizationResult(BaseModel):
    """Solver output for single-decision or portfolio allocation."""
    run_id: str = Field(default_factory=lambda: f"OPT-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str
    solver_name: str
    status: str
    objective_value_usd: float
    selected_candidates: List[DecisionCandidate]
    total_cost_usd: float
    runtime_ms: float
    constraints_satisfied: bool
    relaxation_suggestions: List[str] = Field(default_factory=list)


# --- Decision Readiness & Summary Schemas ---
class DecisionReadinessReport(BaseModel):
    """Assessment of data readiness and model fitness before decisioning."""
    tenant_id: str
    procurement_readiness: str
    inventory_readiness: str
    pricing_readiness: str
    manufacturing_readiness: str
    overall_readiness_pct: float
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DecisionSummaryReport(BaseModel):
    """Master executive decision operating intelligence summary."""
    tenant_id: str
    period_key: str
    total_decisions_proposed: int
    pending_approvals_count: int
    executed_decisions_count: int
    total_pipeline_expected_value_usd: float
    total_downside_risk_mitigated_usd: float
    recommendation_acceptance_rate_pct: float
    active_champion_models_count: int
    top_decision_domain: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
