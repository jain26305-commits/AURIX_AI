"""
AURIX Process Intelligence — Object-Centric Process Mining (OCPM) Engine
Phase 25 Core Implementation.
Maps events across intersecting object instances (Customer, Order, Shipment, Invoice, WorkOrder).
"""

from __future__ import annotations

from typing import Any, Dict, List, Set
from aurix_core.process.contracts import OCPMObjectGraph, ProcessEvent, ProcessType


class OCPMEngine:
    """Builds Object-Centric Process graphs without forcing events into a single case ID."""

    @classmethod
    def build_ocpm_graph(
        cls,
        tenant_id: str,
        events: List[ProcessEvent],
        process_type: ProcessType = ProcessType.ORDER_TO_CASH,
    ) -> OCPMObjectGraph:
        """Construct multi-object event graph mapping many-to-many relationships."""
        proc_events = [e for e in events if e.process_type == process_type]
        object_types: Set[str] = set()

        for ev in proc_events:
            for obj_type in ev.object_bindings.keys():
                object_types.add(obj_type)

        return OCPMObjectGraph(
            tenant_id=tenant_id,
            process_type=process_type,
            total_events_count=len(proc_events),
            object_types_involved=list(object_types),
            events=proc_events,
        )
