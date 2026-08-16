"""Run/Job dispatch, lifecycle polling, and execution summary schemas for Phase 10."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RunExecutionMode(str, Enum):
    """Execution mode: synchronous immediate vs background job."""
    SYNCHRONOUS = "SYNCHRONOUS"
    BACKGROUND = "BACKGROUND"


class RunStatus(str, Enum):
    """Job lifecycle states."""
    QUEUED = "QUEUED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    WAITING_FOR_INPUT = "WAITING_FOR_INPUT"
    FAILED = "FAILED"


class RunCreateRequest(BaseModel):
    """Payload for submitting a new analytical intelligence run."""
    execution_mode: RunExecutionMode = RunExecutionMode.SYNCHRONOUS
    canonical_datasets: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    incremental_update: Optional[Dict[str, Any]] = None
    configuration_overrides: Dict[str, Any] = Field(default_factory=dict)


class RunStatusResponse(BaseModel):
    """Standardized response tracking an analytical execution run."""
    run_id: str
    tenant_id: str
    status: RunStatus
    dataset_hash: Optional[str] = None
    idempotent_hit: bool = False
    executed_capabilities_count: int = 0
    recomputed_capabilities: List[str] = Field(default_factory=list)
    cached_capabilities: List[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    created_at: str
    completed_at: Optional[str] = None
    error_summary: Optional[str] = None
    provenance: Dict[str, Any] = Field(default_factory=dict)


class RunSummaryItem(BaseModel):
    """Brief metadata summary for an execution run in history listings."""
    run_id: str
    status: str
    dataset_hash: Optional[str] = None
    created_at: str
    executed_capabilities_count: int = 0


class RunListResponse(BaseModel):
    """Paginated listing of past execution runs."""
    total_count: int
    runs: List[RunSummaryItem] = Field(default_factory=list)