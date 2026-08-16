"""Real-Time & Event-Driven Intelligence Module Namespace (Phase 13)."""

from aurix_core.events.contracts import (
    AlertContract,
    AlertSeverity,
    AlertStatus,
    EventStatus,
    EventTaxonomy,
    InternalEvent,
)
from aurix_core.events.router import EventRouter, EventRoutingDecision
from aurix_core.events.processor import EventProcessor, EventProcessingResult

__all__ = [
    "EventStatus",
    "EventTaxonomy",
    "InternalEvent",
    "AlertSeverity",
    "AlertStatus",
    "AlertContract",
    "EventRouter",
    "EventRoutingDecision",
    "EventProcessor",
    "EventProcessingResult",
]