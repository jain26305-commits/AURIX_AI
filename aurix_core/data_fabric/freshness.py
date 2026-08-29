"""
AURIX Enterprise Data Fabric — Data Freshness Engine
Phase 19 Core Implementation.
Calculates truthful source data freshness SLA states derived from sync checkpoints.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel

from aurix_core.data_fabric.contracts import CheckpointContract, DataFreshnessState


class FreshnessReport(BaseModel):
    """Telemetry report evaluating connector data freshness."""
    connector_id: str
    tenant_id: str
    state: DataFreshnessState
    age_seconds: float
    last_sync_at: Optional[datetime]
    sla_threshold_seconds: float
    is_within_sla: bool
    summary: str


class FreshnessEngine:
    """Computes dynamic data freshness classifications against SLA thresholds."""

    DEFAULT_SLA_SECONDS = 3600.0  # 1 hour SLA default

    @classmethod
    def calculate_freshness(
        cls,
        checkpoint: Optional[CheckpointContract],
        sla_seconds: float = DEFAULT_SLA_SECONDS,
        is_currently_syncing: bool = False,
    ) -> FreshnessReport:
        """Derive authoritative freshness classification from checkpoint telemetry."""
        now = datetime.now(timezone.utc)

        if is_currently_syncing:
            return FreshnessReport(
                connector_id=checkpoint.connector_id if checkpoint else "UNKNOWN",
                tenant_id=checkpoint.tenant_id if checkpoint else "UNKNOWN",
                state=DataFreshnessState.SYNCING,
                age_seconds=0.0,
                last_sync_at=checkpoint.last_successful_sync_at if checkpoint else None,
                sla_threshold_seconds=sla_seconds,
                is_within_sla=True,
                summary="Connector stream synchronization is currently in progress",
            )

        if not checkpoint or not checkpoint.last_successful_sync_at:
            return FreshnessReport(
                connector_id=checkpoint.connector_id if checkpoint else "UNKNOWN",
                tenant_id=checkpoint.tenant_id if checkpoint else "UNKNOWN",
                state=DataFreshnessState.OFFLINE,
                age_seconds=float("inf"),
                last_sync_at=None,
                sla_threshold_seconds=sla_seconds,
                is_within_sla=False,
                summary="Connector has never performed a successful sync",
            )

        last_sync = checkpoint.last_successful_sync_at
        if not last_sync.tzinfo:
            last_sync = last_sync.replace(tzinfo=timezone.utc)

        age_seconds = max(0.0, (now - last_sync).total_seconds())
        within_sla = age_seconds <= sla_seconds

        if age_seconds <= 900.0:  # < 15 mins
            state = DataFreshnessState.LIVE
            summary = "Data stream is LIVE (synced within last 15 minutes)"
        elif age_seconds <= sla_seconds:  # Within SLA
            state = DataFreshnessState.RECENT
            summary = f"Data is RECENT (synced {round(age_seconds / 60, 1)} minutes ago)"
        elif age_seconds <= sla_seconds * 4:  # Up to 4x SLA
            state = DataFreshnessState.DELAYED
            summary = f"Data is DELAYED beyond SLA ({round(age_seconds / 3600, 1)} hours old)"
        elif age_seconds <= 86400.0:  # Within 24 hours
            state = DataFreshnessState.STALE
            summary = f"Data is STALE ({round(age_seconds / 3600, 1)} hours since last sync)"
        elif age_seconds <= 172800.0:  # Within 48 hours
            state = DataFreshnessState.DEGRADED
            summary = "Data is DEGRADED (>24 hours old)"
        else:
            state = DataFreshnessState.OFFLINE
            summary = "Data is OFFLINE (>48 hours without successful sync)"

        return FreshnessReport(
            connector_id=checkpoint.connector_id,
            tenant_id=checkpoint.tenant_id,
            state=state,
            age_seconds=round(age_seconds, 2),
            last_sync_at=last_sync,
            sla_threshold_seconds=sla_seconds,
            is_within_sla=within_sla,
            summary=summary,
        )
