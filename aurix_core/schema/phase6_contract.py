"""Output contract schema for Phase 5 Supply Intelligence (Input contract for Phase 6)."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from aurix_core.schema.phase5_contract import MissingInput, TrackedValue

__all__ = [
    "CapacityStatus",
    "SupplyRiskLevel",
    "SupplierPerformanceMetrics",
    "SupplierCandidate",
    "SupplierEvaluation",
    "SupplyRiskSummary",
    "ReplenishmentUrgency",
    "ReplenishmentRequirement",
    "Phase6InputContract",
    "MissingInput",
    "TrackedValue",
]


class CapacityStatus(str, Enum):
    CAPACITY_SUFFICIENT = "CAPACITY_SUFFICIENT"
    CAPACITY_CONSTRAINED = "CAPACITY_CONSTRAINED"
    CAPACITY_UNKNOWN = "CAPACITY_UNKNOWN"


class SupplyRiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    NOT_ASSESSABLE = "NOT_ASSESSABLE"


class SupplierPerformanceMetrics(BaseModel):
    on_time_delivery_rate: TrackedValue
    in_full_delivery_rate: TrackedValue
    otif_rate: TrackedValue
    fill_rate: TrackedValue
    mean_lead_time_days: TrackedValue
    lead_time_std_days: TrackedValue
    defect_rate: TrackedValue
    total_orders_evaluated: int


class SupplierCandidate(BaseModel):
    supplier_id: str
    supplier_name: str
    unit_price: Optional[TrackedValue] = None
    currency: str = "USD"
    lead_time_days: Optional[TrackedValue] = None
    lead_time_std_days: Optional[TrackedValue] = None
    moq: Optional[TrackedValue] = None
    pack_size: Optional[TrackedValue] = None
    capacity_units: Optional[TrackedValue] = None
    performance: Optional[SupplierPerformanceMetrics] = None


class SupplierEvaluation(BaseModel):
    supplier_id: str
    supplier_name: str
    is_eligible: bool
    rejection_reason: Optional[str] = None
    unit_price: float
    currency: str = "USD"
    raw_order_quantity: float
    constrained_order_quantity: float
    moq_applied: bool
    pack_size_applied: bool
    total_purchase_cost: Optional[float] = None
    capacity_status: CapacityStatus
    supply_risk_level: SupplyRiskLevel
    supply_risk_score: float
    rank: Optional[int] = None
    selection_status: str  # "RECOMMENDED", "ALTERNATIVE", "REJECTED"
    preference_reasons: List[str] = []


class SupplyRiskSummary(BaseModel):
    overall_risk_level: SupplyRiskLevel
    single_source_dependency: bool
    primary_risk_drivers: List[str] = []


class ReplenishmentUrgency(str, Enum):
    NO_ACTION = "NO_ACTION"
    MONITOR = "MONITOR"
    PLAN_REPLENISHMENT = "PLAN_REPLENISHMENT"
    REPLENISH_NOW = "REPLENISH_NOW"
    EXPEDITED_REPLENISHMENT = "EXPEDITED_REPLENISHMENT"


class ReplenishmentRequirement(BaseModel):
    required: bool
    base_required_quantity: float
    urgency: ReplenishmentUrgency
    inventory_coverage_days: Optional[float] = None
    reorder_point: Optional[float] = None
    inventory_position: Optional[float] = None
    reason: str


class Phase6InputContract(BaseModel):
    sku_id: str
    status: str
    missing_inputs: List[MissingInput] = []
    replenishment: ReplenishmentRequirement
    recommended_supplier: Optional[SupplierEvaluation] = None
    candidate_evaluations: List[SupplierEvaluation] = []
    supply_risk: SupplyRiskSummary
    limitations: List[str] = []
    provenance: Dict[str, Any]
