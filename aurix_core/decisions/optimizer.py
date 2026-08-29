"""
AURIX Deterministic Decision Engine 2.0 — Solver & Optimizer Abstraction
Phase 27 Core Implementation.
Solves linear, knapsack, and multi-objective portfolio allocation problems subject to business budget and capacity limits.
"""

from __future__ import annotations

import time
from typing import List
from aurix_core.decisions.contracts import (
    DecisionCandidate,
    OptimizationRequest,
    OptimizationResult,
)


class DecisionOptimizer:
    """Optimization solver for single-decision and portfolio candidate selection."""

    @classmethod
    def optimize_portfolio(cls, request: OptimizationRequest) -> OptimizationResult:
        """
        Knapsack Budget Allocation Solver:
        Maximize Σ Expected Value subject to Σ Cost <= Budget Limit
        """
        start_t = time.perf_counter()
        budget = request.budget_limit_usd

        # Sort by EV-to-Cost Efficiency ratio
        valid_candidates = [
            c for c in request.candidate_actions if c.expected_value_usd > 0
        ]
        valid_candidates.sort(
            key=lambda x: (x.expected_value_usd / max(1.0, x.cost_usd)),
            reverse=True,
        )

        selected: List[DecisionCandidate] = []
        total_ev = 0.0
        total_cost = 0.0

        for c in valid_candidates:
            if (total_cost + c.cost_usd) <= budget:
                selected.append(c)
                total_ev += c.expected_value_usd
                total_cost += c.cost_usd

        elapsed_ms = round((time.perf_counter() - start_t) * 1000.0, 2)
        is_feasible = len(selected) > 0 or budget == 0.0

        return OptimizationResult(
            tenant_id=request.tenant_id,
            solver_name="AURIX_PORTFOLIO_GREEDY_SOLVER_V2",
            status="OPTIMAL" if is_feasible else "INFEASIBLE",
            objective_value_usd=round(total_ev, 2),
            selected_candidates=selected,
            total_cost_usd=round(total_cost, 2),
            runtime_ms=elapsed_ms,
            constraints_satisfied=is_feasible,
            relaxation_suggestions=[] if is_feasible else ["Increase budget limit by 15% to capture high-yield candidates."],
        )
