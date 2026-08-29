"""
AURIX Process Intelligence — Process Conformance Engine
Phase 25 Core Implementation.
Compares actual execution sequences against expected workflow graphs to detect skipped, inverted, or unauthorized steps.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.process.contracts import ConformanceStatus, ConformanceViolation, ProcessType


class ConformanceEngine:
    """Audits process conformance against tenant-defined expected workflow paths."""

    _STANDARD_O2C_PATH = [
        "ORDER_PLACED",
        "CREDIT_CHECK_APPROVED",
        "INVENTORY_ALLOCATED",
        "GOODS_DISPATCHED",
        "INVOICE_ISSUED",
        "PAYMENT_SETTLED",
    ]

    @classmethod
    def audit_conformance(
        cls,
        tenant_id: str,
        case_id: str,
        actual_sequence: List[str],
        expected_sequence: List[str] | None = None,
        process_type: ProcessType = ProcessType.ORDER_TO_CASH,
    ) -> List[ConformanceViolation]:
        """Detect skipped steps or sequence inversions."""
        expected = expected_sequence or cls._STANDARD_O2C_PATH
        violations: List[ConformanceViolation] = []

        # Check for skipped critical steps
        for expected_step in expected:
            if expected_step not in actual_sequence:
                violations.append(
                    ConformanceViolation(
                        process_type=process_type,
                        case_id=case_id,
                        conformance_status=ConformanceStatus.SKIPPED_STEP,
                        title=f"Skipped Step: {expected_step}",
                        description=f"Process case {case_id} skipped mandatory step {expected_step}.",
                        expected_sequence=expected,
                        actual_sequence=actual_sequence,
                    )
                )

        # Check sequence order
        if len(actual_sequence) >= 2:
            indices = [expected.index(s) for s in actual_sequence if s in expected]
            if indices != sorted(indices):
                violations.append(
                    ConformanceViolation(
                        process_type=process_type,
                        case_id=case_id,
                        conformance_status=ConformanceStatus.WRONG_SEQUENCE,
                        title="Sequence Inversion Detected",
                        description=f"Actual step order {actual_sequence} violates expected order.",
                        expected_sequence=expected,
                        actual_sequence=actual_sequence,
                    )
                )

        return violations
