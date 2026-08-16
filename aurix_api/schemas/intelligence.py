"""Executive intelligence, capability discovery, signals, and snapshot schemas for Phase 10."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CapabilityItem(BaseModel):
    """Discovered capability status and readiness metrics."""
    name: str
    domain: str
    status: str
    freshness: str
    quality_score: float
    completeness_pct: float
    record_completeness_pct: float
    missing_prerequisites: List[str] = Field(default_factory=list)
    partially_populated_fields: List[str] = Field(default_factory=list)
    diagnostic_reasons: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)


class CapabilityDiscoveryResponse(BaseModel):
    """Complete portfolio capability readiness and discovery state."""
    capabilities: Dict[str, CapabilityItem] = Field(default_factory=dict)
    total_available: int
    total_partial: int
    total_unavailable: int
    overall_status: str


class BusinessSignalItem(BaseModel):
    """Detected operational or financial business signal."""
    signal_id: str
    signal_type: str
    domain: str
    severity: str
    affected_entity_id: str
    description: str
    evidence_quality: str
    financial_exposure: Optional[float] = None
    currency: Optional[str] = None


class ActionItem(BaseModel):
    """Prioritized operational executive action."""
    action_id: str
    rank: int
    title: str
    risk_level: str
    recommended_action: str
    affected_domain: str
    financial_impact_value: Optional[float] = None
    currency: Optional[str] = None


class ExecutiveSummaryResponse(BaseModel):
    """Executive narrative summary and headline metrics."""
    headline: str
    overall_health_status: str
    signals_count: int
    actions_count: int
    signals: List[BusinessSignalItem] = Field(default_factory=list)
    prioritized_actions: List[ActionItem] = Field(default_factory=list)
    active_capabilities: List[str] = Field(default_factory=list)


class IntelligenceSnapshotResponse(BaseModel):
    """Complete operational snapshot across all active analytical domains."""
    snapshot_id: str
    generated_at: str
    total_skus: Optional[int] = None
    high_risk_skus_count: int = 0
    supplier_risks_count: int = 0
    delayed_shipments_count: int = 0
    network_bottlenecks_count: int = 0
    financial_exposure_summary: Dict[str, Any] = Field(default_factory=dict)
    active_capabilities: List[str] = Field(default_factory=list)
    unavailable_capabilities: List[str] = Field(default_factory=list)
    freshness_summary: Dict[str, str] = Field(default_factory=dict)