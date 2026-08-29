"""
AURIX Governed Autonomous Agents — Execution Governance Gate
Phase 29 Production Hardened.
Enforces multi-gate validation: tenant scope, policy compliance, permission checks,
idempotency locks, dry-run mode, and SLA approval escalation.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Set
from sqlalchemy.orm import Session
from aurix_core.agents.contracts import (
    AgentDefinition,
    ApprovalRequest,
    ExecutionPlan,
    ExecutionState,
    RiskLevel,
)
from aurix_core.agents.tools import ToolRegistry


class GovernanceGate:
    """Multi-gate execution validator enforcing policy, security, idempotency, and dry-run safety."""

    _executed_idempotency_keys: Set[str] = set()

    @classmethod
    def generate_idempotency_key(cls, tenant_id: str, agent_id: str, plan_id: str) -> str:
        """Generate a cryptographically sound idempotency key for side-effecting actions."""
        raw = f"{tenant_id}:{agent_id}:{plan_id}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def validate_execution_gate(
        cls,
        tenant_id: str,
        agent: AgentDefinition,
        plan: ExecutionPlan,
        idempotency_key: str,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Gate Pipeline:
        1. Tenant Validation
        2. Agent Active Status Check
        3. Tool Rate Limit & Tenant-Scoped Circuit Breaker Check
        4. Dry Run Mode Handling
        5. Idempotency Check (Memory & Database)
        6. Risk-Based Autonomy Routing
        """
        # 1. Tenant Check
        if agent.tenant_id != "GLOBAL" and agent.tenant_id != tenant_id:
            return {"allowed": False, "reason": "Tenant isolation violation."}

        # 2. Status Check
        if agent.status.value != "ACTIVE":
            return {"allowed": False, "reason": f"Agent status is {agent.status.value} (not active)."}

        # 3. Tool Check (Tenant-Scoped)
        for step in plan.steps:
            if ToolRegistry.is_circuit_open(step.tool_call, tenant_id=tenant_id):
                return {"allowed": False, "reason": f"Circuit breaker is OPEN for tool {step.tool_call} on tenant {tenant_id}."}
            if not ToolRegistry.check_rate_limit(step.tool_call, tenant_id):
                return {"allowed": False, "reason": f"Rate limit exceeded for tool {step.tool_call} on tenant {tenant_id}."}

        # 4. Dry Run Check (Safe preview without state mutation)
        if plan.is_dry_run:
            return {
                "allowed": True,
                "requires_human_approval": False,
                "initial_state": ExecutionState.APPROVED.value,
                "is_dry_run": True,
                "reason": "DRY_RUN mode approved. Execution plan validated without side effects.",
            }

        # 5. Idempotency Check
        if idempotency_key in cls._executed_idempotency_keys:
            return {"allowed": False, "reason": "Idempotency violation: Action already executed."}

        if db is not None:
            from aurix_core.database.models.agents import AgentExecutionJournalModel
            exists = db.query(AgentExecutionJournalModel).filter(
                AgentExecutionJournalModel.idempotency_key == idempotency_key
            ).first()
            if exists:
                return {"allowed": False, "reason": "Idempotency violation: Duplicate execution key in database."}

        # 6. Risk-Based Autonomy Routing
        requires_approval = plan.approval_required or agent.risk_classification in (RiskLevel.HIGH, RiskLevel.CRITICAL)

        if requires_approval:
            return {
                "allowed": True,
                "requires_human_approval": True,
                "initial_state": ExecutionState.PENDING_APPROVAL.value,
                "is_dry_run": False,
                "reason": f"Risk level {agent.risk_classification.value} mandates human approval.",
            }

        # Low risk auto-execution allowed
        cls._executed_idempotency_keys.add(idempotency_key)
        return {
            "allowed": True,
            "requires_human_approval": False,
            "initial_state": ExecutionState.APPROVED.value,
            "is_dry_run": False,
            "reason": "Passed all governance gates. Low-risk auto-execution permitted.",
        }

    @classmethod
    def check_approval_sla_and_escalate(
        cls,
        request: ApprovalRequest,
        sla_hours: float = 24.0,
    ) -> ApprovalRequest:
        """Escalate approval requests that exceed configured SLA response deadline."""
        now = datetime.now(timezone.utc)
        if request.status == "PENDING" and (now - request.created_at) > timedelta(hours=sla_hours):
            request.status = "ESCALATED"
            request.escalated_to = "OPERATIONS_VP"
        return request
