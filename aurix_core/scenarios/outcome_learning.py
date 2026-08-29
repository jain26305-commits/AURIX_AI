"""
AURIX Scenario Simulation — Outcome Learning & Attribution Engine
Phase 28 Core Implementation.
Tracks post-execution realized business value vs predicted Expected Value and decomposes prediction errors.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.scenarios.contracts import OutcomeTrackingRecord


class OutcomeLearningEngine:
    """Evaluates post-execution business value realization and tracks prediction errors."""

    @classmethod
    def record_outcome(
        cls,
        tenant_id: str,
        decision_id: str,
        action_id: str,
        predicted_ev_usd: float,
        realized_value_usd: float,
        error_cause: str = "NONE",
    ) -> OutcomeTrackingRecord:
        """
        Prediction Error = Actual Realized Value - Predicted Expected Value
        Value Realization % = (Actual / Predicted) * 100
        """
        pred_error = round(realized_value_usd - predicted_ev_usd, 2)
        realization_pct = round((realized_value_usd / max(1.0, predicted_ev_usd)) * 100.0, 1)

        return OutcomeTrackingRecord(
            tenant_id=tenant_id,
            decision_id=decision_id,
            action_id=action_id,
            predicted_value_usd=round(predicted_ev_usd, 2),
            actual_value_usd=round(realized_value_usd, 2),
            prediction_error_usd=pred_error,
            value_realization_pct=realization_pct,
            error_cause=error_cause,
        )
