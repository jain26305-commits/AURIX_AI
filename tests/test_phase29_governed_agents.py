"""
AURIX Governed Autonomous Agents, Skills & Value Network — Phase 29 Master Test Suite
Validates Agent Runtime, Skill/Tool Registries, Semver Compatibility, Tenant-Scoped Circuit Breakers,
Governance Gates, Dry Run Mode, Multi-Step Compensation & DLQ, and Multi-Currency Value Attribution.
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from aurix_api.app import app
from aurix_core.agents.compensation import CompensationEngine
from aurix_core.agents.contracts import (
    AgentType,
    ApprovalRequest,
    CircuitState,
    ExecutionPlan,
    ExecutionStep,
    ReversibilityStatus,
    RiskLevel,
)
from aurix_core.agents.coordination import MultiAgentCoordinationRouter
from aurix_core.agents.governance_gate import GovernanceGate
from aurix_core.agents.orchestrator import AgentOrchestrator
from aurix_core.agents.planning import AgentPlanner
from aurix_core.agents.runtime import AgentRuntime
from aurix_core.agents.skills import SkillRegistry
from aurix_core.agents.tools import ToolRegistry
from aurix_core.agents.value_network import ValueNetworkEngine


def test_agent_runtime_and_loop_protection() -> None:
    """Test agent runtime lookup and loop protection step budget enforcement."""
    agent = AgentRuntime.get_agent("AGT-FIN-01")
    assert agent is not None
    assert agent.agent_type == AgentType.FINANCE_AGENT

    # Step budget within limit
    assert AgentRuntime.enforce_loop_protection(agent, current_step_count=5) is True

    # Step budget violation
    with pytest.raises(RuntimeError, match="violated execution step budget"):
        AgentRuntime.enforce_loop_protection(agent, current_step_count=12)


def test_skill_and_tool_governed_registries_and_versioning() -> None:
    """Test skill/tool lookups and semantic version compatibility checks."""
    skill = SkillRegistry.get_skill("propose_po_split")
    assert skill is not None
    assert skill.risk_level == RiskLevel.HIGH
    assert skill.requires_approval is True

    # Semver compatibility
    assert SkillRegistry.is_version_compatible("1.0", "1.2.0") is True
    assert SkillRegistry.is_version_compatible("2.0", "1.2.0") is False

    tool = ToolRegistry.get_tool("ERP_PO_API")
    assert tool is not None
    assert tool.rate_limit_per_min == 30


def test_tool_rate_limiting_and_tenant_scoped_circuit_breaker() -> None:
    """Test sliding-window rate limiting and verify tenant-scoped circuit breaker isolation."""
    tool_name = "ERP_PO_API"
    tenant_a = "tenant-a-test"
    tenant_b = "tenant-b-test"

    # Rate limiting check
    assert ToolRegistry.check_rate_limit(tool_name, tenant_a) is True

    # Tenant A fails 5 consecutive times -> Circuit trips for Tenant A ONLY
    assert ToolRegistry.is_circuit_open(tool_name, tenant_id=tenant_a) is False
    for _ in range(5):
        ToolRegistry.record_tool_result(tool_name, success=False, tenant_id=tenant_a)

    assert ToolRegistry.is_circuit_open(tool_name, tenant_id=tenant_a) is True

    # Tenant B should remain CLOSED and unaffected!
    assert ToolRegistry.is_circuit_open(tool_name, tenant_id=tenant_b) is False

    # Circuit breaker reset on success for Tenant A
    ToolRegistry.record_tool_result(tool_name, success=True, tenant_id=tenant_a)
    assert ToolRegistry.is_circuit_open(tool_name, tenant_id=tenant_a) is False


def test_governance_gate_risk_routing_idempotency_and_dry_run() -> None:
    """Test multi-gate execution validation including risk routing, idempotency, and dry run mode."""
    tenant = "tenant-gov-01"
    agent = AgentRuntime.get_agent("AGT-FIN-01")
    assert agent is not None

    plan = AgentPlanner.create_plan(
        tenant_id=tenant,
        agent=agent,
        objective="Analyze overdue invoice batch",
        target_skill="analyze_invoice",
        target_tool="ERP_INVOICE_API",
    )

    idem_key = GovernanceGate.generate_idempotency_key(tenant, agent.agent_id, plan.plan_id)

    # First execution pass (Low risk agent capability -> Auto-approved)
    gate_res = GovernanceGate.validate_execution_gate(tenant, agent, plan, idem_key)
    assert gate_res["allowed"] is True
    assert gate_res["requires_human_approval"] is False

    # Second execution pass (Duplicate idempotency key -> Blocked)
    dup_res = GovernanceGate.validate_execution_gate(tenant, agent, plan, idem_key)
    assert dup_res["allowed"] is False
    assert "Idempotency violation" in dup_res["reason"]

    # Dry run mode check (Validates without recording idempotency lock)
    dry_plan = AgentPlanner.create_plan(
        tenant_id=tenant,
        agent=agent,
        objective="Dry run simulation",
        target_skill="analyze_invoice",
        target_tool="ERP_INVOICE_API",
        is_dry_run=True,
    )
    dry_key = "DRY-KEY-001"
    dry_res = GovernanceGate.validate_execution_gate(tenant, agent, dry_plan, dry_key)
    assert dry_res["allowed"] is True
    assert dry_res["is_dry_run"] is True


def test_multi_step_execution_compensation_and_dlq() -> None:
    """Test multi-step execution runner, automated rollback on failure, and DLQ routing."""
    tenant = "tenant-dlq-01"
    agent = AgentRuntime.get_agent("AGT-FIN-01")
    assert agent is not None

    # Construct plan where step 2 fails
    plan = ExecutionPlan(
        tenant_id=tenant,
        agent_id=agent.agent_id,
        objective="Multi-step invoice and PO processing",
        steps=[
            ExecutionStep(step_index=1, skill_name="analyze_invoice", tool_call="ERP_INVOICE_API"),
            ExecutionStep(step_index=2, skill_name="fail_payment_transfer", tool_call="ERP_PO_API"),
        ],
        risk_level=RiskLevel.LOW,
    )

    idem_key = "IDEM-STEP-FAIL-01"
    record = AgentRuntime.execute_plan_sequential(tenant, agent, plan, idem_key)
    assert record.state.value == "DEAD_LETTER"
    assert "Compensated prior steps" in record.error_message


def test_compensation_and_multi_agent_coordination() -> None:
    """Test rollback reversibility classification and specialized agent routing."""
    comp = CompensationEngine.get_compensating_action("CREATE_PURCHASE_ORDER", ReversibilityStatus.REVERSIBLE)
    assert comp["supported"] is True
    assert comp["compensating_action"] == "CANCEL_PURCHASE_ORDER"

    irr_comp = CompensationEngine.get_compensating_action("EXECUTE_WIRE_TRANSFER", ReversibilityStatus.IRREVERSIBLE)
    assert irr_comp["supported"] is False

    target_agent = MultiAgentCoordinationRouter.route_to_specialized_agent("finance_working_capital")
    assert target_agent == AgentType.FINANCE_AGENT


def test_multi_currency_value_network_attribution() -> None:
    """Test deterministic multi-currency financial value attribution."""
    tenant = "tenant-val-01"

    val_rec = ValueNetworkEngine.attribute_value(
        tenant_id=tenant,
        execution_id="EXE-100",
        attribution_type="AVOIDED_COST",
        realized_value=1250000.0,
        currency="INR",
        base_currency="INR",
        decision_ref="DEC-001",
    )

    assert val_rec.realized_value == 1250000.0
    assert val_rec.currency == "INR"
    assert val_rec.value_attribution_type == "AVOIDED_COST"
    assert val_rec.verified is True


def test_approval_workflow_and_sla_escalation() -> None:
    """Test human approval ticket submission and SLA timeout escalation."""
    tenant = "tenant-apv-01"

    req = ApprovalRequest(
        tenant_id=tenant,
        execution_id="EXE-APV-1",
        plan_id="PLN-APV-1",
        status="PENDING",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    AgentOrchestrator.submit_approval_request(req)

    # Test SLA escalation (created in past -> escalates)
    escalated = GovernanceGate.check_approval_sla_and_escalate(req, sla_hours=24.0)
    assert escalated.status == "ESCALATED"
    assert escalated.escalated_to == "OPERATIONS_VP"

    # Process manager approval
    processed = AgentOrchestrator.process_approval(req.approval_id, approved=True, approver_id="USR-MGR-01")
    assert processed is not None
    assert processed.status == "APPROVED"


def test_master_agent_orchestrator_sweep() -> None:
    """Test master AgentOrchestrator coordination sweep and summary cache rollup."""
    tenant = "tenant-master-agt"

    summary = AgentOrchestrator.run_agent_sweep(tenant_id=tenant)
    assert summary.registered_agents_count >= 2
    assert summary.success_rate_pct > 90.0
    assert summary.total_realized_value_usd > 0.0
