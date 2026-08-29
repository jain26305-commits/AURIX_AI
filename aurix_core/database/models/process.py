"""SQLAlchemy database models for Phase 25 Process Intelligence & OCPM."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin


class ProcessDefinitionModel(Base, TenantMixin):
    """Authoritative persistent record of tenant target workflow definitions."""

    __tablename__ = "process_definitions"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    process_type = Column(String(64), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    expected_steps_json = Column(JSON, nullable=False)
    sla_target_hours = Column(Float, nullable=False, default=72.0)
    version = Column(String(32), nullable=False, default="v1.0")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ProcessEventModel(Base, TenantMixin):
    """Normalized process event fabric log record."""

    __tablename__ = "process_events"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    process_type = Column(String(64), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    source_system = Column(String(64), nullable=False, default="AURIX_FABRIC")
    source_record_id = Column(String(128), nullable=False, index=True)
    actor = Column(String(128), nullable=True)
    location_id = Column(String(64), nullable=True)
    event_timestamp = Column(DateTime, nullable=False, index=True)
    attributes_json = Column(JSON, nullable=True)


class ProcessObjectLinkModel(Base, TenantMixin):
    """Object-Centric many-to-many relationship binding events to business entities."""

    __tablename__ = "process_object_links"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    event_id = Column(String(64), nullable=False, index=True)
    object_type = Column(String(64), nullable=False, index=True)
    object_id = Column(String(128), nullable=False, index=True)


class ProcessVariantModel(Base, TenantMixin):
    """Authoritative persistent record of discovered process execution variants."""

    __tablename__ = "process_variants"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    process_type = Column(String(64), nullable=False, index=True)
    variant_hash = Column(String(64), nullable=False, index=True)
    step_sequence_json = Column(JSON, nullable=False)
    case_count = Column(Integer, nullable=False, default=1)
    average_duration_hours = Column(Float, nullable=False, default=0.0)
    is_standard = Column(Boolean, nullable=False, default=False)


class ProcessConformanceResultModel(Base, TenantMixin):
    """Authoritative persistent record of process conformance deviations."""

    __tablename__ = "process_conformance_results"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    process_type = Column(String(64), nullable=False, index=True)
    case_id = Column(String(128), nullable=False, index=True)
    conformance_status = Column(String(64), nullable=False, index=True)
    deviations_json = Column(JSON, nullable=False)
    evaluated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ProcessSLARuleModel(Base, TenantMixin):
    """Authoritative persistent record of SLA milestone policies."""

    __tablename__ = "process_sla_rules"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    process_type = Column(String(64), nullable=False, index=True)
    start_event_type = Column(String(64), nullable=False)
    end_event_type = Column(String(64), nullable=False)
    max_duration_hours = Column(Float, nullable=False)
    severity = Column(String(32), nullable=False, default="HIGH")


class ProcessMetricSnapshotModel(Base, TenantMixin):
    """Authoritative snapshot of aggregated process performance telemetry."""

    __tablename__ = "process_metric_snapshots"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    period_key = Column(String(64), nullable=False, index=True)
    process_type = Column(String(64), nullable=False, index=True)
    median_cycle_time_hours = Column(Float, nullable=False)
    waiting_time_pct = Column(Float, nullable=False)
    rework_rate_pct = Column(Float, nullable=False)
    evaluated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
