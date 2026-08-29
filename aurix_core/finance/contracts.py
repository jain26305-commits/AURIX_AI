"""
AURIX Business Finance Intelligence — Financial Contracts & Schemas
Phase 21 Core Implementation.
Defines authoritative schemas for P&L, Revenue, Margins, AR/AP, Working Capital, CCC, and Anomalies.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DataAvailabilityStatus(str, Enum):
    """Explicit indicator of underlying financial data completeness."""
    AVAILABLE = "AVAILABLE"
    PARTIALLY_AVAILABLE = "PARTIALLY_AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class FiscalPeriodType(str, Enum):
    """Supported financial period classifications."""
    CALENDAR_MONTH = "CALENDAR_MONTH"
    FISCAL_QUARTER = "FISCAL_QUARTER"
    FISCAL_YEAR = "FISCAL_YEAR"
    MTD = "MTD"
    QTD = "QTD"
    YTD = "YTD"
    CUSTOM = "CUSTOM"


class FinancialAnomalyDomain(str, Enum):
    """Domains for statistical financial anomaly alerts."""
    REVENUE = "REVENUE"
    GROSS_MARGIN = "GROSS_MARGIN"
    COGS_INFLATION = "COGS_INFLATION"
    INVOICE_SPIKE = "INVOICE_SPIKE"
    PAYMENT_IRREGULARITY = "PAYMENT_IRREGULARITY"
    AR_AGING_DRIFT = "AR_AGING_DRIFT"


class PnLStatement(BaseModel):
    """Deterministic P&L breakdown with explicit data availability indicators."""
    model_config = ConfigDict(extra="allow")

    tenant_id: str
    period_key: str
    currency: str = "USD"
    gross_revenue: float
    returns_amount: float = 0.0
    discounts_amount: float = 0.0
    credit_notes_amount: float = 0.0
    net_revenue: float
    cogs: float
    gross_profit: float
    gross_margin_pct: float
    variable_operating_costs: Optional[float] = None
    contribution_margin: Optional[float] = None
    contribution_margin_pct: Optional[float] = None
    operating_expenses: Optional[float] = None
    operating_profit: Optional[float] = None
    ebitda: Optional[float] = None
    operating_profit_status: DataAvailabilityStatus = DataAvailabilityStatus.UNAVAILABLE
    ebitda_status: DataAvailabilityStatus = DataAvailabilityStatus.UNAVAILABLE


class RevenueBreakdown(BaseModel):
    """Multi-dimensional revenue analytics rollup."""
    tenant_id: str
    period_key: str
    currency: str = "USD"
    gross_revenue: float
    net_revenue: float
    by_customer: Dict[str, float] = Field(default_factory=dict)
    by_sku: Dict[str, float] = Field(default_factory=dict)
    by_channel: Dict[str, float] = Field(default_factory=dict)
    by_geography: Dict[str, float] = Field(default_factory=dict)


class MarginSummary(BaseModel):
    """Gross and contribution margin metrics with data validity flags."""
    tenant_id: str
    gross_profit: float
    gross_margin_pct: float
    contribution_margin: Optional[float] = None
    contribution_margin_pct: Optional[float] = None
    margin_status: DataAvailabilityStatus
    notes: Optional[str] = None


class CustomerProfitabilitySummary(BaseModel):
    """Customer-level revenue and contribution profitability record."""
    customer_id: str
    customer_name: str
    gross_revenue: float
    net_revenue: float
    cogs: float
    gross_profit: float
    gross_margin_pct: float
    variable_costs: float = 0.0
    contribution_margin: float
    profitability_tier: str = "STANDARD"


class SkuProfitabilitySummary(BaseModel):
    """SKU-level financial margin and unit contribution record."""
    sku_id: str
    sku_name: str
    units_sold: float
    gross_revenue: float
    cogs: float
    gross_profit: float
    gross_margin_pct: float
    unit_contribution: float
    is_loss_maker: bool = False


class ARAgingBucket(BaseModel):
    """Accounts receivable aging interval metric."""
    bucket: str
    label: str
    total_amount: float
    invoice_count: int
    percent_of_total: float


class ARAgingReport(BaseModel):
    """Accounts receivable aging, exposure, and DSO telemetry."""
    tenant_id: str
    currency: str = "USD"
    total_receivables: float
    total_overdue: float
    dso_days: float
    buckets: List[ARAgingBucket]
    top_overdue_debtors: List[Dict[str, Any]] = Field(default_factory=list)


class APAgingReport(BaseModel):
    """Accounts payable aging, disbursement obligations, and DPO telemetry."""
    tenant_id: str
    currency: str = "USD"
    total_payables: float
    total_overdue: float
    dpo_days: float
    buckets: List[Dict[str, Any]] = Field(default_factory=list)
    upcoming_obligations: List[Dict[str, Any]] = Field(default_factory=list)


class WorkingCapitalSummary(BaseModel):
    """Consolidated operating working capital and Cash Conversion Cycle."""
    tenant_id: str
    currency: str = "USD"
    inventory_valuation: float
    accounts_receivable: float
    accounts_payable: float
    operating_working_capital: float
    dso_days: float
    dio_days: float
    dpo_days: float
    cash_conversion_cycle_days: float
    driver_attribution: List[Dict[str, Any]] = Field(default_factory=list)


class CashFlowForecastSummary(BaseModel):
    """Operating cash inflow and outflow projections."""
    tenant_id: str
    currency: str = "USD"
    current_cash_position: float
    expected_inflows_30d: float
    expected_outflows_30d: float
    projected_net_operating_cash_30d: float


class FinancialAnomalyFinding(BaseModel):
    """Statistical outlier or abnormal financial transaction finding."""
    anomaly_id: str = Field(default_factory=lambda: f"ANOM-FIN-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str
    domain: FinancialAnomalyDomain
    severity: str = "MEDIUM"
    title: str
    description: str
    detected_metric_value: float
    baseline_expected_value: float
    deviation_pct: float
    entity_id: str
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FinancialSummaryReport(BaseModel):
    """Master executive financial summary rollup."""
    tenant_id: str
    reporting_currency: str = "USD"
    period_key: str
    gross_revenue: float
    net_revenue: float
    cogs: float
    gross_profit: float
    gross_margin_pct: float
    operating_working_capital: float
    cash_conversion_cycle_days: float
    days_sales_outstanding: float
    days_payables_outstanding: float
    days_inventory_outstanding: float
    active_anomalies_count: int = 0
    total_receivables_overdue: float = 0.0
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
