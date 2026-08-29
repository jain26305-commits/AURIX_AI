"""
AURIX Enterprise Data Fabric — Ingestion & Model Contracts
Phase 19 Core Contract Definitions.
Authoritative schema contracts for multi-source enterprise data intake.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class CanonicalEntityType(str, Enum):
    """Authoritative Canonical Entity Types for AURIX Enterprise Data Fabric."""
    TENANT = "tenant"
    USER = "user"
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    PRODUCT = "product"
    SKU = "sku"
    MATERIAL = "material"
    LOCATION = "location"
    WAREHOUSE = "warehouse"
    PLANT = "plant"
    ORDER = "order"
    ORDER_LINE = "order_line"
    PURCHASE_ORDER = "purchase_order"
    PURCHASE_ORDER_LINE = "purchase_order_line"
    SHIPMENT = "shipment"
    DELIVERY = "delivery"
    INVOICE = "invoice"
    INVOICE_LINE = "invoice_line"
    PAYMENT = "payment"
    INVENTORY_POSITION = "inventory_position"
    INVENTORY_TRANSACTION = "inventory_transaction"
    BOM = "bom"
    WORK_ORDER = "work_order"
    PRODUCTION_EVENT = "production_event"
    RETURN = "return"
    CONTRACT = "contract"
    PRICE = "price"
    CUSTOMER_CREDIT = "customer_credit"
    SUPPLIER_PERFORMANCE = "supplier_performance"
    CONNECTOR = "connector"
    SYNC_RUN = "sync_run"
    SYNC_CHECKPOINT = "sync_checkpoint"
    SOURCE_RECORD = "source_record"
    LINEAGE_RECORD = "lineage_record"


class DataFreshnessState(str, Enum):
    """Derived real-time source freshness classification."""
    LIVE = "LIVE"
    RECENT = "RECENT"
    SYNCING = "SYNCING"
    DELAYED = "DELAYED"
    STALE = "STALE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"


class SyncMode(str, Enum):
    """Synchronization execution mode."""
    FULL_SNAPSHOT = "FULL_SNAPSHOT"
    INCREMENTAL_CURSOR = "INCREMENTAL_CURSOR"
    CDC_STREAM = "CDC_STREAM"
    DELTA_WATERMARK = "DELTA_WATERMARK"


class SyncStatus(str, Enum):
    """Lifecycle status of a synchronization batch."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ResolutionStatus(str, Enum):
    """Entity resolution match status."""
    RESOLVED_EXACT = "RESOLVED_EXACT"
    RESOLVED_ALIAS = "RESOLVED_ALIAS"
    RESOLVED_FUZZY = "RESOLVED_FUZZY"
    AMBIGUOUS_REVIEW_REQUIRED = "AMBIGUOUS_REVIEW_REQUIRED"
    UNRESOLVED = "UNRESOLVED"


class DriftType(str, Enum):
    """Classification of detected schema drift."""
    FIELD_ADDED = "FIELD_ADDED"
    FIELD_REMOVED = "FIELD_REMOVED"
    TYPE_CHANGED = "TYPE_CHANGED"
    NULLABILITY_CHANGED = "NULLABILITY_CHANGED"
    SEMANTIC_DRIFT = "SEMANTIC_DRIFT"


class ErrorSeverity(str, Enum):
    """Severity rating for data fabric issues."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SourceRecordEnvelope(BaseModel):
    """Wrapper holding raw unadulterated source payloads with audit metadata."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    tenant_id: str
    source_system: str
    source_entity_type: str
    source_record_id: str
    source_version: Optional[str] = "1.0"
    payload: Dict[str, Any]
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ingestion_batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw_hash: Optional[str] = None


class NormalizedRecordEnvelope(BaseModel):
    """Normalized canonical payload preserving source linkage and transformation version."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    tenant_id: str
    canonical_entity_type: CanonicalEntityType
    canonical_id: str
    source_system: str
    source_record_id: str
    transformation_version: str = "1.0.0"
    normalized_data: Dict[str, Any]
    source_data_snapshot: Dict[str, Any]
    lineage_metadata: Dict[str, Any] = Field(default_factory=dict)
    normalized_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CheckpointContract(BaseModel):
    """Stateful checkpoint tracking cursor position and watermarks."""
    model_config = ConfigDict(extra="ignore")

    tenant_id: str
    connector_id: str
    stream_name: str
    cursor_field: Optional[str] = None
    cursor_value: Optional[str] = None
    high_watermark: Optional[datetime] = None
    rows_synced_total: int = 0
    last_successful_sync_at: Optional[datetime] = None
    last_attempted_sync_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    state_metadata: Dict[str, Any] = Field(default_factory=dict)


class QuarantineEnvelope(BaseModel):
    """Isolated invalid or un-normalizable record payload with failure diagnostics."""
    model_config = ConfigDict(extra="allow")

    quarantine_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    source_system: str
    source_entity: str
    source_record_id: Optional[str] = None
    raw_payload: Dict[str, Any]
    failure_stage: str
    failure_reason: str
    error_code: str
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    retryable: bool = False
    retry_count: int = 0
    resolved: bool = False
    resolution_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FieldContract(BaseModel):
    """Individual field contract assertion."""
    field_name: str
    target_type: str
    required: bool = False
    nullable: bool = True
    semantic_role: Optional[str] = None
    default_value: Optional[Any] = None
    regex_pattern: Optional[str] = None


class DatasetContract(BaseModel):
    """Versioned schema contract for an ingestion boundary."""
    contract_id: str
    contract_version: str = "1.0.0"
    canonical_entity_type: CanonicalEntityType
    fields: List[FieldContract]
    allow_unmapped_fields: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
