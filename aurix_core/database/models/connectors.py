"""Persistent database models for Enterprise ERP/WMS/TMS Connectors."""

from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ConnectorModel(Base, TenantMixin):
    __tablename__ = "connectors"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    connector_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="CONNECTED")
    deployment: Mapped[str] = mapped_column(String(128), nullable=False)
    connectivity_state: Mapped[str] = mapped_column(String(32), nullable=False, default="LIVE")

    last_sync_timestamp: Mapped[str] = mapped_column(String(64), nullable=False, default="Just now")
    next_scheduled_sync: Mapped[str] = mapped_column(String(64), nullable=False, default="in 15 minutes")
    records_synced_last_24h: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_rate_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sync_frequency: Mapped[str] = mapped_column(String(128), nullable=False)
    endpoint_masked: Mapped[str] = mapped_column(String(255), nullable=False)
    health_note: Mapped[str] = mapped_column(Text, nullable=False)
    checkpoint: Mapped[str] = mapped_column(String(128), nullable=False)

    # Phase 19 Data Fabric SLA & Drift Fields
    freshness_sla_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=3600.0)
    drift_detection_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
