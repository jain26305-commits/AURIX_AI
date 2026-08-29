"""
AURIX Enterprise Agent Studio & Workflow Orchestration — Phase 30 Master Test Suite
Validates Agent Drafting, Immutable Versioning, Visual Workflow DAG & Cycle Detection,
Static Linters, Multi-Tier Deployment Promotion, Rollbacks, Dry Run Sandbox, and Templates.
"""

from datetime import datetime, timezone
import pytest

from aurix_core.studio.agent_builder import AgentBuilder
from aurix_core.studio.contracts import (
    EnvironmentTier,
    NodeType,
    StudioAgentDraft,
    StudioAgentStatus,
    StudioWorkflowDefinition,
    WorkflowEdge,
    WorkflowNode,
    WorkflowTrigger,
)
from aurix_core.studio.deployment_manager import DeploymentManager
from aurix_core.studio.dry_run_engine import StudioDryRunEngine
from aurix_core.studio.import_export import StudioImportExport
from aurix_core.studio.orchestrator import StudioOrchestrator
from aurix_core.studio.secret_manager import StudioSecretManager
from aurix_core.studio.templates import TemplateCatalog
from aurix_core.studio.validator import StudioValidator
from aurix_core.studio.workflow_builder import WorkflowBuilder


def test_agent_builder_lifecycle_and_drafting() -> None:
    """Test agent drafting, property updates, and catalog listing."""
    tenant = "tenant-studio-01"
    draft = StudioAgentDraft(
        tenant_id=tenant,
        name="Procurement Shortage Agent",
        business_purpose="Automates purchase order reallocation during supplier delays.",
        agent_type="PROCUREMENT_AGENT",
        version="1.0.0",
        allowed_skills=["propose_po_split"],
        allowed_tools=["ERP_PO_API"],
        risk_classification="HIGH",
    )

    created = AgentBuilder.create_agent_draft(draft)
    assert created.agent_id.startswith("ST-AGT-")
    assert created.name == "Procurement Shortage Agent"

    listed = AgentBuilder.list_agents(tenant_id=tenant)
    assert any(a.agent_id == created.agent_id for a in listed)


def test_agent_versioning_and_immutability() -> None:
    """Test publishing immutable agent versions."""
    tenant = "tenant-studio-02"
    draft = StudioAgentDraft(
        tenant_id=tenant,
        name="Collections Aging Review",
        business_purpose="Inspects overdue invoices.",
        version="1.0.0",
    )
    AgentBuilder.create_agent_draft(draft)

    version = AgentBuilder.publish_agent_version(
        agent_id=draft.agent_id,
        published_by="USR-ADMIN-1",
        change_summary="Initial Production Release",
    )

    assert version.version_number == "1.0.0"
    assert version.status == StudioAgentStatus.PUBLISHED
    assert version.config_snapshot_json["name"] == "Collections Aging Review"


def test_workflow_graph_model_and_dag_validation() -> None:
    """Test DAG workflow construction and cycle detection."""
    tenant = "tenant-studio-03"

    # Valid DAG Workflow
    node1 = WorkflowNode(node_id="N-TRIG", node_type=NodeType.TRIGGER, name="Event Trigger")
    node2 = WorkflowNode(node_id="N-SKL", node_type=NodeType.SKILL, name="Inspect Overdue")
    node3 = WorkflowNode(node_id="N-END", node_type=NodeType.END, name="Terminal Node", is_terminal=True)

    wfl = StudioWorkflowDefinition(
        tenant_id=tenant,
        name="Valid Collections Workflow",
        nodes=[node1, node2, node3],
        edges=[
            WorkflowEdge(source_node_id="N-TRIG", target_node_id="N-SKL"),
            WorkflowEdge(source_node_id="N-SKL", target_node_id="N-END"),
        ],
    )

    created_wfl = WorkflowBuilder.create_workflow(wfl)
    assert WorkflowBuilder.detect_cycles(created_wfl) is False

    # Cyclic Invalid Workflow (A -> B -> A)
    cyclic_wfl = StudioWorkflowDefinition(
        tenant_id=tenant,
        name="Cyclic Workflow",
        nodes=[node1, node2],
        edges=[
            WorkflowEdge(source_node_id="N-TRIG", target_node_id="N-SKL"),
            WorkflowEdge(source_node_id="N-SKL", target_node_id="N-TRIG"),
        ],
    )
    assert WorkflowBuilder.detect_cycles(cyclic_wfl) is True


