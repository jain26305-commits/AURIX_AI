"""Database models for tracking the lifecycle of data ingestion runs."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin


class IngestionRun(Base, TenantMixin):
    """
    Persistent representation of an operational data ingestion event.
    Tracks provenance, status, and dataset hashing for idempotency.
    """

    __tablename__ = "ingestion_runs"

    id = Column(String(64), primary_key=True, index=True)
    source_name = Column(String(255), nullable=False)
    domain = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="RECEIVED")
    data_hash = Column(String(128), nullable=False, index=True)

    record_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    validation_summary = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)


class OnboardingQuarantineRecord(Base, TenantMixin):
    """Tenant-scoped immutable record of onboarding rows rejected by validation."""

    __tablename__ = "onboarding_quarantine"

    id = Column(String(64), primary_key=True, index=True)
    run_id = Column(String(64), nullable=False, index=True)
    row_hash = Column(String(128), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    payload_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
