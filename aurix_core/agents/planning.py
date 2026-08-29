"""
AURIX Governed Autonomous Agents — Bounded Agent Planner
Phase 29 Production Hardened.
Produces structured, optimized execution plans with dry-run support and scenario outcome linking.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from aurix_core.agents.contracts import (
    AgentDefinition,
    ExecutionPlan,
    ExecutionStep,
    RiskLevel,
)


class AgentPlanner:
    """Produces bounded, structured execution plans for autonomous agents."""

    @classmethod
    def create_plan(
        cls,
        tenant_id: str,
        agent: AgentDefinition,
        objective: str,
        target_skill: str,
        target_tool: str,
        is_dry_run: bool = False,
        scenario_ref: Optional[str] = None,
    ) -> ExecutionPlan:
        """Construct a structured execution plan."""
        step = ExecutionStep(
            step_index=1,
            skill_name=target_skill,
            tool_call=target_tool,
            inputs={"objective": objective},
            expected_outcome="Successful governed execution of bounded skill.",
        )

        approval_needed = agent.risk_classification in (RiskLevel.HIGH, RiskLevel.CRITICAL)

        return ExecutionPlan(
            tenant_id=tenant_id,
            agent_id=agent.agent_id,
            objective=objective,
            steps=[step],
            risk_level=agent.risk_classification,
            approval_required=approval_needed,
            is_dry_run=is_dry_run,
            scenario_ref=scenario_ref,
        )

    @classmethod
    def optimize_plan(cls, plan: ExecutionPlan) -> ExecutionPlan:
        """Optimize execution plan by reordering validation steps before side-effecting operations."""
        # Ensure non-side-effecting checks execute first
        plan.steps.sort(key=lambda s: 0 if "analyze" in s.skill_name.lower() or "check" in s.skill_name.lower() else 1)
        for idx, step in enumerate(plan.steps):
            step.step_index = idx + 1
        return plan
