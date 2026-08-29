"""
AURIX Process Intelligence — Process-to-Business Impact Engine
Phase 25 Core Implementation.
Quantifies financial and commercial exposure resulting from process latency, rework, and bottleneck friction.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.process.contracts import ProcessBusinessImpact, ProcessType


class ProcessImpactEngine:
    """Translates process inefficiencies into balance sheet, P&L, and customer impact."""

    @classmethod
    def quantify_impact(
        cls,
        tenant_id: str,
        process_type: ProcessType,
        avg_cycle_days: float,
        benchmark_days: float = 30.0,
        annual_revenue: float = 1200000.0,
    ) -> ProcessBusinessImpact:
        """
        Quantify financial drag:
        - DSO Inflation = max(0, avg_cycle_days - benchmark_days)
        - Working Capital Drag = (DSO Inflation / 365) * Annual Revenue
        """
        dso_drag = max(0.0, round(avg_cycle_days - benchmark_days, 1))
        wc_friction = round((dso_drag / 365.0) * annual_revenue, 2)
        otif_penalty = min(25.0, round(dso_drag * 1.5, 1))

        return ProcessBusinessImpact(
            tenant_id=tenant_id,
            process_type=process_type,
            dso_inflation_days=dso_drag,
            working_capital_friction_usd=wc_friction,
            scrap_cost_loss_usd=4500.0,
            commercial_revenue_at_risk_usd=round(wc_friction * 0.6, 2),
            otif_penalty_pct=otif_penalty,
            impact_summary=f"Process latency contributes {dso_drag} days DSO drag and ${wc_friction:,.2f} working capital tie-up.",
        )
