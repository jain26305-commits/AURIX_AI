"""
AURIX Scenario Simulation — Deterministic Scenario Engine
Phase 28 Core Implementation.
Executes multi-domain scenario simulations (Demand Shock, Supplier Delay, Cost Shift) without mutating production state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
from aurix_core.scenarios.contracts import (
    ScenarioAssumption,
    ScenarioDefinition,
    ScenarioResult,
    ScenarioType,
)


class DeterministicScenarioEngine:
    """Simulates multi-domain operational consequences deterministically."""

    @classmethod
    def execute_scenario(
        cls,
        scenario: ScenarioDefinition,
        baseline_revenue: float = 500000.0,
        baseline_margin: float = 120000.0,
        baseline_working_capital: float = 150000.0,
        baseline_risk_exposure: float = 45000.0,
    ) -> ScenarioResult:
        """
        Replay deterministic domain formulas with scenario perturbations applied.
        State Isolation: Pure in-memory computation; live database is never mutated.
        """
        sim_rev = baseline_revenue
        sim_mar = baseline_margin
        sim_wc = baseline_working_capital
        sim_risk = baseline_risk_exposure

        for a in scenario.assumptions:
            p_name = a.parameter_name.upper()
            delta_pct = (a.perturbed_value - a.baseline_value) / max(1.0, abs(a.baseline_value))

            if "DEMAND" in p_name:
                sim_rev = baseline_revenue * (1.0 + delta_pct)
                sim_mar = baseline_margin * (1.0 + (delta_pct * 1.15))
                sim_wc = baseline_working_capital * (1.0 + (delta_pct * 0.5))
            elif "LEAD_TIME" in p_name or "DELAY" in p_name:
                # Lead time increase ties up inventory and increases risk
                sim_wc = baseline_working_capital * (1.0 + (delta_pct * 0.4))
                sim_risk = baseline_risk_exposure * (1.0 + (delta_pct * 1.5))
                sim_mar = baseline_margin - (sim_risk * 0.2)
            elif "COST" in p_name:
                sim_mar = baseline_margin * (1.0 - (delta_pct * 0.8))
                sim_wc = baseline_working_capital * (1.0 + (delta_pct * 0.3))

        ev = (sim_mar - baseline_margin) - (sim_risk - baseline_risk_exposure) * 0.5

        return ScenarioResult(
            tenant_id=scenario.tenant_id,
            scenario_id=scenario.scenario_id,
            simulated_revenue_usd=round(sim_rev, 2),
            simulated_margin_usd=round(sim_mar, 2),
            simulated_working_capital_usd=round(sim_wc, 2),
            simulated_risk_exposure_usd=round(sim_risk, 2),
            expected_value_usd=round(ev, 2),
            confidence_score=0.92,
            p50_usd=round(ev, 2),
            p80_usd=round(ev * 0.85, 2),
            p90_usd=round(ev * 0.70, 2),
            tradeoffs_summary={
                "revenue_delta_usd": round(sim_rev - baseline_revenue, 2),
                "margin_delta_usd": round(sim_mar - baseline_margin, 2),
                "working_capital_delta_usd": round(sim_wc - baseline_working_capital, 2),
                "risk_exposure_delta_usd": round(sim_risk - baseline_risk_exposure, 2),
            },
        )
