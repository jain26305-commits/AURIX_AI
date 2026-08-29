"""
AURIX Enterprise Business Context Graph — Contracts & Schemas
Phase 24 Core Implementation.
Defines authoritative schemas for Graph Nodes, Directed Edges, Evidence, Business Memory,
Data Contracts, Business DNA, Why-Chain, and Capability Readiness.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EntityType(str, Enum):
    """Canonical classification for graph nodes."""
    CUSTOMER = "CUSTOMER"
    SUPPLIER = "SUPPLIER"
    PRODUCT = "PRODUCT"
    SKU = "SKU"
    ORDER = "ORDER"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    INVOICE = "INVOICE"
    PAYMENT = "PAYMENT"
    SHIPMENT = "SHIPMENT"
    WORK_ORDER = "WORK_ORDER"
    WORK_CENTER = "WORK_CENTER"
    MACHINE = "MACHINE"
    CONTRACT = "CONTRACT"
    ASSURANCE_FINDING = "ASSURANCE_FINDING"
    LOCATION = "LOCATION"


class RelationshipType(str, Enum):
    """Canonical classification for directed graph edges."""
    CUSTOMER_OF = "CUSTOMER_OF"
    PLACED_ORDER = "PLACED_ORDER"
    CONTAINS_ITEM = "CONTAINS_ITEM"
    SUPPLIED_BY = "SUPPLIED_BY"
    INVOICED_AS = "INVOICED_AS"
    SETTLED_BY = "SETTLED_BY"
    FULFILLED_BY_SHIPMENT = "FULFILLED_BY_SHIPMENT"
    PRODUCED_VIA = "PRODUCED_VIA"
    ROUTED_TO = "ROUTED_TO"
    DEPENDS_ON = "DEPENDS_ON"
    CONSTRAINED_BY = "CONSTRAINED_BY"
    IMPACTS_FINANCE = "IMPACTS_FINANCE"
    GOVERNED_BY = "GOVERNED_BY"
    CAUSES = "CAUSES"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"


class RelationshipConfidence(str, Enum):
    """Confidence and provenance classification for graph relationships."""
    OBSERVED = "OBSERVED"        # Proven directly by transactional database foreign keys
    CORRELATED = "CORRELATED"    # Statistically linked via co-occurrence or time-series alignment
    INFERRED = "INFERRED"        # Derived via business rule heuristics
    UNKNOWN = "UNKNOWN"          # Unverified relationship


class RelationshipStatus(str, Enum):
    """Lifecycle status of a graph edge."""
    ACTIVE = "ACTIVE"
    HISTORICAL = "HISTORICAL"
    STALE = "STALE"
    DISPUTED = "DISPUTED"


class MemoryCategory(str, Enum):
    """Classification for institutional business memory records."""
    DECISION_HISTORY = "DECISION_HISTORY"
    MANAGER_OVERRIDE = "MANAGER_OVERRIDE"
    ACTION_OUTCOME = "ACTION_OUTCOME"
    CUSTOMER_BEHAVIOR = "CUSTOMER_BEHAVIOR"
    SUPPLIER_PATTERN = "SUPPLIER_PATTERN"
    OPERATING_POLICY = "OPERATING_POLICY"
    LESSON_LEARNED = "LESSON_LEARNED"


class DecisionOutcomeStatus(str, Enum):
    """Verified outcome state of a past decision or action."""
    SUCCESSFUL = "SUCCESSFUL"
    PARTIALLY_SUCCESSFUL = "PARTIALLY_SUCCESSFUL"
    UNSUCCESSFUL = "UNSUCCESSFUL"
    PENDING_EVALUATION = "PENDING_EVALUATION"
    OVERRIDDEN = "OVERRIDDEN"


class DataContractStatus(str, Enum):
    """Operating status of an enterprise data contract."""
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    MUTATED = "MUTATED"
    DEPRECATED = "DEPRECATED"


# --- Graph Node & Edge Contracts ---
class ContextNode(BaseModel):
    """Canonical graph node representing an enterprise entity."""
    model_config = ConfigDict(extra="allow")

    id: str = Field(default_factory=lambda: f"NODE-{uuid.uuid4().hex[:10].upper()}")
    tenant_id: str
    entity_type: EntityType
    canonical_id: str
    name: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    source_system: str = "AURIX_FABRIC"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContextEdge(BaseModel):
    """Directed, evidence-backed relationship between two graph entities."""
    model_config = ConfigDict(extra="allow")

    id: str = Field(default_factory=lambda: f"EDGE-{uuid.uuid4().hex[:10].upper()}")
    tenant_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: RelationshipType
    confidence_level: RelationshipConfidence = RelationshipConfidence.OBSERVED
    relationship_status: RelationshipStatus = RelationshipStatus.ACTIVE
    weight: float = 1.0
    evidence: Dict[str, Any] = Field(default_factory=dict)
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None


# --- Business Memory Contracts ---
class BusinessMemoryRecord(BaseModel):
    """Institutional memory record capturing past decisions, overrides, and outcomes."""
    id: str = Field(default_factory=lambda: f"MEM-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str
    category: MemoryCategory
    title: str
    description: str
    context_entity_id: Optional[str] = None
    decision_action_id: Optional[str] = None
    outcome_status: DecisionOutcomeStatus = DecisionOutcomeStatus.PENDING_EVALUATION
    lessons_learned: Optional[str] = None
    confidence_score: float = 1.0
    recorded_by: str = "SYSTEM_GOVERNANCE"
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Data Contract Registry Contracts ---
class DataContractDefinition(BaseModel):
    """Enterprise Data Contract specification and consumer registry."""
    id: str = Field(default_factory=lambda: f"CTR-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str
    dataset_name: str
    schema_version: str = "v1.0"
    owner_domain: str
    freshness_slo_seconds: int = 3600
    quality_slo_pct: float = 98.0
    downstream_consumers: List[str] = Field(default_factory=list)
    status: DataContractStatus = DataContractStatus.ACTIVE


# --- Business DNA Contracts ---
class BusinessDNASnapshot(BaseModel):
    """Empirical operating profile and concentration metrics."""
    tenant_id: str
    period_key: str
    operating_model: str
    customer_concentration_hhi: float
    supplier_concentration_hhi: float
    inventory_intensity_pct: float
    working_capital_intensity_pct: float
    manufacturing_complexity_tier: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Capability Readiness Contracts ---
class CapabilityReadinessItem(BaseModel):
    """Domain capability readiness item derived from connected data coverage."""
    domain: str
    status: str  # "AVAILABLE", "PARTIAL", "UNAVAILABLE"
    data_coverage_pct: float
    freshness_status: str
    active_connectors_count: int
    details: str


# --- Why-Chain Contracts ---
class WhyChainStep(BaseModel):
    """A single hop in a causal or correlated root-cause chain."""
    step_index: int
    from_node_name: str
    from_node_type: str
    to_node_name: str
    to_node_type: str
    relationship_type: str
    confidence: RelationshipConfidence
    evidence_summary: str
    metric_impact: Optional[str] = None


class WhyChainReport(BaseModel):
    """Reconstructed Why-Chain linking operational symptoms to root causes."""
    tenant_id: str
    target_symptom: str
    root_cause_candidate: str
    confidence_pct: float
    chain_length: int
    steps: List[WhyChainStep]


# --- Master Context Summary ---
class ContextSummaryReport(BaseModel):
    """Master executive cross-domain business context summary."""
    tenant_id: str
    period_key: str
    total_nodes_count: int
    total_edges_count: int
    active_memories_count: int
    active_contracts_count: int
    overall_readiness_pct: float
    business_dna_model: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
