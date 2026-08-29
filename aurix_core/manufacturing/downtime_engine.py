"""
AURIX Manufacturing & Production Intelligence — Machine Downtime & MTBF Engine
Phase 23 Core Implementation.
Analyzes machine stoppages, root cause categorization, and MTBF/MTTR reliability metrics.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.manufacturing.contracts import DowntimeAnalysisReport


class DowntimeEngine:
    """Analyzes asset stoppages and calculates Mean Time Between Failures (MTBF) and MTTR."""

    @classmethod
    def analyze_downtime(
        cls,
        tenant_id: str,
        downtime_events: List[Dict[str, Any]],
        total_operating_hours: float = 720.0,
        period_key: str = "CURRENT",
    ) -> DowntimeAnalysisReport:
        """
        MTBF = (Total Operating Time - Total Unplanned Downtime) / Total Failures
        MTTR = Total Downtime Minutes / Total Failures
        """
        total_mins = 0.0
        unplanned_mins = 0.0
        stoppages = len(downtime_events)
        reasons: Dict[str, float] = {}

        for ev in downtime_events:
            dur = float(ev.get("duration_minutes") or 0.0)
            is_planned = bool(ev.get("is_planned", False))
            reason = str(ev.get("reason_code") or "MECHANICAL_FAILURE")

            total_mins += dur
            if not is_planned:
                unplanned_mins += dur

            reasons[reason] = reasons.get(reason, 0.0) + dur

        unplanned_hrs = unplanned_mins / 60.0
        mtbf = round((max(0.0, total_operating_hours - unplanned_hrs) / max(1, stoppages)), 1)
        mttr = round((unplanned_mins / max(1, stoppages)), 1)

        top_reasons = [
            {"reason": k, "duration_minutes": v, "pct": round((v / max(1.0, total_mins)) * 100.0, 1)}
            for k, v in sorted(reasons.items(), key=lambda x: x[1], reverse=True)
        ]

        return DowntimeAnalysisReport(
            tenant_id=tenant_id,
            period_key=period_key,
            total_downtime_minutes=round(total_mins, 1),
            unplanned_downtime_minutes=round(unplanned_mins, 1),
            total_stoppages_count=stoppages,
            mtbf_hours=mtbf,
            mttr_minutes=mttr,
            top_downtime_reasons=top_reasons[:5],
        )
