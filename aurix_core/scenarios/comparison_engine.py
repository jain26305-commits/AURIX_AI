"""
AURIX Scenario Simulation — Scenario Comparison Engine
Phase 28 Core Implementation.
Side-by-side comparative evaluation of Scenario Alternatives vs. the Do-Nothing baseline.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.scenarios.contracts import (
    ScenarioComparisonReport,
    ScenarioResult,
)


class ScenarioComparisonEngine:
    """Compares candidate scenarios side-by-side against the Do-Nothing control baseline."""

    @classmethod
    def compare_scenarios(
        cls,
        tenant_id: str,
        baseline_result: ScenarioResult,
        candidate_results: List[ScenarioResult],
    ) -> ScenarioComparisonReport:
        """Evaluate candidate options against baseline and recommend the optimal tradeoff path."""
        all_results = [baseline_result] + candidate_results
        comparison_matrix: List[Dict[str, Any]] = []

        for res in all_results:
            comparison_matrix.append({
                "scenario_id": res.scenario_id,
                "is_baseline": res.scenario_id == baseline_result.scenario_id,
                "revenue_usd": res.simulated_revenue_usd,
                "margin_usd": res.simulated_margin_usd,
                "working_capital_usd": res.simulated_working_capital_usd,
                "risk_exposure_usd": res.simulated_risk_exposure_usd,
                "expected_value_usd": res.expected_value_usd,
                "confidence_score": res.confidence_score,
            })

        # Best option has highest Expected Value
        best = max(all_results, key=lambda x: x.expected_value_usd)

        return ScenarioComparisonReport(
            tenant_id=tenant_id,
            baseline_scenario_id=baseline_result.scenario_id,
            comparison_matrix=comparison_matrix,
            recommended_scenario_id=best.scenario_id,
            tradeoffs_explanation=f"Scenario {best.scenario_id} maximizes net Expected Value at ${best.expected_value_usd:,.2f} with risk exposure of ${best.simulated_risk_exposure_usd:,.2f}.",
        )
