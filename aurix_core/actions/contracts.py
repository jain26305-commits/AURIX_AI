"""Pydantic v2 data contracts, action enums, lifecycle states, and audit records for Phase 14."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ActionCategory(str, Enum):
    """Classification of action risk and execution authority levels."""
    READ = "READ"
    ANALYZE = "ANALYZE"
    SIMULATE = "SIMULATE"
    RECOMMEND = "RECOMMEND"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    EXECUTABLE = "EXECUTABLE"
    DESTRUCTIVE = "DESTRUCTIVE"


class ActionType(str, Enum):
    """Supported operational action types corresponding to verified connectors."""
    TRANSFER_STOCK = "TRANSFER_STOCK"
    TRIGGER_REPLENISHMENT = "TRIGGER_REPLENISHMENT"
    CREATE_PROCUREMENT_REQUEST = "CREATE_PROCUREMENT_REQUEST"
    CHANGE_SUPPLIER_REQUEST = "CHANGE_SUPPLIER_REQUEST"
    REQUEST_EXPEDITE = "REQUEST_EXPEDITE"
    REQUEST_CARRIER_CHANGE = "REQUEST_CARRIER_CHANGE"
    EXECUTE_REBALANCE = "EXECUTE_REBALANCE"


class ActionState(str, Enum):
    """Deterministic state machine lifecycle stages for operational actions."""
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTION_SENT = "EXECUTION_SENT"
    EXTERNAL_ACCEPTED = "EXTERNAL_ACCEPTED"
    EXTERNAL_UNKNOWN = "EXTERNAL_UNKNOWN"
    VERIFICATION_PENDING = "VERIFICATION_PENDING"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    APPROVAL_INVALIDATED = "APPROVAL_INVALIDATED"
    ACTION_CONFLICT = "ACTION_CONFLICT"
    COMPENSATION_REQUIRED = "COMPENSATION_REQUIRED"
    COMPENSATED = "COMPENSATED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    MANUAL_INTERVENTION_REQUIRED = "MANUAL_INTERVENTION_REQUIRED"
    EXPIRED = "EXPIRED"


class ApprovalState(str, Enum):
    """Lifecycle states for human approval workflows."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    INVALIDATED = "INVALIDATED"


class ActionApproval(BaseModel):
    """Record of approval decision for an action."""
    approver_id: str = Field(..., description="User or service account ID granting/rejecting approval")
    approver_role: str = Field(..., description="Role held by the approver at decision time")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp of approval decision"
    )
    decision: ApprovalState = Field(..., description="Approval decision state")
    comments: Optional[str] = Field(default=None, description="Optional justification or comments")
    policy_evaluated: Dict[str, Any] = Field(default_factory=dict, description="Policy checks evaluated at approval")


class ActionContract(BaseModel):
    """Master structured action contract for controlled decision execution."""
    action_id: str = Field(..., description="Unique action identifier (e.g., ACT-12345)")
    tenant_id: str = Field(..., description="Strict tenant isolation boundary identifier")
    action_type: ActionType = Field(..., description="Specific operational action type")
    action_category: ActionCategory = Field(..., description="Risk classification category")
    entity_type: str = Field(..., description="Target domain entity type (e.g., inventory, purchase_orders)")
    entity_id: str = Field(..., description="Primary entity identifier (SKU, facility, shipment ID)")
    recommendation_id: Optional[str] = Field(default=None, description="Source Phase 9 recommendation ID")
    source_run_id: Optional[str] = Field(default=None, description="Associated intelligence or ingestion run ID")
    capability_name: Optional[str] = Field(default=None, description="Generating AURIX analytical capability")
    requested_by: str = Field(..., description="User or service account ID requesting the action")
    requested_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Action creation timestamp"
    )
    policy_version: str = Field(default="1.0.0", description="Policy engine version used for validation")
    approval_required: bool = Field(default=True, description="Whether human approval is mandated by policy")
    approval_state: ApprovalState = Field(default=ApprovalState.PENDING, description="Current approval workflow state")
    execution_state: ActionState = Field(default=ActionState.CREATED, description="Current action lifecycle state")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Action execution payload and parameter values")
    expected_result: Dict[str, Any] = Field(default_factory=dict, description="Simulated or expected outcome metrics")
    actual_result: Dict[str, Any] = Field(default_factory=dict, description="Actual outcome returned by external adapter")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Evidence references and analytical provenance")
    freshness_timestamp: str = Field(..., description="Timestamp verifying underlying data freshness")
    idempotency_key: str = Field(..., description="Deterministic key for duplicate write prevention")
    correlation_id: Optional[str] = Field(default=None, description="Distributed correlation trace ID")
    error_message: Optional[str] = Field(default=None, description="Error details if execution or validation failed")
    external_transaction_id: Optional[str] = Field(default=None, description="Transaction ID assigned by external system")
    expires_at: Optional[str] = Field(default=None, description="Expiration timestamp for approval and execution")
    approval_hash: Optional[str] = Field(default=None, description="Cryptographic content hash locked at approval time to enforce immutability")


class ActionAuditRecord(BaseModel):
    """Immutable audit record tracking action state transitions and security checkpoints."""
    audit_id: str = Field(..., description="Unique audit log identifier")
    tenant_id: str = Field(..., description="Tenant scope identifier")
    action_id: str = Field(..., description="Associated action ID")
    actor_id: str = Field(..., description="User or system initiating the state change")
    actor_role: str = Field(..., description="Role of the actor")
    previous_state: Optional[ActionState] = Field(default=None, description="Prior action lifecycle state")
    new_state: ActionState = Field(..., description="Transitioned action lifecycle state")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Audit entry timestamp"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context or validation evidence")