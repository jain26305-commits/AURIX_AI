"""
AURIX Process Intelligence & Object-Centric Process Mining — Contracts & Schemas
Phase 25 Core Implementation.
Defines authoritative schemas for Process Events, OCPM Models, Pipelines (O2C, P2P, Mfg, Returns),
Variants, Cycle Times, Conformance, Bottlenecks, SLAs, Rework Loops, and Impact Mappings.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProcessType(str, Enum):
    """Core enterprise business processes."""
    ORDER_TO_CASH = "ORDER_TO_CASH"
    PROCURE_TO_PAY = "PROCURE_TO_PAY"
    MANUFACTURING_PRODUCTION = "MANUFACTURING_PRODUCTION"
    RETURNS_AND_REVERSE_LOGISTICS = "RETURNS_AND_REVERSE_LOGISTICS"


class ProcessEventType(str, Enum):
    """Standardized event activity verbs."""
    # O2C
    ORDER_PLACED = "ORDER_PLACED"
    CREDIT_CHECK_APPROVED = "CREDIT_CHECK_APPROVED"
    INVENTORY_ALLOCATED = "INVENTORY_ALLOCATED"
    GOODS_DISPATCHED = "GOODS_DISPATCHED"
    SHIPMENT_DELIVERED = "SHIPMENT_DELIVERED"
    INVOICE_ISSUED = "INVOICE_ISSUED"
    PAYMENT_SETTLED = "PAYMENT_SETTLED"
    # P2P
    PURCHASE_REQUISITION_CREATED = "PURCHASE_REQUISITION_CREATED"
    PURCHASE_ORDER_ISSUED = "PURCHASE_ORDER_ISSUED"
    GOODS_RECEIPT_POSTED = "GOODS_RECEIPT_POSTED"
    VENDOR_INVOICE_RECEIVED = "VENDOR_INVOICE_RECEIVED"
    THREE_WAY_MATCH_VERIFIED = "THREE_WAY_MATCH_VERIFIED"
    VENDOR_PAYMENT_DISBURSED = "VENDOR_PAYMENT_DISBURSED"
    # Manufacturing
    PRODUCTION_ORDER_RELEASED = "PRODUCTION_ORDER_RELEASED"
    MATERIAL_STAGED = "MATERIAL_STAGED"
    OPERATION_STARTED = "OPERATION_STARTED"
    QUALITY_INSPECTION_PASSED = "QUALITY_INSPECTION_PASSED"
    OPERATION_COMPLETED = "OPERATION_COMPLETED"
    # Returns
    RETURN_REQUESTED = "RETURN_REQUESTED"
    RMA_AUTHORIZED = "RMA_AUTHORIZED"
    RETURN_RECEIVED = "RETURN_RECEIVED"
    INSPECTION_COMPLETED = "INSPECTION_COMPLETED"
    CREDIT_MEMO_ISSUED = "CREDIT_MEMO_ISSUED"


class ConformanceStatus(str, Enum):
    """Process conformance compliance state."""
    CONFORMANT = "CONFORMANT"
    SKIPPED_STEP = "SKIPPED_STEP"
    WRONG_SEQUENCE = "WRONG_SEQUENCE"
    UNAUTHORIZED_STEP = "UNAUTHORIZED_STEP"
    REWORK_LOOP = "REWORK_LOOP"


class SLASeverity(str, Enum):
    """SLA breach severity level."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DataAvailabilityStatus(str, Enum):
    """Process event completeness indicator."""
    AVAILABLE = "AVAILABLE"
    PARTIALLY_AVAILABLE = "PARTIALLY_AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


# --- Core Process Event & OCPM Schemas ---
class ProcessEvent(BaseModel):
    """Canonical process event envelope."""
    model_config = ConfigDict(extra="allow")

    event_id: str = Field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:10].upper()}")
    tenant_id: str
    process_type: ProcessType
    event_type: str
    event_timestamp: datetime
    source_system: str = "AURIX_FABRIC"
    source_record_id: str
    actor: Optional[str] = None
    location_id: Optional[str] = None
    object_bindings: Dict[str, str] = Field(default_factory=dict)  # {"order_id": "O-1", "invoice_id": "INV-1"}
    attributes: Dict[str, Any] = Field(default_factory=dict)
    evidence: Dict[str, Any] = Field(default_factory=dict)


