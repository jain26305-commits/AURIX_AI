"""
AURIX Scenario Simulation — Scenario Sensitivity Engine
Phase 28 Core Implementation.
Evaluates scenario outcome stability under multi-parameter perturbations (±5%, ±10%, ±20%).
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.scenarios.contracts import (
    ScenarioAssumption,
    ScenarioDefinition,
    ScenarioType,
)
from aurix_core.scenarios.scenario_engine import DeterministicScenarioEngine


class ScenarioSensitivityEngine:
    """Evaluates stability of scenario outcomes across parameter perturbation bands."""

    @classmethod
    def evaluate_sensitivity_matrix(
        cls,
        scenario: ScenarioDefinition,
        perturbations_pct: List[float] | None = None,
    ) -> List[Dict[str, Any]]:
        """Run multi-step parameter sensitivity sweeps."""
        steps = perturbations_pct or [-20.0, -10.0, 0.0, 10.0, 20.0]
        results: List[Dict[str, Any]] = []

        for p in steps:
            # Clone scenario with shifted assumptions
            shifted_assumptions = [
                ScenarioAssumption(
                    parameter_name=a.parameter_name,
                    baseline_value=a.baseline_value,
                    perturbed_value=a.baseline_value * (1.0 + (p / 100.0)),
                )
                for a in scenario.assumptions
            ]
            shifted_scn = ScenarioDefinition(
                tenant_id=scenario.tenant_id,
                scenario_type=scenario.scenario_type,
                name=f"{scenario.name} (Shift {p:+.0f}%)",
                assumptions=shifted_assumptions,
            )
            sim_res = DeterministicScenarioEngine.execute_scenario(shifted_scn)
            results.append({
                "perturbation_pct": p,
                "simulated_revenue_usd": sim_res.simulated_revenue_usd,
                "simulated_margin_usd": sim_res.simulated_margin_usd,
                "expected_value_usd": sim_res.expected_value_usd,
            })

        return results
