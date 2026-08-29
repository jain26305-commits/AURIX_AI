"""
AURIX Deterministic Decision Engine 2.0 — Expected Value Engine
Phase 27 Core Implementation.
Computes Expected Value (EV = P(Success) * Benefit - Cost - Risk Penalty) and business value attribution.
"""

from __future__ import annotations


class ExpectedValueEngine:
    """Calculates deterministic expected value and financial risk-adjusted yield."""

    @classmethod
    def calculate_expected_value(
        cls,
        benefit_usd: float,
        cost_usd: float,
        risk_penalty_usd: float,
        probability_of_success: float = 0.90,
    ) -> float:
        """
        Expected Value = (Probability of Success * Gross Benefit) - Cost - Risk Penalty
        """
        ev = (probability_of_success * benefit_usd) - cost_usd - risk_penalty_usd
        return round(ev, 2)
