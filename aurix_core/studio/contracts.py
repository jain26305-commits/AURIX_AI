"""
AURIX Enterprise Agent Studio & Workflow Orchestration — Contracts & Schemas
Phase 30 Core Implementation.
Defines authoritative schemas for Studio Agents, Workflows, DAG Nodes, Edges,
Draft/Publish Lifecycles, Validations, Deployments, Templates, and Import/Export DTOs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class StudioAgentStatus(str, Enum):
    """Lifecycle state of an Agent Studio entity."""
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    VALID = "VALID"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    PUBLISHED = "PUBLISHED"
    DEPLOYED = "DEPLOYED"
    PAUSED = "PAUSED"
    RETIRED = "RETIRED"


class EnvironmentTier(str, Enum):
    """Governed deployment target environment tiers."""
    DEVELOPMENT = "DEVELOPMENT"
    TEST = "TEST"
    PRODUCTION = "PRODUCTION"


class NodeType(str, Enum):
    """Workflow DAG Node Classifications."""
    TRIGGER = "TRIGGER"
    CONTEXT = "CONTEXT"
    CONDITION = "CONDITION"
    DECISION = "DECISION"
    SKILL = "SKILL"
    TOOL = "TOOL"
    APPROVAL = "APPROVAL"
    WAIT = "WAIT"
    BRANCH = "BRANCH"
    MERGE = "MERGE"
    LOOP = "LOOP"
    DELAY = "DELAY"
    VERIFY = "VERIFY"
    NOTIFICATION = "NOTIFICATION"
    ESCALATE = "ESCALATE"
    END = "END"
    COMPENSATE = "COMPENSATE"


class TriggerType(str, Enum):
    """Workflow triggering mechanisms."""
    EVENT = "EVENT"
    SCHEDULE = "SCHEDULE"
    MANUAL = "MANUAL"
    API = "API"
    THRESHOLD = "THRESHOLD"


# --- Workflow Graph Definition Schemas ---
class WorkflowNode(BaseModel):
    """Single node within a visual DAG workflow definition."""
    node_id: str = Field(default_factory=lambda: f"NODE-{uuid.uuid4().hex[:6].upper()}")
    node_type: NodeType
    name: str
    description: str = ""
    config: Dict[str, Any] = Field(default_factory=dict)
    skill_ref: Optional[str] = None
    tool_ref: Optional[str] = None
    required_role: Optional[str] = None
    timeout_seconds: int = 300
    retry_limit: int = 3
    is_terminal: bool = False


class WorkflowEdge(BaseModel):
    """Directed connection between workflow nodes."""
    edge_id: str = Field(default_factory=lambda: f"EDGE-{uuid.uuid4().hex[:6].upper()}")
    source_node_id: str
    target_node_id: str
    condition_expr: Optional[str] = None  # e.g. "outcome == 'SUCCESS'" or "amount > 50000"


class WorkflowTrigger(BaseModel):
    """Trigger configuration for workflow activation."""
    trigger_type: TriggerType = TriggerType.EVENT
    event_pattern: str = "INVENTORY_SHORTAGE_DETECTED"
    schedule_cron: Optional[str] = None
    threshold_conditions: Dict[str, Any] = Field(default_factory=dict)


class StudioWorkflowDefinition(BaseModel):
    """Complete graph definition of a visual workflow."""
    workflow_id: str = Field(default_factory=lambda: f"WFL-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str = "GLOBAL"
    name: str
    description: str = ""
    version: str = "1.0.0"
    status: StudioAgentStatus = StudioAgentStatus.DRAFT
    triggers: List[WorkflowTrigger] = Field(default_factory=list)
    nodes: List[WorkflowNode] = Field(default_factory=list)
    edges: List[WorkflowEdge] = Field(default_factory=list)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Agent Builder & Versioning Schemas ---
class StudioAgentDraft(BaseModel):
    """Agent Builder configuration payload."""
    agent_id: str = Field(default_factory=lambda: f"ST-AGT-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str = "GLOBAL"
    name: str
    business_purpose: str
    domain: str = "SUPPLY_CHAIN"
    owner: str = "ADMIN"
    agent_type: str = "PROCUREMENT_AGENT"
    version: str = "1.0.0"
    status: StudioAgentStatus = StudioAgentStatus.DRAFT
    allowed_skills: List[str] = Field(default_factory=list)
    allowed_tools: List[str] = Field(default_factory=list)
    allowed_context_domains: List[str] = Field(default_factory=list)
    risk_classification: str = "MEDIUM"
    max_steps_per_execution: int = 10
    budget_limit_usd: float = 1000.0
    workflow_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StudioAgentVersion(BaseModel):
    """Immutable versioned snapshot of a published Studio Agent."""
    version_id: str = Field(default_factory=lambda: f"VER-{uuid.uuid4().hex[:8].upper()}")
    agent_id: str
    tenant_id: str
    version_number: str  # e.g., "1.0.0", "1.1.0"
    status: StudioAgentStatus = StudioAgentStatus.PUBLISHED
    config_snapshot_json: Dict[str, Any]
    published_by: str
    change_summary: str = ""
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Validation, Linter & Governance DTOs ---
class ValidationIssue(BaseModel):
    """Structured configuration or DAG linter finding."""
    severity: str  # "ERROR", "WARNING", "INFO"
    code: str
    message: str
    node_id: Optional[str] = None


class ValidationReport(BaseModel):
    """Pre-publication static analysis report."""
    is_valid: bool
    total_errors: int = 0
    total_warnings: int = 0
    issues: List[ValidationIssue] = Field(default_factory=list)
    blast_radius_summary: Dict[str, Any] = Field(default_factory=dict)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Deployment & Rollback DTOs ---
class DeploymentRecord(BaseModel):
    """Record of an agent/workflow promotion to an environment tier."""
    deployment_id: str = Field(default_factory=lambda: f"DEP-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str
    agent_id: str
    version_id: str
    environment: EnvironmentTier
    deployed_by: str
    deployed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "ACTIVE"  # "ACTIVE", "ROLLED_BACK", "SUPERSEDED"
    rollback_from_id: Optional[str] = None


# --- Template & Dependency Graph DTOs ---
class StudioTemplate(BaseModel):
    """Pre-governed reusable enterprise agent or workflow template."""
    template_id: str = Field(default_factory=lambda: f"TPL-{uuid.uuid4().hex[:8].upper()}")
    template_type: str  # "AGENT", "WORKFLOW"
    name: str
    category: str
    description: str
    suggested_risk: str = "MEDIUM"
    definition_json: Dict[str, Any]


class DependencyGraphReport(BaseModel):
    """Resolution graph showing entity relationships across Agent Studio."""
    tenant_id: str
    agent_id: str
    dependencies: List[Dict[str, Any]]
    downstream_impacts: List[str]


class ChangeImpactReport(BaseModel):
    """Impact analysis prior to version publication or rollback."""
    agent_id: str
    target_version: str
    affected_workflows: List[str]
    affected_tools: List[str]
    risk_level_change: str
    requires_executive_signoff: bool = False


# --- Master Studio Panoramic Summary ---
class StudioSummaryReport(BaseModel):
    """Master executive overview of Agent Studio control plane health."""
    tenant_id: str
    period_key: str = "CURRENT"
    total_agents_count: int
    draft_agents_count: int
    published_agents_count: int
    deployed_production_count: int
    active_workflows_count: int
    available_templates_count: int
    total_deployments_count: int
    recent_deployments: List[DeploymentRecord] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