class OCPMObjectGraph(BaseModel):
    """Object-Centric Process Model mapping event streams across intersecting entities."""
    tenant_id: str
    process_type: ProcessType
    total_events_count: int
    object_types_involved: List[str]
    events: List[ProcessEvent]


# --- Process Variant Schemas ---
class ProcessVariant(BaseModel):
    """Discovered execution path variant."""
    variant_id: str = Field(default_factory=lambda: f"VAR-{uuid.uuid4().hex[:8].upper()}")
    process_type: ProcessType
    step_sequence: List[str]
    case_count: int
    frequency_pct: float
    average_duration_hours: float
    is_standard_path: bool = False


# --- Cycle Time & Queue Schemas ---
class CycleTimeBreakdown(BaseModel):
    """Touch time vs Waiting/Queue time decomposition."""
    process_type: ProcessType
    total_cycle_time_hours: float
    active_touch_time_hours: float
    waiting_queue_time_hours: float
    waiting_time_ratio_pct: float
    handoff_delays_hours: float
    benchmark_median_hours: float
    benchmark_p90_hours: float


# --- Bottleneck & Conformance Schemas ---
class ProcessBottleneck(BaseModel):
    """Multi-variable bottleneck finding."""
    bottleneck_id: str = Field(default_factory=lambda: f"BNK-{uuid.uuid4().hex[:8].upper()}")
    process_type: ProcessType
    step_name: str
    queue_depth_cases: int
    average_waiting_hours: float
    sla_breach_rate_pct: float
    severity: str = "HIGH"
    primary_friction_cause: str
    annualized_financial_drag: float = 0.0


class ConformanceViolation(BaseModel):
    """Process conformance audit finding."""
    violation_id: str = Field(default_factory=lambda: f"CONF-{uuid.uuid4().hex[:8].upper()}")
    process_type: ProcessType
    case_id: str
    conformance_status: ConformanceStatus
    title: str
    description: str
    expected_sequence: List[str]
    actual_sequence: List[str]
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SLAViolation(BaseModel):
    """SLA threshold violation record."""
    violation_id: str = Field(default_factory=lambda: f"SLA-{uuid.uuid4().hex[:8].upper()}")
    process_type: ProcessType
    case_id: str
    milestone_name: str
    target_sla_hours: float
    actual_duration_hours: float
    deviation_hours: float
    severity: SLASeverity
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReworkLoop(BaseModel):
    """Detected repetitive rework loop."""
    loop_id: str = Field(default_factory=lambda: f"LP-{uuid.uuid4().hex[:8].upper()}")
    process_type: ProcessType
    case_id: str
    loop_steps: List[str]
    iterations_count: int
    total_wasted_hours: float
    estimated_cost_waste: float


# --- Process-to-Business Impact ---
class ProcessBusinessImpact(BaseModel):
    """Cross-domain operational and financial impact translation."""
    tenant_id: str
    process_type: ProcessType
    dso_inflation_days: float
    working_capital_friction_usd: float
    scrap_cost_loss_usd: float
    commercial_revenue_at_risk_usd: float
    otif_penalty_pct: float
    impact_summary: str


# --- Master Process Summary ---
class ProcessSummaryReport(BaseModel):
    """Master executive process operating intelligence summary."""
    tenant_id: str
    period_key: str
    overall_process_health_score: float  # 0.0 to 100.0
    total_events_processed: int
    active_cases_count: int
    discovered_variants_count: int
    conformance_rate_pct: float
    sla_compliance_rate_pct: float
    average_o2c_cycle_days: float
    average_p2p_cycle_days: float
    top_bottleneck_step: str
    total_process_financial_drag_usd: float
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
