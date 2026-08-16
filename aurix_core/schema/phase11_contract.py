"""Output contract schema for Phase 9 Executive & AI Intelligence."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from aurix_core.schema.phase5_contract import MissingInput, TrackedValue


class SignalSeverity(str, Enum):
    """Severity classification for structured business signals."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    INFO = "INFO"


class SignalDomain(str, Enum):
    """Functional domain producing the business signal."""

    DEMAND = "DEMAND"
    INVENTORY = "INVENTORY"
    SUPPLY = "SUPPLY"
    LOGISTICS = "LOGISTICS"
    NETWORK = "NETWORK"
    DECISION = "DECISION"
    ECONOMICS = "ECONOMICS"


class EvidenceType(str, Enum):
    """Epistemological evidence categorization for Zero-Fabrication integrity."""

    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"
    MODEL_OUTPUT = "MODEL_OUTPUT"
    RECOMMENDATION = "RECOMMENDATION"
    UNAVAILABLE = "UNAVAILABLE"


class BusinessSignal(BaseModel):
    """Structured business signal extracted from Phase 1-8 outputs."""

    signal_id: str
    signal_type: str
    domain: SignalDomain
    severity: SignalSeverity
    affected_entity_id: str
    description: str
    evidence_quality: EvidenceType
    source_phase: str
    source_metrics: Dict[str, TrackedValue] = Field(default_factory=dict)
    financial_exposure: Optional[TrackedValue] = None
    provenance: Dict[str, Any] = Field(default_factory=dict)


class PrioritizedAction(BaseModel):
    """Ranked business action with multi-dimensional prioritization scoring."""

    action_id: str
    rank: int
    title: str
    description: str
    domain: SignalDomain
    priority_score: float
    financial_impact: Optional[TrackedValue] = None
    operational_impact: Optional[TrackedValue] = None
    risk_level: str
    underlying_signal_ids: List[str] = Field(default_factory=list)
    recommended_decision_id: Optional[str] = None


class EvidenceChainStep(BaseModel):
    """Single link in a multi-phase evidence chain."""

    step_number: int
    phase: str
    entity_id: str
    metric_name: str
    metric_value: TrackedValue
    relationship_type: str
    explanation: str


class EvidenceChain(BaseModel):
    """Connected multi-phase root-cause or evidentiary chain."""

    chain_id: str
    title: str
    primary_signal_id: str
    steps: List[EvidenceChainStep] = Field(default_factory=list)
    summary: str


class ExecutiveSummarySection(BaseModel):
    """Structured section within an executive brief."""

    section_title: str
    key_takeaways: List[str] = Field(default_factory=list)
    detailed_narrative: str


class ExecutiveSummary(BaseModel):
    """Structured, machine-readable executive brief generated from facts."""

    headline: str
    overall_health_status: str
    what_changed: ExecutiveSummarySection
    top_risks: ExecutiveSummarySection
    top_opportunities: ExecutiveSummarySection
    recommended_actions: ExecutiveSummarySection
    financial_impact_summary: ExecutiveSummarySection
    operational_impact_summary: ExecutiveSummarySection
    data_limitations: ExecutiveSummarySection


class AIInterpretation(BaseModel):
    """Optional grounded AI narrative with strict source attribution and validation status."""

    is_generated: bool = False
    model_info: Optional[str] = None
    grounded_narrative: Optional[str] = None
    source_attribution_ids: List[str] = Field(default_factory=list)
    validation_status: str = "UNVALIDATED"
    fallback_used: bool = False


class Phase11InputContract(BaseModel):
    """System-level output contract for Phase 9 Executive & AI Intelligence."""

    status: str
    missing_inputs: List[MissingInput] = Field(default_factory=list)
    signals: List[BusinessSignal] = Field(default_factory=list)
    prioritized_actions: List[PrioritizedAction] = Field(default_factory=list)
    evidence_chains: List[EvidenceChain] = Field(default_factory=list)
    executive_summary: Optional[ExecutiveSummary] = None
    ai_interpretation: Optional[AIInterpretation] = None
    limitations: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)