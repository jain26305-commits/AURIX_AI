"""
AURIX Manufacturing & Production Intelligence — Quality, Yield & Scrap Engine
Phase 23 Core Implementation.
Calculates First-Pass Yield, Scrap Rates, Defect Pareto, and Scrap Loss Cost.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.manufacturing.contracts import QualityYieldSummary


class QualityEngine:
    """Calculates manufacturing quality yield, scrap rate, and financial scrap leakage."""

    @classmethod
    def evaluate_quality(
        cls,
        tenant_id: str,
        production_events: List[Dict[str, Any]],
        unit_scrap_cost: float = 25.0,
        period_key: str = "CURRENT",
    ) -> QualityYieldSummary:
        """
        First-Pass Yield = (Good Units / Total Units) * 100
        Scrap Rate = (Scrap Units / Total Units) * 100
        """
        total_produced = 0.0
        good_units = 0.0
        scrap_units = 0.0
        rework_units = 0.0
        reasons: Dict[str, float] = {}

        for ev in production_events:
            qty = float(ev.get("quantity") or 0.0)
            good = float(ev.get("good_quantity") or qty)
            scrap = float(ev.get("scrap_quantity") or 0.0)
            reason = str(ev.get("reason_code") or "GENERAL_DEFECT")

            total_produced += qty
            good_units += good
            scrap_units += scrap

            if scrap > 0:
                reasons[reason] = reasons.get(reason, 0.0) + scrap

        fpy = round((good_units / max(1.0, total_produced)) * 100.0, 2)
        scrap_rate = round((scrap_units / max(1.0, total_produced)) * 100.0, 2)
        scrap_cost = round(scrap_units * unit_scrap_cost, 2)

        return QualityYieldSummary(
            tenant_id=tenant_id,
            period_key=period_key,
            total_units_produced=total_produced,
            good_units_produced=good_units,
            scrap_units=scrap_units,
            rework_units=rework_units,
            first_pass_yield_pct=min(100.0, fpy),
            scrap_rate_pct=scrap_rate,
            total_scrap_cost_loss=scrap_cost,
            defect_reasons_breakdown=reasons,
        )
