"""Contracts for governed Phase 16 agent orchestration.

Agents orchestrate existing deterministic AURIX tools. They never bypass the
Phase 14 action executor and never own duplicate business calculations.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    SUPERVISOR = "SUPERVISOR"
    SUPPLIER = "SUPPLIER"
    PROCUREMENT = "PROCUREMENT"
    INVENTORY = "INVENTORY"
    MANUFACTURING = "MANUFACTURING"
    LOGISTICS = "LOGISTICS"
    FULFILLMENT = "FULFILLMENT"
    RISK = "RISK"
    FINANCE = "FINANCE"
    SCENARIO = "SCENARIO"
    EXECUTIVE = "EXECUTIVE"


class AutonomyLevel(int, Enum):
    OBSERVE = 0
    EXPLAIN = 1
    RECOMMEND = 2
    PREPARE_ACTION = 3
    EXECUTE_LOW_RISK = 4
    GOVERNED_ORCHESTRATION = 5


class AgentToolCall(BaseModel):
    tool_name: str
    capability: Optional[str] = None
    success: bool
    provenance: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)


class AgentRunResult(BaseModel):
    success: bool
    agent: AgentRole
    autonomy_level: AutonomyLevel = AutonomyLevel.RECOMMEND
    query: str
    answer: str
    answer_source: str = "AURIX_ENGINE"
    specialist_agents: List[AgentRole] = Field(default_factory=list)
    tool_calls: List[AgentToolCall] = Field(default_factory=list)
    facts: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    impact: Dict[str, Any] = Field(default_factory=dict)
    case_id: Optional[str] = None
    ai_provider: Optional[str] = None
    provenance: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class ControlTowerQuery(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    entity_id: Optional[str] = None
    autonomy_level: AutonomyLevel = AutonomyLevel.RECOMMEND
    auto_create_case: bool = False
