"""
AURIX Business Finance Intelligence Package Initialization
"""

from aurix_core.finance.contracts import (
    APAgingReport,
    ARAgingBucket,
    ARAgingReport,
    CashFlowForecastSummary,
    CustomerProfitabilitySummary,
    DataAvailabilityStatus,
    FinancialAnomalyDomain,
    FinancialAnomalyFinding,
    FinancialSummaryReport,
    FiscalPeriodType,
    MarginSummary,
    PnLStatement,
    RevenueBreakdown,
    SkuProfitabilitySummary,
    WorkingCapitalSummary,
)

__all__ = [
    "DataAvailabilityStatus",
    "FiscalPeriodType",
    "FinancialAnomalyDomain",
    "PnLStatement",
    "RevenueBreakdown",
    "MarginSummary",
    "CustomerProfitabilitySummary",
    "SkuProfitabilitySummary",
    "ARAgingBucket",
    "ARAgingReport",
    "APAgingReport",
    "WorkingCapitalSummary",
    "CashFlowForecastSummary",
    "FinancialAnomalyFinding",
    "FinancialSummaryReport",
]
