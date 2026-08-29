"""SQLAlchemy database models for Phase 24 Enterprise Business Context Graph."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin


class ContextNodeModel(Base, TenantMixin):
    """Authoritative persistent record of a graph node entity."""

    __tablename__ = "context_nodes"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    entity_type = Column(String(64), nullable=False, index=True)
    canonical_id = Column(String(128), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    attributes_json = Column(JSON, nullable=True)
    source_system = Column(String(64), nullable=False, default="AURIX_FABRIC")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ContextEdgeModel(Base, TenantMixin):
    """Authoritative persistent record of an evidence-backed directed graph relationship."""

    __tablename__ = "context_edges"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    source_node_id = Column(String(64), nullable=False, index=True)
    target_node_id = Column(String(64), nullable=False, index=True)
    relationship_type = Column(String(64), nullable=False, index=True)
    confidence_level = Column(String(32), nullable=False, default="OBSERVED")
    relationship_status = Column(String(32), nullable=False, default="ACTIVE")
    weight = Column(Float, nullable=False, default=1.0)
    evidence_json = Column(JSON, nullable=True)
    effective_from = Column(DateTime, nullable=True)
    effective_to = Column(DateTime, nullable=True)


class BusinessMemoryModel(Base, TenantMixin):
    """Authoritative persistent record of institutional business memory."""

    __tablename__ = "business_memories"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    category = Column(String(64), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    context_entity_id = Column(String(128), nullable=True, index=True)
    decision_action_id = Column(String(128), nullable=True, index=True)
    outcome_status = Column(String(64), nullable=False, default="PENDING_EVALUATION")
    lessons_learned = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=False, default=1.0)
    recorded_by = Column(String(64), nullable=False, default="SYSTEM_GOVERNANCE")
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DataContractModel(Base, TenantMixin):
    """Authoritative persistent record of enterprise data contracts."""

    __tablename__ = "data_contracts"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    dataset_name = Column(String(128), nullable=False, index=True)
    schema_version = Column(String(32), nullable=False, default="v1.0")
    owner_domain = Column(String(64), nullable=False)
    freshness_slo_seconds = Column(Integer, nullable=False, default=3600)
    quality_slo_pct = Column(Float, nullable=False, default=98.0)
    consumers_json = Column(JSON, nullable=True)
    status = Column(String(32), nullable=False, default="ACTIVE")


class BusinessDNASnapshotModel(Base, TenantMixin):
    """Authoritative persistent snapshot of derived Business DNA."""

    __tablename__ = "business_dna_snapshots"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    period_key = Column(String(64), nullable=False, index=True)
    operating_model = Column(String(128), nullable=False)
    customer_concentration_hhi = Column(Float, nullable=False)
    supplier_concentration_hhi = Column(Float, nullable=False)
    inventory_intensity_pct = Column(Float, nullable=False)
    working_capital_intensity_pct = Column(Float, nullable=False)
    manufacturing_complexity_tier = Column(String(32), nullable=False)
    evaluated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
