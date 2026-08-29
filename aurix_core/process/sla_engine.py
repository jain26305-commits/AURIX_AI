"""
AURIX Process Intelligence — SLA & Policy Violation Engine
Phase 25 Core Implementation.
Detects time-based SLA threshold breaches across approval, delivery, and payment milestones.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.process.contracts import ProcessType, SLASeverity, SLAViolation


class SLAEngine:
    """Monitors and flags operational SLA milestone threshold breaches."""

    @classmethod
    def evaluate_slas(
        cls,
        tenant_id: str,
        case_id: str,
        milestone_name: str,
        target_hours: float,
        actual_hours: float,
        process_type: ProcessType = ProcessType.ORDER_TO_CASH,
    ) -> List[SLAViolation]:
        """Flag SLA breach if actual duration exceeds target SLA."""
        violations: List[SLAViolation] = []
        if actual_hours > target_hours:
            dev = round(actual_hours - target_hours, 1)

            # Severity classification based on actual vs target ratio
            if actual_hours >= (target_hours * 2.0):
                sev = SLASeverity.CRITICAL
            elif actual_hours >= (target_hours * 1.25):
                sev = SLASeverity.HIGH
            else:
                sev = SLASeverity.MEDIUM

            violations.append(
                SLAViolation(
                    process_type=process_type,
                    case_id=case_id,
                    milestone_name=milestone_name,
                    target_sla_hours=target_hours,
                    actual_duration_hours=actual_hours,
                    deviation_hours=dev,
                    severity=sev,
                )
            )

        return violations
