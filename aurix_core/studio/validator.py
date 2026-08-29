"""
AURIX Enterprise Agent Studio — Configuration Validator & DAG Linter
Phase 30 Core Implementation.
Performs pre-publication static analysis verifying graph integrity, skill/tool existence, and blast radius.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.agents.skills import SkillRegistry
from aurix_core.agents.tools import ToolRegistry
from aurix_core.studio.contracts import (
    NodeType,
    StudioAgentDraft,
    StudioWorkflowDefinition,
    ValidationIssue,
    ValidationReport,
)
from aurix_core.studio.workflow_builder import WorkflowBuilder


class StudioValidator:
    """Pre-publication static analyzer and blast radius assessor."""

    @classmethod
    def validate_agent_draft(cls, draft: StudioAgentDraft) -> ValidationReport:
        """Validate agent draft properties, permissions, and skill/tool compatibility."""
        issues: List[ValidationIssue] = []

        if not draft.name or len(draft.name.strip()) < 3:
            issues.append(ValidationIssue(severity="ERROR", code="INVALID_NAME", message="Agent name must be at least 3 characters."))

        if draft.max_steps_per_execution <= 0 or draft.max_steps_per_execution > 50:
            issues.append(ValidationIssue(severity="ERROR", code="INVALID_STEP_LIMIT", message="Step limit must be between 1 and 50."))

        # Check registered skills
        for skill in draft.allowed_skills:
            if not SkillRegistry.get_skill(skill):
                issues.append(ValidationIssue(severity="WARNING", code="UNREGISTERED_SKILL", message=f"Skill '{skill}' is not currently in SkillRegistry."))

        # Check registered tools
        for tool in draft.allowed_tools:
            if not ToolRegistry.get_tool(tool):
                issues.append(ValidationIssue(severity="WARNING", code="UNREGISTERED_TOOL", message=f"Tool '{tool}' is not currently in ToolRegistry."))

        errors = [i for i in issues if i.severity == "ERROR"]
        warnings = [i for i in issues if i.severity == "WARNING"]

        return ValidationReport(
            is_valid=len(errors) == 0,
            total_errors=len(errors),
            total_warnings=len(warnings),
            issues=issues,
            blast_radius_summary={
                "risk_tier": draft.risk_classification,
                "max_financial_exposure_usd": draft.budget_limit_usd,
                "tool_surface_count": len(draft.allowed_tools),
            },
        )

    @classmethod
    def validate_workflow_graph(cls, workflow: StudioWorkflowDefinition) -> ValidationReport:
        """Validate visual workflow DAG structure, terminal nodes, and cycle freedom."""
        issues: List[ValidationIssue] = []

        if not workflow.nodes:
            issues.append(ValidationIssue(severity="ERROR", code="EMPTY_WORKFLOW", message="Workflow must contain at least one node."))
            return ValidationReport(is_valid=False, total_errors=1, issues=issues)

        # 1. Trigger presence
        has_trigger = any(n.node_type == NodeType.TRIGGER for n in workflow.nodes)
        if not has_trigger and not workflow.triggers:
            issues.append(ValidationIssue(severity="ERROR", code="NO_TRIGGER", message="Workflow must specify an entry trigger."))

        # 2. Cycle Detection
        if WorkflowBuilder.detect_cycles(workflow):
            issues.append(ValidationIssue(severity="ERROR", code="CYCLIC_DAG", message="Workflow graph contains an illegal recursive cycle."))

        # 3. Dangling / Unconnected nodes
        node_ids = {n.node_id for n in workflow.nodes}
        connected_ids = {e.source_node_id for e in workflow.edges} | {e.target_node_id for e in workflow.edges}
        if len(workflow.nodes) > 1:
            dangling = node_ids - connected_ids
            for d in dangling:
                issues.append(ValidationIssue(severity="WARNING", code="DANGLING_NODE", message="Node is not connected to any edge.", node_id=d))

        errors = [i for i in issues if i.severity == "ERROR"]
        warnings = [i for i in issues if i.severity == "WARNING"]

        return ValidationReport(
            is_valid=len(errors) == 0,
            total_errors=len(errors),
            total_warnings=len(warnings),
            issues=issues,
            blast_radius_summary={"total_nodes": len(workflow.nodes), "total_edges": len(workflow.edges)},
        )
