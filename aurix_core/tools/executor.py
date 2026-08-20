"""Deterministic AURIX tool execution boundary."""

from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.orm import Session

from aurix_core.intelligence.router import RoutingDecision
from aurix_core.tools.contracts import ToolRequest, ToolResult
from aurix_core.tools.registry import ToolRegistry


class DeterministicToolExecutor:
    """Executes only registered, read-only deterministic tools."""

    @classmethod
    def execute(
        cls,
        db: Session,
        tenant_id: str,
        query: str,
        routing: RoutingDecision,
        parameters: Dict[str, Any] | None = None,
    ) -> ToolResult:

        tool = ToolRegistry.resolve_for_capability(routing.target_capability)
        if tool is not None and tool.side_effect:
            return ToolResult(
                success=False,
                tool_name=tool.name,
                capability=tool.capability,
                answer="The deterministic query path cannot execute side-effecting tools.",
                limitations=["SIDE_EFFECT_TOOL_BLOCKED"],
            )
        if tool is None:
            return ToolResult(
                success=False,
                tool_name="UNRESOLVED",
                capability=routing.target_capability,
                answer="No deterministic AURIX tool is registered for this capability.",
                limitations=["NO_DETERMINISTIC_TOOL"],
            )

        if routing.resolved_entity_id is None and tool.requires_entity:
            return ToolResult(
                success=False,
                tool_name=tool.name,
                capability=tool.capability,
                answer="A specific entity is required before this deterministic capability can run.",
                limitations=["ENTITY_REQUIRED"],
            )

        request = ToolRequest(
            tenant_id=tenant_id,
            query=query,
            tool_name=tool.name,
            entity_id=routing.resolved_entity_id,
            entity_type=routing.resolved_entity_type,
            parameters={
                **(parameters or {}),
            },
        )
        return ToolRegistry.execute(db, request)
