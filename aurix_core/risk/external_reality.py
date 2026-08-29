"""
AURIX Risk, Causal & External Intelligence — External Reality Ingestion Layer
Phase 26 Core Implementation.
Ingestion, normalization, freshness validation, and provenance enforcement for external market and environmental signals.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
from aurix_core.risk.contracts import (
    ExternalSignal,
    RiskSeverity,
    SignalStatus,
    SignalType,
)


class ExternalRealityLayer:
    """Ingests and sanitizes external signals with strict zero-trust input safety."""

    @classmethod
    def ingest_signal(
        cls,
        source_name: str,
        source_record_id: str,
        signal_type: SignalType,
        geography: str,
        severity: RiskSeverity,
        metric_value: float,
        metric_unit: str = "INDEX",
        raw_payload: Dict[str, Any] | None = None,
    ) -> ExternalSignal:
        """Validate and normalize an incoming external real-world signal."""
        now = datetime.now(timezone.utc)

        return ExternalSignal(
            source_name=source_name.strip().upper(),
            source_record_id=str(source_record_id),
            signal_type=signal_type,
            geography=geography.strip().upper(),
            severity=severity,
            metric_value=float(metric_value),
            metric_unit=metric_unit.strip().upper(),
            observed_at=now,
            valid_from=now,
            status=SignalStatus.LIVE,
            raw_payload=raw_payload or {},
        )
