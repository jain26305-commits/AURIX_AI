"""SQLAlchemy database models for Phase 26 Risk, Causal & External Intelligence."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin


class RiskFindingModel(Base, TenantMixin):
    """Authoritative persistent record of an enterprise risk finding."""

    __tablename__ = "risk_findings"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    risk_domain = Column(String(64), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(128), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    probability = Column(Float, nullable=False, default=0.5)
    impact_amount = Column(Float, nullable=False, default=0.0)
    exposure_amount = Column(Float, nullable=False, default=0.0)
    priority_score = Column(Float, nullable=False, default=0.0, index=True)
    urgency_hours = Column(Float, nullable=False, default=24.0)
    confidence_level = Column(Float, nullable=False, default=0.9)
    status = Column(String(32), nullable=False, default="ACTIVE", index=True)
    evidence_json = Column(JSON, nullable=True)
    first_detected = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_to = Column(DateTime, nullable=True)


class ExternalSignalModel(Base):
    """Global external reality event or market indicator feed record."""

    __tablename__ = "external_signals"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    source_name = Column(String(128), nullable=False, index=True)
    source_record_id = Column(String(128), nullable=False, index=True)
    signal_type = Column(String(64), nullable=False, index=True)
    geography = Column(String(64), nullable=False, index=True)
    severity = Column(String(32), nullable=False, default="MEDIUM")
    confidence = Column(Float, nullable=False, default=0.95)
    metric_value = Column(Float, nullable=False, default=0.0)
    metric_unit = Column(String(32), nullable=False, default="INDEX")
    currency = Column(String(16), nullable=False, default="USD")
    observed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    valid_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_to = Column(DateTime, nullable=True)
    raw_payload_json = Column(JSON, nullable=True)


class ExternalSignalMappingModel(Base, TenantMixin):
    """Tenant-scoped binding connecting external signals to internal enterprise entities."""

    __tablename__ = "external_signal_mappings"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    signal_id = Column(String(64), ForeignKey("external_signals.id"), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(128), nullable=False, index=True)
    mapping_rule = Column(String(128), nullable=False)
    confidence = Column(Float, nullable=False, default=0.9)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class OpportunityFindingModel(Base, TenantMixin):
    """Authoritative persistent record of an identified operational or financial upside opportunity."""

    __tablename__ = "opportunity_findings"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    opportunity_type = Column(String(64), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(128), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    potential_value_usd = Column(Float, nullable=False, default=0.0, index=True)
    probability = Column(Float, nullable=False, default=0.85)
    confidence = Column(Float, nullable=False, default=0.9)
    priority_rank = Column(Integer, nullable=False, default=1)
    evidence_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CausalEvidenceModel(Base, TenantMixin):
    """Authoritative persistent record of evidence-backed causal classifications."""

    __tablename__ = "causal_evidence_records"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    cause_entity_id = Column(String(128), nullable=False, index=True)
    effect_entity_id = Column(String(128), nullable=False, index=True)
    relationship_classification = Column(String(64), nullable=False, index=True)
    methodology = Column(String(128), nullable=False)
    confidence_score = Column(Float, nullable=False, default=0.95)
    confounders_json = Column(JSON, nullable=True)
    evidence_json = Column(JSON, nullable=True)
    evaluated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
