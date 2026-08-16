"""Pydantic v2 contracts, enums, and data schemas for Universal Integration Hub (Phase 12)."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IntegrationFamily(str, Enum):
    """Categorical classification of integration source systems."""
    ERP = "ERP"
    WMS = "WMS"
    TMS = "TMS"
    MES = "MES"
    CRM = "CRM"
    ECOMMERCE = "ECOMMERCE"
    POS = "POS"
    SUPPLIER = "SUPPLIER"
    CUSTOMER = "CUSTOMER"
    EDI = "EDI"
    SFTP = "SFTP"
    REST = "REST"
    WEBHOOK = "WEBHOOK"
    IOT = "IOT"
    TELEMATICS = "TELEMATICS"
    EXTERNAL_FEED = "EXTERNAL_FEED"
    CUSTOM = "CUSTOM"


class ConnectorLifecycleState(str, Enum):
    """Execution lifecycle state for a connector execution pipeline."""
    CONFIGURED = "CONFIGURED"
    AUTHENTICATING = "AUTHENTICATING"
    CONNECTED = "CONNECTED"
    DISCOVERING = "DISCOVERING"
    SYNCING = "SYNCING"
    VALIDATING = "VALIDATING"
    NORMALIZING = "NORMALIZING"
    PERSISTING = "PERSISTING"
    RECONCILING = "RECONCILING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"


class ConnectorHealthState(str, Enum):
    """Health classification for an external integration endpoint."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DELAYED = "DELAYED"
    FAILED = "FAILED"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    SCHEMA_ERROR = "SCHEMA_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    UNKNOWN = "UNKNOWN"


class SyncMode(str, Enum):
    """Operational mode for data synchronization."""
    INITIAL_FULL = "INITIAL_FULL"
    INCREMENTAL = "INCREMENTAL"
    MANUAL = "MANUAL"
    EVENT_DRIVEN = "EVENT_DRIVEN"


class SyncStatus(str, Enum):
    """Execution status for a synchronization run."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AuthType(str, Enum):
    """Supported authentication mechanisms for external systems."""
    NONE = "NONE"
    API_KEY = "API_KEY"
    BEARER_TOKEN = "BEARER_TOKEN"
    BASIC_AUTH = "BASIC_AUTH"
    OAUTH2_CLIENT_CREDENTIALS = "OAUTH2_CLIENT_CREDENTIALS"
    HMAC_SIGNATURE = "HMAC_SIGNATURE"


class ReconciliationStatus(str, Enum):
    """Classification of multi-source data comparisons and variances."""
    MATCHED = "MATCHED"
    MINOR_VARIANCE = "MINOR_VARIANCE"
    MATERIAL_VARIANCE = "MATERIAL_VARIANCE"
    UNRESOLVED = "UNRESOLVED"
    NOT_RECONCILABLE = "NOT_RECONCILABLE"


class SecretRef(BaseModel):
    """Reference identifier for credentials resolved securely at runtime without plaintext database storage."""
    secret_id: str = Field(..., description="Unique secret identifier or key vault key")
    key_name: Optional[str] = Field(default=None, description="Specific sub-key name within secret vault")
    provider_type: str = Field(default="ENVIRONMENT", description="Secret provider backend (e.g. ENVIRONMENT, VAULT)")
    env_fallback: Optional[str] = Field(default=None, description="Environment variable fallback name")


class AuthConfig(BaseModel):
    """Authentication configuration containing non-plaintext credential references."""
    auth_type: AuthType = AuthType.NONE
    secret_ref: Optional[SecretRef] = None
    token_url: Optional[str] = None
    client_id: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)
    custom_headers: Dict[str, str] = Field(default_factory=dict)
    custom_params: Dict[str, str] = Field(default_factory=dict)


class ConnectorConfig(BaseModel):
    """Tenant-scoped connector configuration and state metadata."""
    connector_id: str = Field(..., description="Unique connector identifier")
    tenant_id: str = Field(..., description="Tenant identifier owning this connector")
    name: str = Field(..., description="Human-readable connector name")
    family: IntegrationFamily = IntegrationFamily.REST
    adapter_type: str = Field(..., description="Registered adapter class name (e.g. generic_rest, erp_odoo)")
    base_url: Optional[str] = None
    auth_config: AuthConfig = Field(default_factory=AuthConfig)
    schedule_cron: Optional[str] = None
    enabled: bool = True
    cursor: Optional[Dict[str, Any]] = Field(default=None, description="Last recorded sync cursor/checkpoint")
    last_sync_timestamp: Optional[str] = None
    last_sync_status: Optional[SyncStatus] = None
    health_state: ConnectorHealthState = ConnectorHealthState.UNKNOWN
    source_timezone: str = "UTC"
    custom_settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SyncRunRecord(BaseModel):
    """Historical record representing an individual synchronization execution."""
    sync_run_id: str
    tenant_id: str
    connector_id: str
    sync_mode: SyncMode
    status: SyncStatus = SyncStatus.QUEUED
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    records_received: int = 0
    records_accepted: int = 0
    records_rejected: int = 0
    cursor_before: Optional[Dict[str, Any]] = None
    cursor_after: Optional[Dict[str, Any]] = None
    input_hash: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    error_summary: Optional[str] = None
    affected_capabilities: List[str] = Field(default_factory=list)
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)


class SourceLineageRecord(BaseModel):
    """Source-to-canonical record lineage tracking schema."""
    lineage_id: str
    tenant_id: str
    source_system: str
    connector_id: str
    source_record_id: str
    source_timestamp: Optional[str] = None
    canonical_entity: str
    canonical_record_id: str
    sync_run_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ReconciliationRecord(BaseModel):
    """Data reconciliation record comparing values across distinct authoritative systems."""
    reconciliation_id: str
    tenant_id: str
    entity_type: str
    entity_key: str
    primary_source: str
    primary_value: float
    secondary_source: str
    secondary_value: float
    absolute_difference: float
    variance_pct: float
    reconciliation_status: ReconciliationStatus
    resolution_applied: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class IntegrationHealthReport(BaseModel):
    """Comprehensive health and reliability metrics for a connector."""
    connector_id: str
    tenant_id: str
    health_state: ConnectorHealthState
    last_successful_sync: Optional[str] = None
    last_attempt: Optional[str] = None
    success_rate_pct: float = 100.0
    records_processed_24h: int = 0
    records_rejected_24h: int = 0
    average_latency_ms: float = 0.0
    error_summary: Optional[str] = None


class WebhookEventPayload(BaseModel):
    """Standardized event intake container for incoming webhooks."""
    event_id: str
    tenant_id: str
    source_system: str
    connector_id: Optional[str] = None
    event_type: str
    entity_type: str
    event_timestamp: str
    received_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload: Dict[str, Any] = Field(default_factory=dict)
    signature: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)