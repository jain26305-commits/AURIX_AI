"""Action prioritization engine for Phase 9 Executive Intelligence."""

import uuid
from typing import Dict, List, Optional
from aurix_core.intelligence.config import IntelligenceConfiguration
from aurix_core.schema.phase5_contract import TrackedValue, ValueState
from aurix_core.schema.phase11_contract import (
    BusinessSignal,
    PrioritizedAction,
    SignalSeverity,
)


class ActionPrioritizer:
    """Ranks and prioritizes business actions using deterministic multi-dimensional scoring."""

    _SEVERITY_SCORE_MAP: Dict[SignalSeverity, float] = {
        SignalSeverity.CRITICAL: 1.0,
        SignalSeverity.HIGH: 0.8,
        SignalSeverity.MODERATE: 0.5,
        SignalSeverity.LOW: 0.2,
        SignalSeverity.INFO: 0.1,
    }

    _CURRENCY_BASELINE_MAP: Dict[str, float] = {
        "USD": 100000.0,
        "EUR": 90000.0,
        "GBP": 80000.0,
        "INR": 8000000.0,
        "CAD": 130000.0,
        "AUD": 140000.0,
    }

    @classmethod
    def prioritize_signals(
        cls,
        signals: List[BusinessSignal],
        config: Optional[IntelligenceConfiguration] = None,
    ) -> List[PrioritizedAction]:
        """Converts business signals into ranked PrioritizedAction instances."""
        cfg = config or IntelligenceConfiguration()
        if not signals:
            return []

        scored_actions: List[PrioritizedAction] = []

        for sig in signals:
            act_id = f"ACT-{uuid.uuid4().hex[:8]}"

            # 1. Severity Score component
            sev_score = cls._SEVERITY_SCORE_MAP.get(sig.severity, 0.1)

            # 2. Financial Exposure Score component & Currency Scaling
            has_valid_fin = (
                sig.financial_exposure is not None
                and sig.financial_exposure.value is not None
                and sig.financial_exposure.state != ValueState.UNAVAILABLE
            )

            if has_valid_fin and sig.financial_exposure is not None and sig.financial_exposure.value is not None:
                fin_val = float(sig.financial_exposure.value)
                curr_str = str(sig.provenance.get("currency", "USD")).upper().strip()
                baseline = cls._CURRENCY_BASELINE_MAP.get(curr_str, 100000.0)
                fin_score = min(1.0, max(0.0, fin_val / baseline))
                fin_impact_tv = sig.financial_exposure
            else:
                fin_score = 0.0
                fin_impact_tv = TrackedValue(
                    value=None,
                    state=ValueState.UNAVAILABLE,
                    source="UNAVAILABLE_FINANCIAL_EXPOSURE",
                )

            # 3. Operational Urgency Score component
            urgency_score = cls._SEVERITY_SCORE_MAP.get(sig.severity, 0.4)

            # 4. Service Impact Score component
            svc_metric = sig.source_metrics.get("service_level_change") or sig.source_metrics.get("stockout_risk")
            if svc_metric and svc_metric.value is not None:
                service_score = min(1.0, max(0.0, abs(float(svc_metric.value))))
            else:
                service_score = 0.5

            # Multi-dimensional Weighted Score Calculation
            raw_composite = (
                (sev_score * cfg.severity_weight)
                + (fin_score * cfg.financial_exposure_weight)
                + (urgency_score * cfg.operational_urgency_weight)
                + (service_score * cfg.service_impact_weight)
            )
            composite_score = round(min(1.0, max(0.0, raw_composite)), 4)

            rec_id = sig.provenance.get("recommendation_id") if sig.provenance else None

            scored_actions.append(
                PrioritizedAction(
                    action_id=act_id,
                    rank=0,
                    title=f"Address {sig.signal_type.replace('_', ' ').title()}",
                    description=sig.description,
                    domain=sig.domain,
                    priority_score=composite_score,
                    financial_impact=fin_impact_tv,
                    operational_impact=None,
                    risk_level=sig.severity.value,
                    underlying_signal_ids=[sig.signal_id],
                    recommended_decision_id=str(rec_id) if rec_id else None,
                )
            )

        # Sort descending by priority_score, breaking ties deterministically by title and action_id
        scored_actions.sort(key=lambda a: (-a.priority_score, a.title, a.action_id))

        # Assign 1-based ranks and cap to max_prioritized_actions
        final_actions: List[PrioritizedAction] = []
        for idx, act in enumerate(scored_actions[: cfg.max_prioritized_actions], start=1):
            act.rank = idx
            final_actions.append(act)

        return final_actions