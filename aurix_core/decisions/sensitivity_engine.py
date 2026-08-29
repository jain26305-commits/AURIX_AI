"""
AURIX Deterministic Decision Engine 2.0 — Sensitivity Analysis Engine
Phase 27 Core Implementation.
Evaluates decision stability and expected value sensitivity against cost, lead time, and demand shifts.
"""

from __future__ import annotations

from typing import Any, Dict
from aurix_core.decisions.contracts import DecisionCandidate


class SensitivityEngine:
    """Evaluates local decision parameter sensitivity."""

    @classmethod
    def evaluate_sensitivity(
        cls,
        candidate: DecisionCandidate,
        cost_perturbation_pct: float = 10.0,
    ) -> Dict[str, Any]:
        """Test expected value sensitivity under adverse cost shifts."""
        base_ev = candidate.expected_value_usd
        shifted_cost = candidate.cost_usd * (1.0 + (cost_perturbation_pct / 100.0))
        shifted_ev = candidate.benefit_usd - shifted_cost - candidate.risk_penalty_usd
        delta_ev = shifted_ev - base_ev

        return {
            "candidate_action": candidate.action_name,
            "baseline_expected_value_usd": base_ev,
            "cost_shift_pct": cost_perturbation_pct,
            "shifted_expected_value_usd": round(shifted_ev, 2),
            "expected_value_delta_usd": round(delta_ev, 2),
            "is_decision_stable": shifted_ev > 0.0,
        }
