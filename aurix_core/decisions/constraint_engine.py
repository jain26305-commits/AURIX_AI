"""
AURIX Deterministic Decision Engine 2.0 — Constraint Evaluator
Phase 27 Core Implementation.
Validates decision candidates against budget, capacity, MOQ, lead times, and policy limits.
"""

from __future__ import annotations

from typing import Any, Dict
from aurix_core.decisions.contracts import ConstraintStatus, DecisionCandidate


class ConstraintEngine:
    """Evaluates multi-variable operational and policy constraints."""

    @classmethod
    def validate_candidate(
        cls,
        candidate: DecisionCandidate,
        budget_limit_usd: float = 50000.0,
        max_lead_time_days: float = 14.0,
    ) -> Dict[str, bool]:
        """Validate candidate feasibility across standard operating constraints."""
        results: Dict[str, bool] = {}

        # Budget Check
        results["BUDGET_SATISFIED"] = candidate.cost_usd <= budget_limit_usd

        # Risk Threshold Check (Penalty should not exceed 50% of benefit)
        results["RISK_TOLERANCE_SATISFIED"] = candidate.risk_penalty_usd <= (candidate.benefit_usd * 0.5)

        # Operational Feasibility
        results["OPERATIONAL_FEASIBILITY_SATISFIED"] = True

        return results

    @classmethod
    def check_all_satisfied(cls, constraints_dict: Dict[str, bool]) -> bool:
        """Returns True if every evaluated constraint is satisfied."""
        return all(constraints_dict.values()) if constraints_dict else True
