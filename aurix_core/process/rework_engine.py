"""
AURIX Process Intelligence — Rework & Loop Detection Engine
Phase 25 Core Implementation.
Detects repetitive loops (A -> B -> A or Review -> Reject -> Review) and quantifies wasted time and cost.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.process.contracts import ProcessType, ReworkLoop


class ReworkEngine:
    """Detects repeating execution loops and calculates wasted operational effort."""

    @classmethod
    def detect_rework_loops(
        cls,
        case_id: str,
        step_sequence: List[str],
        process_type: ProcessType = ProcessType.ORDER_TO_CASH,
        hourly_cost_rate: float = 45.0,
    ) -> List[ReworkLoop]:
        """Identify repeated steps within an individual case execution sequence."""
        loops: List[ReworkLoop] = []
        step_counts: Dict[str, int] = {}

        for s in step_sequence:
            step_counts[s] = step_counts.get(s, 0) + 1

        for step, count in step_counts.items():
            if count > 1:
                wasted_hrs = round((count - 1) * 4.0, 1)
                cost = round(wasted_hrs * hourly_cost_rate, 2)

                loops.append(
                    ReworkLoop(
                        process_type=process_type,
                        case_id=case_id,
                        loop_steps=[step],
                        iterations_count=count,
                        total_wasted_hours=wasted_hrs,
                        estimated_cost_waste=cost,
                    )
                )

        return loops
