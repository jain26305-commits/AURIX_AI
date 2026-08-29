"""
AURIX Risk, Causal & External Intelligence — Contracts & Schemas
Phase 26 Core Implementation.
Defines authoritative schemas for Risk Findings, Exposure Models, Business Impact Prioritization,
Causal Classifications, External Signals, Signal Mappings, Opportunities, and Coverage Reports.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RiskDomain(str, Enum):
    """Enterprise risk domain classifications."""
    SUPPLIER = "SUPPLIER"
    CUSTOMER = "CUSTOMER"
    PRODUCT_SKU = "PRODUCT_SKU"
    INVENTORY = "INVENTORY"
    PLANT_FACILITY = "PLANT_FACILITY"
    FINANCIAL = "FINANCIAL"
    COMMERCIAL = "COMMERCIAL"
    MANUFACTURING = "MANUFACTURING"
    PROCESS = "PROCESS"
    EXTERNAL_ENVIRONMENT = "EXTERNAL_ENVIRONMENT"


class RiskSeverity(str, Enum):
    """Risk severity classification."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskStatus(str, Enum):
    """Lifecycle status of an identified risk."""
    ACTIVE = "ACTIVE"
    MONITORED = "MONITORED"
    MITIGATING = "MITIGATING"
    RESOLVED = "RESOLVED"
    EXPIRED = "EXPIRED"


class CausalClassification(str, Enum):
    """Evidence-backed relationship classification."""
    OBSERVED = "OBSERVED"        # Directly proven by transactional logs
    CORRELATED = "CORRELATED"    # Statistically linked in time-series co-occurrence
    INFERRED = "INFERRED"        # Derived via business rule heuristics
    CAUSAL = "CAUSAL"            # Proven causal link with temporal precedence & confounder control
    UNKNOWN = "UNKNOWN"          # Unverified relationship


class SignalType(str, Enum):
    """External reality signal classifications."""
    WEATHER_DISRUPTION = "WEATHER_DISRUPTION"
    PORT_CONGESTION = "PORT_CONGESTION"
    FREIGHT_RATE_SPIKE = "FREIGHT_RATE_SPIKE"
    FX_VOLATILITY = "FX_VOLATILITY"
    COMMODITY_PRICE_SURGE = "COMMODITY_PRICE_SURGE"
    GEOPOLITICAL_RESTRICTION = "GEOPOLITICAL_RESTRICTION"
    MARKET_DEMAND_SHIFT = "MARKET_DEMAND_SHIFT"


class SignalStatus(str, Enum):
    """Operational health of an external feed signal."""
    LIVE = "LIVE"
    RECENT = "RECENT"
    STALE = "STALE"
    DEGRADED = "DEGRADED"


class OpportunityType(str, Enum):
    """Operational and financial upside classifications."""
    PROCUREMENT_SAVINGS = "PROCUREMENT_SAVINGS"
    FREIGHT_CONSOLIDATION = "FREIGHT_CONSOLIDATION"
    WORKING_CAPITAL_RELEASE = "WORKING_CAPITAL_RELEASE"
    MARGIN_RECOVERY = "MARGIN_RECOVERY"
    INVENTORY_REDUCTION = "INVENTORY_REDUCTION"
    SERVICE_IMPROVEMENT = "SERVICE_IMPROVEMENT"


# --- Core Risk Finding Schemas ---
class RiskFinding(BaseModel):
    """Authoritative enterprise risk finding record."""
    model_config = ConfigDict(extra="allow")

    risk_id: str = Field(default_factory=lambda: f"RSK-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str
    risk_domain: RiskDomain
    entity_type: str
    entity_id: str
    title: str
    description: str
    probability: float = Field(ge=0.0, le=1.0)
    impact_amount_usd: float = 0.0
    exposure_amount_usd: float = 0.0
    priority_score: float = 0.0
    urgency_hours: float = 24.0
    confidence_level: float = Field(default=0.9, ge=0.0, le=1.0)
    severity: RiskSeverity = RiskSeverity.MEDIUM
    status: RiskStatus = RiskStatus.ACTIVE
    evidence: Dict[str, Any] = Field(default_factory=dict)
    first_detected: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_to: Optional[datetime] = None


# --- External Reality Signal Schemas ---
class ExternalSignal(BaseModel):
    """Normalized external reality event or market feed record."""
    model_config = ConfigDict(extra="allow")

    signal_id: str = Field(default_factory=lambda: f"SIG-{uuid.uuid4().hex[:8].upper()}")
    source_name: str
    source_record_id: str
    signal_type: SignalType
    geography: str
    severity: RiskSeverity = RiskSeverity.MEDIUM
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    metric_value: float = 0.0
    metric_unit: str = "INDEX"
    currency: str = "USD"
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_from: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_to: Optional[datetime] = None
    status: SignalStatus = SignalStatus.LIVE
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


class ExternalSignalMapping(BaseModel):
    """Tenant-scoped binding connecting external signals to internal enterprise entities."""
    mapping_id: str = Field(default_factory=lambda: f"MAP-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str
    signal_id: str
    entity_type: str
    entity_id: str
    mapping_rule: str
    confidence: float = 0.9
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Opportunity Finding Schemas ---
class OpportunityFinding(BaseModel):
    """Identified operational or financial upside opportunity."""
    model_config = ConfigDict(extra="allow")

    opportunity_id: str = Field(default_factory=lambda: f"OPP-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str
    opportunity_type: OpportunityType
    entity_type: str
    entity_id: str
    title: str
    description: str
    potential_value_usd: float = 0.0
    probability: float = Field(default=0.85, ge=0.0, le=1.0)
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    priority_rank: int = 1
    evidence: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Causal Evidence Schemas ---
class CausalEvidenceRecord(BaseModel):
    """Evidence envelope supporting causal or correlated relationships."""
    causal_id: str = Field(default_factory=lambda: f"CSL-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str
    cause_entity_id: str
    effect_entity_id: str
    relationship_classification: CausalClassification
    methodology: str
    confidence_score: float = 0.95
    known_confounders: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Coverage & Readiness Schemas ---
class RiskCoverageReport(BaseModel):
    """Empirical assessment of risk and signal data coverage across domains."""
    tenant_id: str
    supplier_coverage_pct: float
    customer_coverage_pct: float
    manufacturing_coverage_pct: float
    process_coverage_pct: float
    external_signal_coverage_pct: float
    overall_coverage_pct: float
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Master Risk Summary Report ---
class RiskSummaryReport(BaseModel):
    """Master executive risk, opportunity, and external intelligence summary."""
    tenant_id: str
    period_key: str
    total_active_risks_count: int
    total_exposure_usd: float
    total_expected_loss_usd: float
    critical_priorities_count: int
    top_risk_domain: str
    active_opportunities_count: int
    total_opportunity_value_usd: float
    active_external_signals_count: int
    overall_risk_coverage_pct: float
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