def test_configuration_validator_and_linting() -> None:
    """Test static analyzer reporting errors on invalid configurations."""
    draft = StudioAgentDraft(
        name="X",  # Too short
        business_purpose="Test",
        max_steps_per_execution=100,  # Exceeds limit
        allowed_skills=["unknown_custom_skill"],
    )

    report = StudioValidator.validate_agent_draft(draft)
    assert report.is_valid is False
    assert report.total_errors >= 2
    assert any(iss.code == "INVALID_NAME" for iss in report.issues)
    assert any(iss.code == "INVALID_STEP_LIMIT" for iss in report.issues)


def test_environment_promotion_and_deployment_gate() -> None:
    """Test deploying agent version to PRODUCTION and synchronizing with Phase 29 runtime."""
    tenant = "tenant-dep-01"
    draft = StudioAgentDraft(
        tenant_id=tenant,
        name="Live Production Agent",
        business_purpose="Autonomous replenishment",
        agent_type="INVENTORY_AGENT",
        version="1.2.0",
        allowed_skills=["analyze_invoice"],
        allowed_tools=["ERP_INVOICE_API"],
    )
    AgentBuilder.create_agent_draft(draft)
    AgentBuilder.publish_agent_version(draft.agent_id, "ADMIN")

    dep = DeploymentManager.deploy_agent_version(
        tenant_id=tenant,
        agent_id=draft.agent_id,
        version_number="1.2.0",
        environment=EnvironmentTier.PRODUCTION,
        deployed_by="USR-DEPLOYER-01",
    )

    assert dep.environment == EnvironmentTier.PRODUCTION
    assert dep.status == "ACTIVE"


def test_deployment_rollback_integrity() -> None:
    """Test one-click rollback of production deployments."""
    tenant = "tenant-rb-01"
    agent_id = "ST-AGT-ROLLBACK-1"
    draft = StudioAgentDraft(tenant_id=tenant, agent_id=agent_id, name="Rollback Target", business_purpose="Test", version="1.0.0")
    AgentBuilder.create_agent_draft(draft)

    # Deploy v1
    DeploymentManager.deploy_agent_version(tenant, agent_id, "1.0.0", EnvironmentTier.PRODUCTION, "ADMIN")

    # Rollback to v1
    rb = DeploymentManager.rollback_deployment(tenant, agent_id, "1.0.0", "USR-ADMIN-ROLLBACK")
    assert rb.status == "ACTIVE"
    assert rb.version_id == f"VER-{agent_id}-1.0.0"


def test_dry_run_simulation_isolation() -> None:
    """Test non-mutating sandbox simulation trace generation."""
    tenant = "tenant-dry-01"
    node1 = WorkflowNode(node_id="N1", node_type=NodeType.TRIGGER, name="Simulated Trigger")
    node2 = WorkflowNode(node_id="N2", node_type=NodeType.TOOL, name="ERP PO API")

    wfl = StudioWorkflowDefinition(tenant_id=tenant, name="Dry Run Test", nodes=[node1, node2])
    res = StudioDryRunEngine.execute_dry_run(tenant, wfl)

    assert res["is_dry_run"] is True
    assert res["total_steps_simulated"] == 2
    assert len(res["step_trace"]) == 2


def test_template_catalog_and_secret_redaction() -> None:
    """Test pre-governed template retrieval and secret redaction."""
    templates = TemplateCatalog.list_templates()
    assert len(templates) >= 2

    # Secret Redaction
    raw_config = {"api_key": "sk-live-123456", "db_password": "supersecretpassword", "timeout": 30}
    sanitized = StudioSecretManager.sanitize_config_for_export(raw_config)
    assert sanitized["api_key"] == "SECRET_REF_API_KEY"
    assert sanitized["db_password"] == "SECRET_REF_DB_PASSWORD"
    assert sanitized["timeout"] == 30


def test_safe_import_export_sanitization() -> None:
    """Test package export and sanitized import enforcing tenant scoping."""
    tenant = "tenant-exp-01"
    draft = StudioAgentDraft(tenant_id=tenant, name="Exportable Agent", business_purpose="Test export")

    bundle = StudioImportExport.export_agent_bundle(draft)
    assert bundle["bundle_type"] == "AURIX_STUDIO_AGENT_PACKAGE"

    # Import into new tenant
    imported = StudioImportExport.import_agent_bundle("tenant-new-02", bundle)
    assert imported.tenant_id == "tenant-new-02"
    assert imported.name == "Exportable Agent"


def test_studio_orchestrator_summary_sweep() -> None:
    """Test master StudioOrchestrator control plane summary rollup."""
    tenant = "tenant-orch-01"
    summary = StudioOrchestrator.run_studio_sweep(tenant_id=tenant)
    assert summary.total_agents_count >= 1
    assert summary.available_templates_count >= 2
