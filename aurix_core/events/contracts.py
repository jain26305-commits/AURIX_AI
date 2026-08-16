"""Pydantic v2 data contracts, event status enums, taxonomy, and alert structures for Phase 13."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EventStatus(str, Enum):
    """Lifecycle states for real-time event processing."""
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    DUPLICATE = "DUPLICATE"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    QUARANTINED = "QUARANTINED"


class EventTaxonomy(str, Enum):
    """Clean operational event taxonomy mapped to AURIX analytical capabilities."""
    INVENTORY_UPDATED = "INVENTORY_UPDATED"
    DEMAND_UPDATED = "DEMAND_UPDATED"
    FORECAST_INPUT_CHANGED = "FORECAST_INPUT_CHANGED"
    SUPPLIER_UPDATED = "SUPPLIER_UPDATED"
    PURCHASE_ORDER_UPDATED = "PURCHASE_ORDER_UPDATED"
    SHIPMENT_UPDATED = "SHIPMENT_UPDATED"
    ETA_CHANGED = "ETA_CHANGED"
    LOCATION_UPDATED = "LOCATION_UPDATED"
    CAPACITY_UPDATED = "CAPACITY_UPDATED"
    NETWORK_UPDATED = "NETWORK_UPDATED"
    COST_UPDATED = "COST_UPDATED"
    SCENARIO_UPDATED = "SCENARIO_UPDATED"
    SOURCE_SYNC_COMPLETED = "SOURCE_SYNC_COMPLETED"
    SOURCE_SYNC_FAILED = "SOURCE_SYNC_FAILED"


class InternalEvent(BaseModel):
    """Normalized internal event contract bridging Phase 12 integrations and Phase 13 intelligence."""
    event_id: str = Field(..., description="Unique event identifier (e.g., EVT-12345)")
    tenant_id: str = Field(..., description="Strict tenant isolation boundary identifier")
    source_system: str = Field(..., description="Originating system (e.g., ERP_ODOO, WMS_GENERIC)")
    connector_id: Optional[str] = Field(default=None, description="Associated integration connector ID")
    event_type: EventTaxonomy = Field(..., description="Classified operational event type")
    entity_type: str = Field(..., description="Target domain entity (e.g., inventory, demand_history, shipments)")
    entity_id: str = Field(..., description="Primary entity identifier (e.g., SKU-101, SHPM-99)")
    changed_fields: List[str] = Field(default_factory=list, description="List of attributes modified in this event")
    event_timestamp: str = Field(..., description="Source-reported event timestamp ISO string")
    received_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Platform ingestion receipt timestamp"
    )
    payload_hash: str = Field(..., description="SHA-256 idempotency payload hash")
    source_record_id: Optional[str] = Field(default=None, description="Upstream source record ID")
    ingestion_run_id: Optional[str] = Field(default=None, description="Associated Phase 12 sync run ID")
    correlation_id: Optional[str] = Field(default=None, description="Distributed correlation trace ID")
    causation_id: Optional[str] = Field(default=None, description="Causation ID triggering this event")
    schema_version: int = Field(default=1, description="Event schema version for backward compatibility")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Raw or normalized entity state snapshot")
    status: EventStatus = Field(default=EventStatus.RECEIVED, description="Current event processing state")
    attempt_count: int = Field(default=0, description="Number of processing attempts executed")
    last_error: Optional[str] = Field(default=None, description="Last recorded failure message if any")


class AlertSeverity(str, Enum):
    """Operational alert severity classification."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    """Lifecycle status of generated operational alerts."""
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    SUPPRESSED = "SUPPRESSED"


class AlertContract(BaseModel):
    """Normalized internal alert contract for event-driven exceptions and risks."""
    alert_id: str = Field(..., description="Unique alert identifier")
    tenant_id: str = Field(..., description="Tenant scope identifier")
    severity: AlertSeverity = Field(..., description="Severity classification")
    event_id: Optional[str] = Field(default=None, description="Triggering event ID")
    capability_name: Optional[str] = Field(default=None, description="Affected AURIX analytical capability")
    entity_id: str = Field(..., description="Impacted entity identifier (SKU, facility, shipment)")
    title: str = Field(..., description="Concise alert title")
    description: str = Field(..., description="Detailed operational context and risk description")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Alert generation timestamp"
    )
    status: AlertStatus = Field(default=AlertStatus.ACTIVE, description="Current alert status")
    evidence_reference: Dict[str, Any] = Field(default_factory=dict, description="Underlying metric values or facts")
    deduplication_key: str = Field(..., description="Deterministic key for duplicate alert suppression")