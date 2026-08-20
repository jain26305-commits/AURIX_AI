"""Step 1 hardening tests for deterministic-first Phase 16 architecture."""

from aurix_core.intelligence.router import BusinessRouter, QueryType
from aurix_core.phase16.case_service import _ALLOWED_CASE_TRANSITIONS
from aurix_core.tools.registry import ToolRegistry


def test_read_queries_use_registered_deterministic_tools() -> None:
    decision = BusinessRouter.route("show current inventory for SKU-100")
    assert decision.query_type == QueryType.READ
    assert decision.target_tool == "inventory.position"
    assert decision.requires_ai is False
    assert decision.fast_path_eligible is True


def test_scenario_queries_are_deterministic_when_tool_is_available() -> None:
    decision = BusinessRouter.route("what if supplier delay is 7 days")
    assert decision.query_type == QueryType.SIMULATE
    assert decision.target_tool == "phase16.scenario"
    assert decision.requires_ai is False


def test_all_registered_tools_are_non_side_effecting() -> None:
    assert ToolRegistry.list_definitions()
    assert all(tool.side_effect is False for tool in ToolRegistry.list_definitions())


def test_case_state_machine_is_closed_and_monotonic() -> None:
    assert "CLOSED" in _ALLOWED_CASE_TRANSITIONS
    assert _ALLOWED_CASE_TRANSITIONS["CLOSED"] == set()
