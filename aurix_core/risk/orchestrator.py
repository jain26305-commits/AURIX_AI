"""
AURIX Risk, Causal & External Intelligence — Master Risk Orchestrator
Phase 26 Core Implementation.
Coordinates multi-domain risk evaluation, signal ingestion, opportunity ranking, and panoramic summary caching.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from aurix_core.risk.contracts import (
    RiskFinding,
    RiskSummaryReport,
)
from aurix_core.risk.coverage_engine import RiskCoverageEngine
from aurix_core.risk.exposure_engine import ExposureEngine
from aurix_core.risk.opportunity_engine import OpportunityEngine
from aurix_core.risk.prioritization_engine import PrioritizationEngine
from aurix_core.risk.risk_engine import RiskEngine

logger = logging.getLogger("aurix.risk.orchestrator")


class RiskOrchestrator:
    """Master risk and opportunity intelligence coordinator."""

    _summary_cache: Dict[str, RiskSummaryReport] = {}

    @classmethod
    def run_risk_sweep(
        cls,
        tenant_id: str,
        suppliers: List[Dict[str, Any]],
        customers: List[Dict[str, Any]],
        inventory_items: List[Dict[str, Any]],
        work_orders: List[Dict[str, Any]],
        invoices: List[Dict[str, Any]],
        assurance_findings: List[Dict[str, Any]],
        process_bottlenecks: List[Dict[str, Any]],
        external_signals: Optional[List[Any]] = None,
        period_key: str = "CURRENT",
    ) -> RiskSummaryReport:
        """Execute comprehensive panoramic enterprise risk and opportunity sweep."""
        # 1. Evaluate Core Risks
        raw_findings = RiskEngine.evaluate_risks(
            tenant_id=tenant_id,
            suppliers=suppliers,
            customers=customers,
            inventory_items=inventory_items,
            work_orders=work_orders,
            assurance_findings=assurance_findings,
            process_bottlenecks=process_bottlenecks,
        )

        # 2. Prioritize Findings
        prioritized_findings = PrioritizationEngine.prioritize_risks(raw_findings)
        critical_count = len([f for f in prioritized_findings if f.priority_score > 5000.0])

        # 3. Rollup Exposures
        exposure_data = ExposureEngine.rollup_exposures(tenant_id, prioritized_findings)

        # 4. Discover Opportunities
        opportunities = OpportunityEngine.detect_opportunities(
            tenant_id=tenant_id,
            purchase_orders=[],
            inventory_items=inventory_items,
            invoices=invoices,
        )
        total_opp_val = sum(o.potential_value_usd for o in opportunities)

        # 5. Coverage Assessment
        coverage = RiskCoverageEngine.evaluate_coverage(
            tenant_id=tenant_id,
            suppliers_count=len(suppliers),
            customers_count=len(customers),
            work_orders_count=len(work_orders),
            process_events_count=50,
            external_signals_count=len(external_signals or []),
        )

        summary = RiskSummaryReport(
            tenant_id=tenant_id,
            period_key=period_key,
            total_active_risks_count=len(prioritized_findings),
            total_exposure_usd=exposure_data["total_gross_impact_usd"],
            total_expected_loss_usd=exposure_data["total_expected_loss_usd"],
            critical_priorities_count=critical_count,
            top_risk_domain=exposure_data["top_risk_domain"],
            active_opportunities_count=len(opportunities),
            total_opportunity_value_usd=round(total_opp_val, 2),
            active_external_signals_count=len(external_signals or []),
            overall_risk_coverage_pct=coverage.overall_coverage_pct,
        )

        cls._summary_cache[tenant_id] = summary
        return summary
