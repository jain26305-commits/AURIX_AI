"""
AURIX Risk, Causal & External Intelligence — Simulation Scenario Contracts
Phase 26 Core Implementation.
Exports structured risk distribution parameters and opportunity baselines for Phase 28 scenario simulation.
"""

from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field
from aurix_core.risk.contracts import RiskFinding


class RiskScenarioContract(BaseModel):
    """Structured risk distribution payload prepared for Monte Carlo scenario engines."""
    tenant_id: str
    scenario_parameters: Dict[str, Dict[str, float]]
    active_risk_count: int
    total_exposure_usd: float


class ScenarioContractBuilder:
    """Prepares simulation-ready parameter distributions from current risk findings."""

    @classmethod
    def build_scenario_parameters(
        cls,
        tenant_id: str,
        findings: List[RiskFinding],
    ) -> RiskScenarioContract:
        """Extract disruption probability distributions by risk domain."""
        params: Dict[str, Dict[str, float]] = {}
        total_exp = sum(f.exposure_amount_usd for f in findings)

        for f in findings:
            dom = f.risk_domain.value
            if dom not in params:
                params[dom] = {"mean_probability": 0.0, "total_impact": 0.0, "count": 0}
            params[dom]["mean_probability"] += f.probability
            params[dom]["total_impact"] += f.impact_amount_usd
            params[dom]["count"] += 1

        for dom, data in params.items():
            data["mean_probability"] = round(data["mean_probability"] / max(1, data["count"]), 3)

        return RiskScenarioContract(
            tenant_id=tenant_id,
            scenario_parameters=params,
            active_risk_count=len(findings),
            total_exposure_usd=round(total_exp, 2),
        )
