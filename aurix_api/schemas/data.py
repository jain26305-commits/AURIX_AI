"""Data ingestion, validation, and dataset readiness schemas for Phase 10."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IngestionRecord(BaseModel):
    """Generic canonical data record container."""
    data: Dict[str, Any]


class DataIngestRequest(BaseModel):
    """Payload for submitting canonical domain datasets."""
    entity_name: str                               # e.g., demand_history, inventory_levels, purchase_orders
    records: List[Dict[str, Any]] = Field(default_factory=list)
    source_system: str = "REST_API"
    source_timestamp: Optional[str] = None
    is_incremental: bool = False
    key_fields: Optional[List[str]] = None


class DataIngestSummary(BaseModel):
    """Execution summary returned after dataset ingestion."""
    entity_name: str
    total_submitted: int
    total_accepted: int
    total_rejected: int
    duplicates_count: int = 0
    corrections_count: int = 0
    ingestion_run_id: str
    status: str
    quality_score: float = 1.0
    null_density_pct: float = 0.0


class EntityReadinessDetail(BaseModel):
    """Readiness metrics for an individual domain entity."""
    entity_name: str
    available: bool
    quality_score: float
    completeness_pct: float
    record_completeness_pct: float
    null_density_pct: float
    freshness: str
    freshness_age_hours: Optional[float] = None
    source_health: str
    missing_fields: List[str] = Field(default_factory=list)
    partially_populated_fields: List[str] = Field(default_factory=list)


class ReadinessResponse(BaseModel):
    """Portfolio-wide data readiness evaluation."""
    tenant_id: str
    entities: Dict[str, EntityReadinessDetail] = Field(default_factory=dict)
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())