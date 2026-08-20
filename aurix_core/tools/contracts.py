"""Contracts for deterministic AURIX tools used by the Query Router and agents."""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session


class ToolAccess(str, Enum):
    """Access classification for a deterministic tool."""

    READ = "READ"
    CALCULATE = "CALCULATE"


class ToolRequest(BaseModel):
    """Validated request passed from the router to a deterministic tool."""

    tenant_id: str
    query: str
    tool_name: str
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Structured, provenance-aware result returned by an AURIX tool."""

    success: bool
    tool_name: str
    capability: Optional[str] = None
    answer: str = ""
    data: Dict[str, Any] = Field(default_factory=dict)
    source: str = "AURIX_ENGINE"
    deterministic: bool = True
    provenance: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)


ToolHandler = Callable[[Session, ToolRequest], ToolResult]


class ToolDefinition(BaseModel):
    """Metadata describing one deterministic AURIX capability."""

    name: str
    description: str
    capability: Optional[str] = None
    access: ToolAccess = ToolAccess.READ
    domains: Sequence[str] = Field(default_factory=list)
    query_types: Sequence[str] = Field(default_factory=list)
    requires_entity: bool = False
    required_permissions: Sequence[str] = Field(default_factory=list)
    side_effect: bool = False
    risk_level: str = "READ_ONLY"
    handler: Optional[ToolHandler] = Field(default=None, exclude=True)

    model_config = {"arbitrary_types_allowed": True}
