"""Output contract schema for Phase 8 Financial Intelligence & Scenario Simulation."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from aurix_core.schema.phase5_contract import MissingInput, TrackedValue


class FinancialRiskLevel(str, Enum):
    """Categorization of financial exposure and working capital risk."""

    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNAVAILABLE = "UNAVAILABLE"


class ScenarioType(str, Enum):
    """Supported deterministic scenario categories for sensitivity analysis."""

    DEMAND_SHOCK = "DEMAND_SHOCK"
    LEAD_TIME_VOLATILITY = "LEAD_TIME_VOLATILITY"
    FREIGHT_COST_ESCALATION = "FREIGHT_COST_ESCALATION"
    SUPPLIER_PRICE_CHANGE = "SUPPLIER_PRICE_CHANGE"
    SERVICE_LEVEL_ADJUSTMENT = "SERVICE_LEVEL_ADJUSTMENT"
    NETWORK_DISRUPTION = "NETWORK_DISRUPTION"


class ScenarioStatus(str, Enum):
    """Execution status of a defined scenario."""

    COMPUTED = "COMPUTED"
    INFEASIBLE = "INFEASIBLE"
    UNAVAILABLE_INPUTS = "UNAVAILABLE_INPUTS"
    NOT_ASSESSABLE = "NOT_ASSESSABLE"


class TCOBreakdown(BaseModel):
    """Total Cost of Ownership breakdown preserving Zero-Fabrication principles."""

    currency: str
    purchase_cost: TrackedValue
    freight_cost: TrackedValue
    holding_cost: TrackedValue
    expedite_cost: TrackedValue
    stockout_exposure_cost: TrackedValue
    total_cost_of_ownership: TrackedValue


class WorkingCapitalExposure(BaseModel):
    """Working capital segmentation at the SKU/Node level."""

    sku_id: str
    node_id: str
    currency: str
    total_inventory_value: TrackedValue
    cycle_stock_value: TrackedValue
    safety_stock_value: TrackedValue
    excess_capital_tied: TrackedValue
    annual_holding_cost: TrackedValue
    financial_risk_level: FinancialRiskLevel


class CurrencyGroupedPortfolio(BaseModel):
    """Currency-isolated portfolio aggregation to prevent multi-currency math contamination."""

    currency: str
    total_inventory_value: TrackedValue
    total_working_capital_exposure: TrackedValue
    total_holding_cost: TrackedValue
    total_freight_spend: TrackedValue


class ScenarioOverride(BaseModel):
    """Deterministic, isolated input multipliers and overrides for scenario execution."""

    demand_multiplier: Optional[float] = None
    lead_time_multiplier: Optional[float] = None
    freight_cost_multiplier: Optional[float] = None
    supplier_price_multiplier: Optional[float] = None
    service_level_target: Optional[float] = None


class ScenarioFinancialComparison(BaseModel):
    """Explicit Baseline vs. Scenario vs. Delta tracking for a specific currency."""

    currency: str
    baseline_inventory_value: TrackedValue
    scenario_inventory_value: TrackedValue
    inventory_value_delta: TrackedValue
    baseline_holding_cost: TrackedValue
    scenario_holding_cost: TrackedValue
    holding_cost_delta: TrackedValue
    baseline_tco: TrackedValue
    scenario_tco: TrackedValue
    tco_delta: TrackedValue


class ScenarioResult(BaseModel):
    """Output container for a single isolated scenario evaluation."""

    scenario_id: str
    scenario_type: ScenarioType
    description: str
    status: ScenarioStatus
    overrides: ScenarioOverride
    financial_comparison_by_currency: Dict[str, ScenarioFinancialComparison] = Field(default_factory=dict)
    operational_impact: Dict[str, TrackedValue] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)


class Phase10InputContract(BaseModel):
    """System-level output contract for Phase 8 Financial Intelligence & Scenario Simulation."""

    status: str
    missing_inputs: List[MissingInput] = Field(default_factory=list)
    portfolio_financials_by_currency: Dict[str, CurrencyGroupedPortfolio] = Field(default_factory=dict)
    sku_working_capital: Dict[str, List[WorkingCapitalExposure]] = Field(default_factory=dict)
    sku_tco: Dict[str, TCOBreakdown] = Field(default_factory=dict)
    scenarios: Dict[str, ScenarioResult] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)