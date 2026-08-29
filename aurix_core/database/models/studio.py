"""SQLAlchemy database models for Phase 30 Enterprise Agent Studio & Workflow Orchestration."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from aurix_core.database.engine import Base
from aurix_core.database.models.base import TenantMixin


class StudioAgentModel(Base, TenantMixin):
    """Authoritative persistent record of Agent Studio definitions."""

    __tablename__ = "studio_agents"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    business_purpose = Column(Text, nullable=False, default="")
    domain = Column(String(64), nullable=False, default="SUPPLY_CHAIN")
    owner = Column(String(128), nullable=False, default="ADMIN")
    agent_type = Column(String(64), nullable=False, default="PROCUREMENT_AGENT")
    version = Column(String(32), nullable=False, default="1.0.0")
    status = Column(String(32), nullable=False, default="DRAFT", index=True)
    allowed_skills_json = Column(JSON, nullable=True)
    allowed_tools_json = Column(JSON, nullable=True)
    context_domains_json = Column(JSON, nullable=True)
    risk_classification = Column(String(32), nullable=False, default="MEDIUM")
    max_steps = Column(Integer, nullable=False, default=10)
    budget_limit_usd = Column(Float, nullable=False, default=1000.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class StudioAgentVersionModel(Base, TenantMixin):
    """Immutable published version snapshot records."""

    __tablename__ = "studio_agent_versions"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    agent_id = Column(String(64), ForeignKey("studio_agents.id"), nullable=False, index=True)
    version_number = Column(String(32), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="PUBLISHED")
    config_snapshot_json = Column(JSON, nullable=False)
    published_by = Column(String(128), nullable=False)
    change_summary = Column(Text, nullable=True)
    published_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class StudioWorkflowModel(Base, TenantMixin):
    """Authoritative visual workflow graph definitions."""

    __tablename__ = "studio_workflows"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    version = Column(String(32), nullable=False, default="1.0.0")
    status = Column(String(32), nullable=False, default="DRAFT")
    triggers_json = Column(JSON, nullable=True)
    nodes_json = Column(JSON, nullable=True)
    edges_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class StudioWorkflowVersionModel(Base, TenantMixin):
    """Immutable visual workflow graph version snapshots."""

    __tablename__ = "studio_workflow_versions"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    workflow_id = Column(String(64), ForeignKey("studio_workflows.id"), nullable=False, index=True)
    version_number = Column(String(32), nullable=False)
    nodes_json = Column(JSON, nullable=False)
    edges_json = Column(JSON, nullable=False)
    published_by = Column(String(128), nullable=False)
    published_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class StudioDeploymentModel(Base, TenantMixin):
    """Deployment promotion history records."""

    __tablename__ = "studio_deployments"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    agent_id = Column(String(64), nullable=False, index=True)
    version_id = Column(String(64), nullable=False)
    environment = Column(String(32), nullable=False, default="PRODUCTION", index=True)
    deployed_by = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False, default="ACTIVE")
    deployed_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class StudioTemplateModel(Base):
    """Global pre-governed template catalog records."""

    __tablename__ = "studio_templates"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    template_type = Column(String(32), nullable=False)
    name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    definition_json = Column(JSON, nullable=False)


class StudioAuditLogModel(Base, TenantMixin):
    """Immutable audit trail of all Studio control plane modifications."""

    __tablename__ = "studio_audit_logs"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True, index=True)
    action_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False, index=True)
    performed_by = Column(String(128), nullable=False)
    details_json = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
