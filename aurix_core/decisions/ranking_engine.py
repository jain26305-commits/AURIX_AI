"""
AURIX Deterministic Decision Engine 2.0 — Deterministic Ranking Engine
Phase 27 Core Implementation.
Ranks decision alternatives using explainable mathematical utility and constraint satisfaction scores.
"""

from __future__ import annotations

from typing import List
from aurix_core.decisions.contracts import DecisionCandidate


class RankingEngine:
    """Evaluates and ranks decision alternatives deterministically."""

    @classmethod
    def calculate_utility(cls, candidate: DecisionCandidate) -> float:
        """
        Utility = Expected Value - (Cost * 0.2) - (Risk Penalty * 0.5)
        """
        utility = candidate.expected_value_usd - (candidate.cost_usd * 0.2) - (candidate.risk_penalty_usd * 0.5)
        return round(utility, 2)

    @classmethod
    def rank_candidates(cls, candidates: List[DecisionCandidate]) -> List[DecisionCandidate]:
        """Rank candidates descending by utility score."""
        for c in candidates:
            if c.utility_score == 0.0:
                c.utility_score = cls.calculate_utility(c)

        candidates.sort(key=lambda x: x.utility_score, reverse=True)
        return candidates
