"""SQLAlchemy ORM models for Phase 9 Autonomous Discovery, Executive Intelligence, and AI Grounding."""

from datetime import datetime
from sqlalchemy import Column, DateTime, Index, String, Text
from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin


class IntelligenceRunModel(Base, TenantMixin):
    """Tracks execution runs of the Autonomous Intelligence and Orchestration pipeline."""

    __tablename__ = "intelligence_runs"

    id = Column(String(64), primary_key=True, index=True)
    dataset_hash = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="EXECUTING")  # EXECUTING, COMPLETED, PARTIAL_SUCCESS, FAILED
    configuration = Column(Text, nullable=True)  # JSON-serialized configuration
    provenance = Column(Text, nullable=True)  # JSON-serialized provenance & execution metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_intel_run_tenant_hash", "tenant_id", "dataset_hash"),
    )


class CapabilityStateModel(Base, TenantMixin):
    """Persists discovered capability availability states, readiness evaluations, and missing prerequisites."""

    __tablename__ = "capability_states"

    id = Column(String(64), primary_key=True, index=True)
    run_id = Column(String(64), nullable=False, index=True)
    capability_name = Column(String(64), nullable=False, index=True)
    domain = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False)  # AVAILABLE, PARTIAL, UNAVAILABLE, BLOCKED, WAITING_FOR_INPUT
    freshness_state = Column(String(32), nullable=False, default="LIVE")  # LIVE, RECENT, STALE, VERY_STALE, UNKNOWN
    readiness_json = Column(Text, nullable=True)  # JSON-serialized readiness dimensions (Quality, Completeness)
    missing_prerequisites_json = Column(Text, nullable=True)  # JSON-serialized list of missing fields/entities

    __table_args__ = (
        Index("idx_cap_state_tenant_run", "tenant_id", "run_id"),
        Index("idx_cap_state_tenant_name", "tenant_id", "capability_name"),
    )


class IntelligenceSnapshotModel(Base, TenantMixin):
    """Persists verified current-state intelligence snapshots across all domains for rapid AI access."""

    __tablename__ = "intelligence_snapshots"

    id = Column(String(64), primary_key=True, index=True)
    run_id = Column(String(64), nullable=False, index=True)
    snapshot_json = Column(Text, nullable=False)  # JSON-serialized structured portfolio snapshot
    summary_json = Column(Text, nullable=True)  # JSON-serialized executive KPI rollups
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_snapshot_tenant_run", "tenant_id", "run_id"),
    )


class BusinessSignalModel(Base, TenantMixin):
    """Persists business signals extracted during an intelligence run."""

    __tablename__ = "business_signals"

    id = Column(String(64), primary_key=True, index=True)
    run_id = Column(String(64), nullable=False, index=True)
    signal_type = Column(String(64), nullable=False, index=True)
    severity = Column(String(32), nullable=False, default="MODERATE")
    domain = Column(String(32), nullable=False)
    description = Column(Text, nullable=True)
    evidence_json = Column(Text, nullable=True)  # JSON-serialized evidence dictionary

    __table_args__ = (
        Index("idx_signal_tenant_run", "tenant_id", "run_id"),
    )


class PrioritizedActionModel(Base, TenantMixin):
    """Persists prioritized operational and executive actions."""

    __tablename__ = "prioritized_actions"

    id = Column(String(64), primary_key=True, index=True)
    run_id = Column(String(64), nullable=False, index=True)
    action_type = Column(String(64), nullable=False)
    priority_score = Column(String(32), nullable=False)
    urgency = Column(String(32), nullable=False)
    description = Column(Text, nullable=True)
    financial_exposure_json = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_action_tenant_run", "tenant_id", "run_id"),
    )


class ExecutiveSummaryModel(Base, TenantMixin):
    """Persists structured executive narratives and headlines."""

    __tablename__ = "executive_summaries"

    id = Column(String(64), primary_key=True, index=True)
    run_id = Column(String(64), nullable=False, index=True)
    headline = Column(Text, nullable=False)
    narrative_json = Column(Text, nullable=True)  # JSON-serialized narrative sections

    __table_args__ = (
        Index("idx_summary_tenant_run", "tenant_id", "run_id"),
    )


class ConversationModel(Base, TenantMixin):
    """Persists conversational thread sessions for grounded AI interactions."""

    __tablename__ = "conversations"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(256), nullable=True)
    active_domain = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_conversation_tenant", "tenant_id", "id"),
    )


class ConversationMessageModel(Base, TenantMixin):
    """Persists individual messages within a conversation session."""

    __tablename__ = "conversation_messages"

    id = Column(String(64), primary_key=True, index=True)
    conversation_id = Column(String(64), nullable=False, index=True)
    role = Column(String(32), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    provenance_json = Column(Text, nullable=True)  # JSON-serialized fact-pack references
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_msg_tenant_conv", "tenant_id", "conversation_id"),
    )


class AIAuditLogModel(Base, TenantMixin):
    """Audits AI requests, router classifications, provider routing, grounding validation, and token usage."""

    __tablename__ = "ai_audit_logs"

    id = Column(String(64), primary_key=True, index=True)
    conversation_id = Column(String(64), nullable=True, index=True)
    query_type = Column(String(32), nullable=False)  # READ, ANALYZE, EXPLAIN, SIMULATE, etc.
    provider_name = Column(String(64), nullable=False)  # GeminiFlashLite, GeminiFlash, Groq, Fallback
    model_name = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)  # SUCCESS, FALLBACK, REJECTED
    grounding_status = Column(String(32), nullable=False)  # VALIDATED, UNGROUNDED, DETERMINISTIC_FAST_PATH
    routing_meta_json = Column(Text, nullable=True)
    token_usage_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_ai_audit_tenant", "tenant_id", "id"),
    )