"""Deterministic Event Router and Impact Analysis Engine for Phase 13."""

import logging
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from aurix_core.events.contracts import EventTaxonomy, InternalEvent
from aurix_core.intelligence.incremental import IncrementalMergeEngine

logger = logging.getLogger("aurix_core.events.router")


class EventRoutingDecision(BaseModel):
    """Result of event impact analysis and capability invalidation routing."""

    event_id: str
    tenant_id: str
    event_type: EventTaxonomy
    canonical_entity_name: str
    entity_id: str
    dirty_capabilities: List[str] = Field(default_factory=list)
    requires_recomputation: bool = True
    routing_metadata: Dict[str, Any] = Field(default_factory=dict)


class EventRouter:
    """Deterministic Event Router mapping incoming operational events to dirty capability branches."""

    EVENT_ENTITY_MAP: Dict[EventTaxonomy, str] = {
        EventTaxonomy.INVENTORY_UPDATED: "inventory_levels",
        EventTaxonomy.DEMAND_UPDATED: "demand_history",
        EventTaxonomy.FORECAST_INPUT_CHANGED: "demand_history",
        EventTaxonomy.SUPPLIER_UPDATED: "supplier_catalog",
        EventTaxonomy.PURCHASE_ORDER_UPDATED: "purchase_orders",
        EventTaxonomy.SHIPMENT_UPDATED: "shipments",
        EventTaxonomy.ETA_CHANGED: "shipments",
        EventTaxonomy.LOCATION_UPDATED: "network_nodes",
        EventTaxonomy.CAPACITY_UPDATED: "network_nodes",
        EventTaxonomy.NETWORK_UPDATED: "network_nodes",
        EventTaxonomy.COST_UPDATED: "item_costs",
        EventTaxonomy.SCENARIO_UPDATED: "scenario_parameters",
        EventTaxonomy.SOURCE_SYNC_COMPLETED: "demand_history",
        EventTaxonomy.SOURCE_SYNC_FAILED: "demand_history",
    }

    @classmethod
    def route_event(cls, event: InternalEvent) -> EventRoutingDecision:
        """Analyze an internal event and resolve its dirty capability branches."""
        canonical_entity = cls.EVENT_ENTITY_MAP.get(event.event_type, event.entity_type)
        dirty_caps = IncrementalMergeEngine.ENTITY_CAPABILITY_GRAPH.get(
            canonical_entity,
            [],
        )
        requires_recompute = (
            len(dirty_caps) > 0
            and event.event_type != EventTaxonomy.SOURCE_SYNC_FAILED
        )

        logger.debug(
            "Event routed [ID: %s, Type: %s] -> Entity [%s] -> Dirty Capabilities: %s",
            event.event_id,
            event.event_type,
            canonical_entity,
            dirty_caps,
        )

        return EventRoutingDecision(
            event_id=event.event_id,
            tenant_id=event.tenant_id,
            event_type=event.event_type,
            canonical_entity_name=canonical_entity,
            entity_id=event.entity_id,
            dirty_capabilities=sorted(list(set(dirty_caps))),
            requires_recomputation=requires_recompute,
            routing_metadata={
                "source_system": event.source_system,
                "changed_fields": event.changed_fields,
                "schema_version": event.schema_version,
            },
        )