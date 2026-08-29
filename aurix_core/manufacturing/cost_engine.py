"""
AURIX Manufacturing & Production Intelligence — Production Cost Variance Engine
Phase 23 Core Implementation.
Calculates Actual vs Standard manufacturing costs (Material + Labor + Scrap Overhead).
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.manufacturing.contracts import ProductionCostVarianceReport


class ProductionCostEngine:
    """Computes Actual vs. Standard manufacturing cost variances."""

    @classmethod
    def evaluate_cost_variance(
        cls,
        tenant_id: str,
        work_orders: List[Dict[str, Any]],
        products_lookup: Dict[str, Dict[str, Any]],
        period_key: str = "CURRENT",
    ) -> ProductionCostVarianceReport:
        """
        Cost Variance = Total Actual Cost - Planned Standard Cost
        """
        planned_std = 0.0
        act_mat = 0.0
        act_labor = 0.0
        act_scrap = 0.0

        for wo in work_orders:
            sku = str(wo.get("sku_id"))
            target_qty = float(wo.get("target_quantity") or 0.0)
            completed_qty = float(wo.get("completed_quantity") or target_qty)
            scrap_qty = float(wo.get("scrap_quantity") or 0.0)

            p_info = products_lookup.get(sku, {})
            unit_cost = float(p_info.get("unit_cost") or 50.0)

            # Planned standard cost
            planned_std += target_qty * unit_cost

            # Actual material cost (including completed + scrap)
            act_mat += (completed_qty + scrap_qty) * unit_cost
            act_scrap += scrap_qty * unit_cost

            # Actual labor from run time minutes ($30/hr standard labor rate)
            run_mins = float(wo.get("actual_run_time_minutes") or (completed_qty * 5.0))
            act_labor += (run_mins / 60.0) * 30.0

        total_actual = act_mat + act_labor
        variance = round(total_actual - planned_std, 2)
        var_pct = round((variance / max(1.0, planned_std)) * 100.0, 2)

        return ProductionCostVarianceReport(
            tenant_id=tenant_id,
            period_key=period_key,
            planned_standard_cost=round(planned_std, 2),
            actual_material_cost=round(act_mat, 2),
            actual_labor_cost=round(act_labor, 2),
            actual_scrap_overhead=round(act_scrap, 2),
            total_actual_production_cost=round(total_actual, 2),
            cost_variance=variance,
            cost_variance_pct=var_pct,
        )
