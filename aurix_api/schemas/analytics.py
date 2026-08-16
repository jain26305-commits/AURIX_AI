"""Domain analytics response schemas for Phase 10."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DemandAnalyticsResponse(BaseModel):
    """Demand classification and statistical variance analytics."""
    status: str = "COMPUTED"
    classified_skus: Dict[str, Any] = Field(default_factory=dict)
    total_skus: int = 0


class ForecastAnalyticsResponse(BaseModel):
    """Forecasting point estimates, confidence bounds, and champion models."""
    status: str = "COMPUTED"
    sku_forecasts: Dict[str, Any] = Field(default_factory=dict)
    total_forecasts: int = 0


class InventoryAnalyticsResponse(BaseModel):
    """Safety stock, reorder point, and inventory position risk analytics."""
    status: str = "COMPUTED"
    inventory_policies: Dict[str, Any] = Field(default_factory=dict)
    risk_evaluations: Dict[str, Any] = Field(default_factory=dict)
    high_risk_skus_count: int = 0


class SupplyAnalyticsResponse(BaseModel):
    """Supplier performance, OTD rates, and supplier ranking allocations."""
    status: str = "COMPUTED"
    supplier_performance: Dict[str, Any] = Field(default_factory=dict)
    supplier_rankings: Dict[str, Any] = Field(default_factory=dict)
    high_risk_suppliers_count: int = 0


class LogisticsAnalyticsResponse(BaseModel):
    """Shipment tracking, dynamic ETAs, and delay evaluations."""
    status: str = "COMPUTED"
    shipments: Dict[str, Any] = Field(default_factory=dict)
    delayed_shipments_count: int = 0


class NetworkAnalyticsResponse(BaseModel):
    """Network topology nodes, capacity utilizations, and lateral rebalancing transfers."""
    status: str = "COMPUTED"
    network_nodes: Dict[str, Any] = Field(default_factory=dict)
    network_bottlenecks_count: int = 0
    rebalancing_recommendations: List[Dict[str, Any]] = Field(default_factory=list)


class EconomicsAnalyticsResponse(BaseModel):
    """Total cost of ownership, working capital, and scenario simulations."""
    status: str = "COMPUTED"
    portfolio_working_capital: float = 0.0
    portfolio_annual_holding_cost: float = 0.0
    currency: str = "USD"
    sku_financials: Dict[str, Any] = Field(default_factory=dict)
    scenarios_evaluated: Dict[str, Any] = Field(default_factory=dict)