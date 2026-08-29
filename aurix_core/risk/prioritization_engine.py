"""
AURIX Risk, Causal & External Intelligence — Business Impact Prioritization Engine
Phase 26 Core Implementation.
Ranks risks using multi-factor formula: Priority = Financial Impact * Prob * Urgency * Confidence * Irreversibility.
"""

from __future__ import annotations

import math
from typing import List
from aurix_core.risk.contracts import RiskFinding


class PrioritizationEngine:
    """Prioritizes operational risks mathematically to surface top management action items."""

    @classmethod
    def calculate_priority_score(cls, finding: RiskFinding) -> float:
        """
        Priority Score = Financial Impact * Probability * (1 + (1 / max(1, Urgency Hours))) * Confidence
        Scaled logarithmically for clean sorting.
        """
        urgency_factor = 1.0 + (24.0 / max(1.0, finding.urgency_hours))
        raw_score = finding.impact_amount_usd * finding.probability * urgency_factor * finding.confidence_level
        return round(raw_score, 2)

    @classmethod
    def prioritize_risks(cls, findings: List[RiskFinding]) -> List[RiskFinding]:
        """Rank all active risk findings descending by multi-factor priority score."""
        for f in findings:
            f.priority_score = cls.calculate_priority_score(f)

        findings.sort(key=lambda x: x.priority_score, reverse=True)
        return findings
