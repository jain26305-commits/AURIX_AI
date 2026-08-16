"""SQLAlchemy persistent ORM models for Phase 13 events, quarantine, and alerts."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, Index
from aurix_core.database.engine import Base


class PersistentEventModel(Base):
    """Persistent store for processed event idempotency history."""

    __tablename__ = "persistent_events"

    event_id = Column(String(64), primary_key=True, nullable=False)
    tenant_id = Column(String(64), index=True, nullable=False)
    idempotency_key = Column(String(128), index=True, nullable=False)
    status = Column(String(32), nullable=False, default="COMPLETED")
    processed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_persistent_events_tenant_idem", "tenant_id", "idempotency_key"),
    )


class PersistentQuarantineModel(Base):
    """Persistent dead-letter quarantine store for malformed or failed events."""

    __tablename__ = "persistent_quarantine"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), index=True, nullable=False)
    tenant_id = Column(String(64), index=True, nullable=False)
    source_system = Column(String(64), nullable=True)
    reason = Column(Text, nullable=False)
    payload_json = Column(Text, nullable=False)
    quarantined_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class PersistentAlertModel(Base):
    """Persistent store for operational alerts generated from events."""

    __tablename__ = "persistent_alerts"

    alert_id = Column(String(64), primary_key=True, nullable=False)
    tenant_id = Column(String(64), index=True, nullable=False)
    event_id = Column(String(64), index=True, nullable=False)
    severity = Column(String(32), nullable=False, default="MEDIUM")
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="ACTIVE")
    deduplication_key = Column(String(128), index=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_persistent_alerts_tenant_dedup", "tenant_id", "deduplication_key"),
    )