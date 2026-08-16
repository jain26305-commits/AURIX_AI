"""Pydantic request and response schemas for Integration Hub API endpoints in Phase 12."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from aurix_core.integrations.contracts import (
    AuthConfig,
    IntegrationFamily,
    ReconciliationRecord,
    SyncMode
)


class ConnectorCreateRequest(BaseModel):
    """Payload to register a new external data connector."""
    name: str = Field(..., min_length=2, max_length=100, description="Display name for the connector")
    family: IntegrationFamily = Field(default=IntegrationFamily.REST)
    adapter_type: str = Field(..., description="Registered adapter class (generic_rest, erp_odoo, generic_wms, sftp)")
    base_url: Optional[str] = None
    auth_config: AuthConfig = Field(default_factory=AuthConfig)
    schedule_cron: Optional[str] = None
    enabled: bool = True
    custom_settings: Dict[str, Any] = Field(default_factory=dict)


class ConnectorUpdateRequest(BaseModel):
    """Payload to update an existing connector configuration."""
    name: Optional[str] = None
    base_url: Optional[str] = None
    auth_config: Optional[AuthConfig] = None
    schedule_cron: Optional[str] = None
    enabled: Optional[bool] = None
    custom_settings: Optional[Dict[str, Any]] = None


class TriggerSyncRequest(BaseModel):
    """Payload to trigger a data synchronization execution."""
    mode: SyncMode = Field(default=SyncMode.INCREMENTAL)
    entity_name: str = Field(default="demand_history")
    key_field: str = Field(default="sku_id")
    source_id_field: str = Field(default="id")
    batch_size: int = Field(default=1000, ge=1, le=10000)


class ReconcileDatasetsRequest(BaseModel):
    """Payload to execute multi-source variance reconciliation."""
    entity_type: str = Field(..., description="Business domain entity (e.g. inventory, orders)")
    dataset_a: List[Dict[str, Any]] = Field(..., description="Primary authoritative dataset")
    source_a: str = Field(default="ERP")
    dataset_b: List[Dict[str, Any]] = Field(..., description="Secondary authoritative dataset")
    source_b: str = Field(default="WMS")
    key_field: str = Field(default="sku_id")
    metric_field: str = Field(default="inventory_level")
    material_threshold_pct: Optional[float] = Field(default=5.0)


class ReconciliationSummaryResponse(BaseModel):
    """Summary result of a dataset reconciliation pass."""
    total_entities_evaluated: int
    matched_count: int
    minor_variance_count: int
    material_variance_count: int
    unresolved_count: int
    audit_trail: List[ReconciliationRecord] = Field(default_factory=list)
    reconciled_dataset_sample: List[Dict[str, Any]] = Field(default_factory=list)