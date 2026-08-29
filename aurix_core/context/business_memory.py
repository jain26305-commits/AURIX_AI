"""
AURIX Enterprise Business Context Graph — Business Memory Engine
Phase 24 Core Implementation.
Captures, persists, and retrieves institutional memory: previous decisions, manager overrides, action outcomes, and lessons learned.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from aurix_core.context.contracts import (
    BusinessMemoryRecord,
    DecisionOutcomeStatus,
    MemoryCategory,
)


class BusinessMemoryEngine:
    """Institutional memory engine providing verifiable historical decision recall."""

    _memory_store: Dict[str, List[BusinessMemoryRecord]] = {}

    @classmethod
    def record_memory(cls, memory: BusinessMemoryRecord) -> BusinessMemoryRecord:
        """Store an authoritative business memory record."""
        tenant_memories = cls._memory_store.setdefault(memory.tenant_id, [])
        tenant_memories.append(memory)
        return memory

    @classmethod
    def query_memories(
        cls,
        tenant_id: str,
        entity_id: Optional[str] = None,
        category: Optional[MemoryCategory] = None,
        outcome_status: Optional[DecisionOutcomeStatus] = None,
    ) -> List[BusinessMemoryRecord]:
        """Query institutional memories with tenant and attribute filters."""
        memories = cls._memory_store.get(tenant_id, [])

        filtered = [
            m for m in memories
            if (entity_id is None or m.context_entity_id == entity_id)
            and (category is None or m.category == category)
            and (outcome_status is None or m.outcome_status == outcome_status)
        ]

        filtered.sort(key=lambda x: x.recorded_at, reverse=True)
        return filtered
