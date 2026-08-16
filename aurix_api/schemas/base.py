"""Standard API response envelopes, generic wrappers, and base schemas for Phase 10."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseStatus(str, Enum):
    """Standardized API execution status codes."""
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"
    USER_INPUT_REQUIRED = "USER_INPUT_REQUIRED"
    DUPLICATE = "DUPLICATE"


class ResponseMetadata(BaseModel):
    """Execution metadata attached to API responses."""
    tenant_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    engine_version: str = "10.0.0-api-platform"
    additional_info: Dict[str, Any] = Field(default_factory=dict)


class ApiResponse(BaseModel, Generic[T]):
    """Standardized success response envelope for all versioned API endpoints."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    request_id: str = Field(default_factory=lambda: f"REQ-{uuid.uuid4().hex[:12].upper()}")
    data: Optional[T] = None
    meta: Optional[ResponseMetadata] = None


class ErrorDetail(BaseModel):
    """Granular error breakdown for validation or operational failures."""
    field: Optional[str] = None
    issue: str
    message: str


class ApiErrorPayload(BaseModel):
    """Inner payload structure for error responses."""
    code: str
    message: str
    details: List[ErrorDetail] = Field(default_factory=list)


class ApiErrorResponse(BaseModel):
    """Standardized error response envelope."""
    status: ResponseStatus = ResponseStatus.FAILED
    request_id: str = Field(default_factory=lambda: f"REQ-{uuid.uuid4().hex[:12].upper()}")
    error: ApiErrorPayload
    meta: Optional[ResponseMetadata] = None