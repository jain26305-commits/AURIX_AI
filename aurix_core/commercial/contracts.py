"""
AURIX Enterprise Sales & Commercial Intelligence — Contracts & Schemas
Phase 22 Core Implementation.
Defines authoritative schemas for Account 360, Commercial OTIF, PVM Decomposition,
Discount Leakage, Channel Performance, Product Velocity, and Commercial Anomalies.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ParetoTier(str, Enum):
    """Customer revenue concentration tiering."""
    TIER_A = "TIER_A"  # Top 80% revenue (High Value)
    TIER_B = "TIER_B"  # Next 15% revenue (Core)
    TIER_C = "TIER_C"  # Tail 5% revenue (Low Value / Tail)


class AccountHealthStatus(str, Enum):
    """Account engagement and relationship vitality."""
    THRIVING = "THRIVING"
    STABLE = "STABLE"
    AT_RISK = "AT_RISK"
    DORMANT = "DORMANT"
    CHURNED = "CHURNED"


class VelocityTier(str, Enum):
    """Product commercial movement speed classification."""
    FAST_MOVING = "FAST_MOVING"
    STEADY = "STEADY"
    SLOW_MOVING = "SLOW_MOVING"
    DEAD_STOCK = "DEAD_STOCK"


class CommercialAnomalyDomain(str, Enum):
    """Domains for commercial and sales exception detection."""
    UNAUTHORIZED_DISCOUNT = "UNAUTHORIZED_DISCOUNT"
    VOLUME_DEFECT = "VOLUME_DEFECT"
    MARGIN_DILUTION = "MARGIN_DILUTION"
    ACCOUNT_DORMANCY = "ACCOUNT_DORMANCY"
    ORDER_CANCELLATION_SPIKE = "ORDER_CANCELLATION_SPIKE"


class Account360Summary(BaseModel):
    """Comprehensive commercial profile for a customer account."""
    model_config = ConfigDict(extra="allow")

    customer_id: str
    customer_name: str
    segment: str = "SMB"
    pareto_tier: ParetoTier
    health_status: AccountHealthStatus
    health_score: float  # 0.0 to 100.0
    lifetime_revenue: float
    period_revenue: float
    order_count: int
    average_order_value: float
    order_frequency_days: float
    days_since_last_order: int
    gross_margin_pct: float
    discount_rate_pct: float
    otif_rate_pct: float


class CommercialOTIFReport(BaseModel):
    """Commercial On-Time In-Full delivery performance from customer perspective."""
    tenant_id: str
    period_key: str
    total_orders: int
    on_time_orders: int
    in_full_orders: int
    otif_orders: int
    otif_rate_pct: float
    fill_rate_pct: float
    average_lead_time_days: float
    backlog_order_count: int
    cancellation_rate_pct: float


class PVMDecomposition(BaseModel):
    """Price-Volume-Mix variance decomposition against a baseline period."""
    tenant_id: str
    baseline_period: str
    current_period: str
    currency: str = "USD"
    baseline_revenue: float
    current_revenue: float
    total_revenue_change: float
    price_effect: float
    volume_effect: float
    mix_effect: float
    price_effect_pct: float
    volume_effect_pct: float
    mix_effect_pct: float
    notes: Optional[str] = None


class DiscountLeakageAudit(BaseModel):
    """Audit finding for realized discount leakage and off-invoice concessions."""
    tenant_id: str
    total_gross_revenue: float
    total_discounts_granted: float
    overall_discount_rate_pct: float
    unauthorized_discounts_total: float
    leakage_count: int
    top_discounted_accounts: List[Dict[str, Any]] = Field(default_factory=list)


class ChannelPerformanceSummary(BaseModel):
    """Commercial performance and margin comparison across sales channels."""
    channel_name: str
    gross_revenue: float
    net_revenue: float
    cogs: float
    gross_profit: float
    gross_margin_pct: float
    order_count: int
    average_order_value: float
    revenue_contribution_pct: float


class ProductVelocitySummary(BaseModel):
    """Product sales velocity, attach rates, and catalog concentration."""
    sku_id: str
    sku_name: str
    category: str
    velocity_tier: VelocityTier
    units_sold: float
    gross_revenue: float
    gross_margin_pct: float
    order_attach_rate_pct: float
    top_cross_sell_skus: List[str] = Field(default_factory=list)


class CommercialAnomalyFinding(BaseModel):
    """Commercial exception or rogue sales behavior finding."""
    anomaly_id: str = Field(default_factory=lambda: f"ANOM-COMM-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str
    domain: CommercialAnomalyDomain
    severity: str = "MEDIUM"
    title: str
    description: str
    impact_amount: float = 0.0
    entity_id: str
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CommercialSummaryReport(BaseModel):
    """Master executive sales & commercial operating intelligence summary."""
    tenant_id: str
    period_key: str
    currency: str = "USD"
    gross_revenue: float
    net_revenue: float
    total_orders: int
    average_order_value: float
    active_customers_count: int
    dormant_customers_count: int
    commercial_otif_pct: float
    overall_discount_pct: float
    top_growth_channel: str
    active_anomalies_count: int
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
