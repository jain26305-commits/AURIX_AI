"""Phase 4/5 upstream contract schema definitions."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ValueState(str, Enum):
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"
    USER_PROVIDED = "USER_PROVIDED"
    ASSUMPTION = "ASSUMPTION"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TrackedValue(BaseModel):
    value: Optional[Any] = None
    state: ValueState
    source: str
    notes: Optional[Any] = None


class MissingInput(BaseModel):
    field: str
    state: str
    domain: str
    severity: str
    prompt: str


class InventoryMetrics(BaseModel):
    safety_stock: TrackedValue
    reorder_point: TrackedValue
    economic_order_quantity: TrackedValue
    order_quantity: TrackedValue
    inventory_position: TrackedValue
    inventory_coverage_days: TrackedValue


class FinancialExposure(BaseModel):
    inventory_value: TrackedValue
    holding_cost_exposure: TrackedValue
    stockout_cost_exposure: TrackedValue


InventoryFinancials = FinancialExposure


class Phase5InputContract(BaseModel):
    sku_id: str
    status: str
    missing_inputs: List[MissingInput] = []
    metrics: Optional[InventoryMetrics] = None
    risk_status: Optional[str] = None
    financials: Optional[InventoryFinancials] = None
    policy_applied: Optional[str] = None
    limitations: List[str] = []
    provenance: Dict[str, Any]
