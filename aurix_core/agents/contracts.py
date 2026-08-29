"""
AURIX Governed Autonomous Agents, Skills & Value Network — Contracts & Schemas
Phase 29 Production Hardened.
Defines authoritative schemas for Agent Runtime, Skill Registry, Tool Registry,
Risk Classifications, Circuit Breakers, Execution Plans, Approval Workflows,
Dead-Letter Queues, and Multi-Currency Value Attribution.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AgentType(str, Enum):
    """Specialized enterprise agent classifications."""
    FINANCE_AGENT = "FINANCE_AGENT"
    PROCUREMENT_AGENT = "PROCUREMENT_AGENT"
    SALES_AGENT = "SALES_AGENT"
    INVENTORY_AGENT = "INVENTORY_AGENT"
    MANUFACTURING_AGENT = "MANUFACTURING_AGENT"
    SUPPLY_CHAIN_AGENT = "SUPPLY_CHAIN_AGENT"
    RISK_AGENT = "RISK_AGENT"
    EXECUTIVE_AGENT = "EXECUTIVE_AGENT"
    ASSURANCE_AGENT = "ASSURANCE_AGENT"


class AgentStatus(str, Enum):
    """Agent lifecycle status."""
    REGISTERED = "REGISTERED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


class RiskLevel(str, Enum):
    """Autonomy risk classification."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExecutionState(str, Enum):
    """Lifecycle state of an autonomous execution."""
    PLANNED = "PLANNED"
    PENDING_GATE = "PENDING_GATE"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    VERIFIED = "VERIFIED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    DEAD_LETTER = "DEAD_LETTER"


class ReversibilityStatus(str, Enum):
    """Operational reversibility classification."""
    REVERSIBLE = "REVERSIBLE"
    PARTIALLY_REVERSIBLE = "PARTIALLY_REVERSIBLE"
    IRREVERSIBLE = "IRREVERSIBLE"


class CircuitState(str, Enum):
    """Tool circuit breaker operational states."""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


# --- Agent Runtime Contract ---
class AgentDefinition(BaseModel):
    """Authoritative agent runtime specification."""
    model_config = ConfigDict(extra="allow")

    agent_id: str = Field(default_factory=lambda: f"AGT-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str = "GLOBAL"
    agent_type: AgentType
    name: str
    version: str = "v1.0"
    status: AgentStatus = AgentStatus.ACTIVE
    owner: str = "SYSTEM_GOVERNANCE"
    capabilities: List[str] = Field(default_factory=list)
    risk_classification: RiskLevel = RiskLevel.MEDIUM
    allowed_tools: List[str] = Field(default_factory=list)
    max_steps_per_execution: int = 10
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Skill & Tool Registry Contracts ---
class SkillDefinition(BaseModel):
    """Governed enterprise skill specification."""
    skill_id: str = Field(default_factory=lambda: f"SKL-{uuid.uuid4().hex[:8].upper()}")
    name: str
    version: str = "v1.0"
    description: str = ""
    risk_level: RiskLevel = RiskLevel.MEDIUM
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False
    side_effect: ReversibilityStatus = ReversibilityStatus.REVERSIBLE


class ToolDefinition(BaseModel):
    """Governed internal API or connector tool specification with circuit breaker telemetry."""
    tool_id: str = Field(default_factory=lambda: f"TLS-{uuid.uuid4().hex[:8].upper()}")
    name: str
    version: str = "v1.0"
    endpoint_ref: str
    risk_level: RiskLevel = RiskLevel.MEDIUM
    rate_limit_per_min: int = 60
    circuit_state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_timestamp: Optional[datetime] = None


# --- Execution Plan & Journal Contracts ---
class ExecutionStep(BaseModel):
    """A single bounded step in an agent execution plan."""
    step_index: int
    skill_name: str
    tool_call: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    expected_outcome: str = ""
    is_completed: bool = False
    is_compensated: bool = False


class ExecutionPlan(BaseModel):
    """Structured agent plan submitted to the execution gate."""
    plan_id: str = Field(default_factory=lambda: f"PLN-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str = "GLOBAL"
    agent_id: str
    objective: str
    steps: List[ExecutionStep] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    approval_required: bool = False
    is_dry_run: bool = False
    scenario_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExecutionJournalRecord(BaseModel):
    """Immutable audit journal record of an agent execution."""
    execution_id: str = Field(default_factory=lambda: f"EXE-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str = "GLOBAL"
    agent_id: str
    plan_id: str
    idempotency_key: str
    state: ExecutionState = ExecutionState.PLANNED
    risk_level: RiskLevel = RiskLevel.MEDIUM
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    is_dry_run: bool = False
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class ApprovalRequest(BaseModel):
    """Human-in-the-loop approval ticket for high-risk autonomous actions."""
    approval_id: str = Field(default_factory=lambda: f"APV-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str = "GLOBAL"
    execution_id: str
    plan_id: str
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED, ESCALATED
    required_role: str = "OPERATIONS_MANAGER"
    approver_id: Optional[str] = None
    reason: Optional[str] = None
    sla_deadline: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    escalated_to: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Multi-Currency Value Network Contracts ---
class ValueNetworkRecord(BaseModel):
    """Value Network realization record connecting execution outcomes to financial value."""
    value_id: str = Field(default_factory=lambda: f"VAL-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str = "GLOBAL"
    execution_id: str
    decision_ref: Optional[str] = None
    value_attribution_type: str
    realized_value: float = 0.0
    currency: str = "USD"
    base_currency: str = "USD"
    verified: bool = True
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Master Agent Summary Report ---
class AgentSummaryReport(BaseModel):
    """Master executive agent operating intelligence summary."""
    tenant_id: str
    period_key: str
    registered_agents_count: int
    active_agents_count: int
    total_executions_count: int
    success_rate_pct: float
    pending_approvals_count: int
    dead_letter_count: int = 0
    total_realized_value_usd: float = 0.0
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
