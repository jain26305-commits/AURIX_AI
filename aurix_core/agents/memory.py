"""
AURIX Governed Autonomous Agents — Governed Agent Memory Manager
Phase 29 Core Implementation.
Maintains short-term execution context while deferring authoritative business memory to Phase 24 Context Graph.
"""

from __future__ import annotations

from typing import Any, Dict, List


class AgentMemoryManager:
    """Manages short-term execution memory without duplicating authoritative enterprise databases."""

    _short_term_context: Dict[str, List[Dict[str, Any]]] = {}

    @classmethod
    def store_execution_context(cls, execution_id: str, key: str, value: Any) -> None:
        """Store transient execution context for multi-step agent workflows."""
        records = cls._short_term_context.setdefault(execution_id, [])
        records.append({"key": key, "value": value})

    @classmethod
    def get_execution_context(cls, execution_id: str) -> List[Dict[str, Any]]:
        """Retrieve short-term execution memory."""
        return cls._short_term_context.get(execution_id, [])
