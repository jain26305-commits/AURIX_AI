"""
AURIX Business Finance Intelligence — Master Finance Orchestrator
Phase 21 Core Implementation.
Coordinates P&L, Margin, Profitability, AR/AP, Working Capital, CCC, and Anomalies.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
from aurix_core.finance.anomaly_engine import FinancialAnomalyEngine
from aurix_core.finance.ap_engine import APEngine
from aurix_core.finance.ar_engine import AREngine
from aurix_core.finance.config import FinanceConfigManager
from aurix_core.finance.contracts import (
    FinancialSummaryReport,
    PnLStatement,
)
from aurix_core.finance.margin_engine import MarginEngine
from aurix_core.finance.profitability_engine import ProfitabilityEngine
from aurix_core.finance.revenue_engine import RevenueEngine
from aurix_core.finance.working_capital_engine import WorkingCapitalEngine

logger = logging.getLogger("aurix.finance.orchestrator")


class FinanceOrchestrator:
    """Master financial intelligence coordinator for AURIX Enterprise."""

    _summary_cache: Dict[str, FinancialSummaryReport] = {}

    @classmethod
    def run_financial_analysis(
        cls,
        tenant_id: str,
        orders: List[Dict[str, Any]],
        invoices: List[Dict[str, Any]],
        payments: List[Dict[str, Any]],
        products: List[Dict[str, Any]],
        inventory_positions: List[Dict[str, Any]],
        customers: Optional[List[Dict[str, Any]]] = None,
        period_key: str = "CURRENT",
    ) -> FinancialSummaryReport:
        """Execute end-to-end multi-dimensional financial intelligence sweep."""
        config = FinanceConfigManager.get_config(tenant_id)

        # 1. Revenue Intelligence
        rev_breakdown = RevenueEngine.calculate_revenue(
            tenant_id=tenant_id,
            orders=orders,
            invoices=invoices,
            period_key=period_key,
            currency=config.reporting_currency,
        )

        # 2. Total COGS & Inventory Valuation
        prod_cost_map = {str(p.get("id")): float(p.get("unit_cost") or 0.0) for p in products}
        total_cogs = sum(float(line.get("quantity") or 1.0) * prod_cost_map.get(str(line.get("sku_id")), 10.0) for line in orders)
        inv_valuation = sum(float(pos.get("on_hand") or 0.0) * prod_cost_map.get(str(pos.get("sku_id")), 10.0) for pos in inventory_positions)

        # 3. Margin Intelligence
        margin_summary = MarginEngine.calculate_margin(
            tenant_id=tenant_id,
            net_revenue=rev_breakdown.net_revenue,
            cogs=total_cogs,
        )

        # 4. AR & AP Aging
        ar_report = AREngine.calculate_ar_aging(
            tenant_id=tenant_id,
            invoices=invoices,
            annual_revenue=rev_breakdown.net_revenue,
            currency=config.reporting_currency,
        )
        ap_report = APEngine.calculate_ap_aging(
            tenant_id=tenant_id,
            invoices=invoices,
            annual_cogs=total_cogs,
            currency=config.reporting_currency,
        )

        # 5. Working Capital & CCC
        wc_summary = WorkingCapitalEngine.calculate_working_capital(
            tenant_id=tenant_id,
            inventory_valuation=inv_valuation,
            accounts_receivable=ar_report.total_receivables,
            accounts_payable=ap_report.total_payables,
            annual_revenue=rev_breakdown.net_revenue,
            annual_cogs=total_cogs,
            currency=config.reporting_currency,
        )

        # 6. Anomaly Detection
        anomalies = FinancialAnomalyEngine.audit_transactions(tenant_id, invoices)

        # Master Summary Rollup
        summary = FinancialSummaryReport(
            tenant_id=tenant_id,
            reporting_currency=config.reporting_currency,
            period_key=period_key,
            gross_revenue=rev_breakdown.gross_revenue,
            net_revenue=rev_breakdown.net_revenue,
            cogs=round(total_cogs, 2),
            gross_profit=margin_summary.gross_profit,
            gross_margin_pct=margin_summary.gross_margin_pct,
            operating_working_capital=wc_summary.operating_working_capital,
            cash_conversion_cycle_days=wc_summary.cash_conversion_cycle_days,
            days_sales_outstanding=wc_summary.dso_days,
            days_payables_outstanding=wc_summary.dpo_days,
            days_inventory_outstanding=wc_summary.dio_days,
            active_anomalies_count=len(anomalies),
            total_receivables_overdue=ar_report.total_overdue,
        )

        cls._summary_cache[tenant_id] = summary
        return summary
