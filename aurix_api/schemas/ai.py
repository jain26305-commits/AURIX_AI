"""AI Copilot query requests, page-aware contexts, and response schemas for Phase 10 & Phase 12."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PageContextSchema(BaseModel):
    """Page-level active client context."""
    current_page: Optional[str] = None
    current_module: Optional[str] = None
    active_entity_type: Optional[str] = None
    active_entity_id: Optional[str] = None
    active_filters: Dict[str, Any] = Field(default_factory=dict)


class AiQueryRequest(BaseModel):
    """Input payload for user questions to the AI Copilot."""
    query: Optional[str] = None
    prompt: Optional[str] = None
    entity_id: Optional[str] = None
    conversation_id: Optional[str] = None
    page_context: Optional[PageContextSchema] = None
    analytical_data: Optional[Dict[str, Any]] = None


class AiQueryResponse(BaseModel):
    """Verified, grounded AI Copilot response with fully compatible attribute aliases."""
    response_id: str = "RESP-DEFAULT"
    response_type: str = "READ"
    headline: str
    response: Optional[str] = None
    summary: str = Field(default="")
    narrative: str = Field(default="")
    verified_facts: List[str] = Field(default_factory=list)
    explanation: str = Field(default="")
    recommendations: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    financial_impact: Dict[str, Any] = Field(default_factory=dict)
    operational_impact: Dict[str, Any] = Field(default_factory=dict)
    data_limitations: List[str] = Field(default_factory=list)
    source: str = "AURIX_DETERMINISTIC_PLATFORM"
    evidence_quality: str = "HIGH"
    freshness: str = "UNKNOWN"
    provider_used: str = "DETERMINISTIC_FALLBACK"
    model_used: str = "aurix-copilot-v1"
    is_fallback: bool = False
    confidence_score: float = 0.95
    token_usage: Dict[str, int] = Field(default_factory=dict)
    suggested_actions: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)


class ConversationMessageSchema(BaseModel):
    """Message item within a conversational memory thread."""
    message_id: str
    role: str
    content: str
    created_at: str


class ConversationCreateRequest(BaseModel):
    """Payload to initiate a new isolated conversation thread."""
    title: Optional[str] = None
    active_domain: Optional[str] = None