"""
Deterministic AURIX Query Planning Contracts.

The planner converts natural-language enterprise questions into an explicit,
auditable execution plan before any deterministic tool is executed.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QueryIntent(str, Enum):
    READ = "READ"
    ANALYZE = "ANALYZE"
    EXPLAIN = "EXPLAIN"
    COMPARE = "COMPARE"
    RANK = "RANK"
    RECOMMEND = "RECOMMEND"
    SUMMARIZE = "SUMMARIZE"
    SIMULATE = "SIMULATE"
    TREND = "TREND"
    DIAGNOSE = "DIAGNOSE"


class OutputMode(str, Enum):
    ANSWER = "ANSWER"
    SUMMARY = "SUMMARY"
    TABLE = "TABLE"
    RANKING = "RANKING"
    COMPARISON = "COMPARISON"
    EXPLANATION = "EXPLANATION"
    RECOMMENDATION = "RECOMMENDATION"


class QueryEntity(BaseModel):
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    name: Optional[str] = None
    confidence: float = 0.0


class QueryMetric(BaseModel):
    name: str
    aliases: List[str] = Field(default_factory=list)
    aggregation: Optional[str] = None
    confidence: float = 0.0


class QueryTimeWindow(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None
    label: Optional[str] = None


class QueryFilter(BaseModel):
    field: str
    operator: str
    value: Any


class DeterministicOperation(BaseModel):
    operation_id: str
    tool_name: str
    capability: Optional[str] = None
    entity: Optional[QueryEntity] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    required: bool = True


class DeterministicQueryPlan(BaseModel):
    query: str
    normalized_query: str
    intent: QueryIntent
    confidence: float = 0.0

    entities: List[QueryEntity] = Field(default_factory=list)
    metrics: List[QueryMetric] = Field(default_factory=list)
    time_window: Optional[QueryTimeWindow] = None
    filters: List[QueryFilter] = Field(default_factory=list)

    operations: List[DeterministicOperation] = Field(default_factory=list)

    output_mode: OutputMode = OutputMode.ANSWER

    requires_historical_data: bool = False
    requires_cross_entity_analysis: bool = False
    requires_calculation: bool = False
    requires_recommendation: bool = False

    missing_requirements: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    provenance: Dict[str, Any] = Field(default_factory=dict)
