"""Output contract schema for Phase 6 Logistics Intelligence (Input contract for Phase 7)."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from aurix_core.schema.phase5_contract import MissingInput, TrackedValue, ValueState


class ShipmentStatus(str, Enum):
    NOT_DISPATCHED = "NOT_DISPATCHED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    DELAYED = "DELAYED"
    EXCEPTION = "EXCEPTION"
    UNKNOWN = "UNKNOWN"


class LogisticsRiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    NOT_ASSESSABLE = "NOT_ASSESSABLE"


class ExpediteRecommendation(str, Enum):
    NORMAL_TRANSPORT = "NORMAL_TRANSPORT"
    MONITOR = "MONITOR"
    EXPEDITED_REPLENISHMENT = "EXPEDITED_REPLENISHMENT"
    EXPEDITED_SHIPPING_REQUIRED = "EXPEDITED_SHIPPING_REQUIRED"
    EXPEDITED_CRITICAL = "EXPEDITED_CRITICAL"
    NOT_REQUIRED = "NOT_REQUIRED"


class EvidenceQuality(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNAVAILABLE = "UNAVAILABLE"


class TransportDetails(BaseModel):
    carrier_id: Optional[str] = None
    mode: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    distance_km: TrackedValue


class ETADetails(BaseModel):
    estimated_delivery_date: Optional[str] = None
    value_state: ValueState
    eta_source: str
    eta_method: str
    evidence_quality: EvidenceQuality
    supporting_sample_size: Optional[int] = None
    provenance: Dict[str, Any]


class CostBreakdown(BaseModel):
    total_freight_cost: TrackedValue
    cost_per_unit: TrackedValue
    cost_per_kg: TrackedValue
    currency: str = "USD"


class ShipmentEvaluation(BaseModel):
    shipment_id: str
    sku_id: str
    status: ShipmentStatus
    transport: TransportDetails
    eta: ETADetails
    costs: CostBreakdown


class CarrierPerformanceMetrics(BaseModel):
    sample_size: int
    on_time_delivery_rate: TrackedValue
    in_full_delivery_rate: TrackedValue
    otif_rate: TrackedValue
    median_transit_days: TrackedValue
    p90_transit_days: TrackedValue
    p95_transit_days: TrackedValue
    transit_std_days: TrackedValue
    mean_delay_days: TrackedValue


class LogisticsRiskSummary(BaseModel):
    risk_level: LogisticsRiskLevel
    risk_score: float
    delay_probability: float
    primary_risk_drivers: List[str] = []


class ExpediteDecision(BaseModel):
    recommendation: ExpediteRecommendation
    justification: str
    urgency_score: float


class Phase7InputContract(BaseModel):
    sku_id: str
    status: str
    missing_inputs: List[MissingInput] = []
    shipment_evaluation: Optional[ShipmentEvaluation] = None
    carrier_performance: Optional[CarrierPerformanceMetrics] = None
    overall_logistics_risk: LogisticsRiskSummary
    expedite_decision: ExpediteDecision
    limitations: List[str] = []
    provenance: Dict[str, Any]
