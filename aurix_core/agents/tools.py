"""
AURIX Governed Autonomous Agents — Tool Registry
Phase 29 Production Hardened.
Manages internal connector tools with distributed Redis rate limiting and tenant-scoped 3-state circuit breakers.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from aurix_core.agents.contracts import CircuitState, RiskLevel, ToolDefinition

try:
    import redis
    _redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    _redis_client: Optional[redis.Redis] = redis.from_url(_redis_url, decode_responses=True)
except Exception:
    _redis_client = None


class ToolRegistry:
    """Governed tool registry enforcing distributed rate limits and tenant-isolated circuit breaker logic."""

    _tools: Dict[str, ToolDefinition] = {
        "ERP_PO_API": ToolDefinition(
            tool_id="TLS-ERP-PO",
            name="ERP_PO_API",
            version="v1.0",
            endpoint_ref="/api/v1/erp/purchase-orders",
            risk_level=RiskLevel.HIGH,
            rate_limit_per_min=30,
        ),
        "ERP_INVOICE_API": ToolDefinition(
            tool_id="TLS-ERP-INV",
            name="ERP_INVOICE_API",
            version="v1.0",
            endpoint_ref="/api/v1/erp/invoices",
            risk_level=RiskLevel.LOW,
            rate_limit_per_min=120,
        ),
    }

    _call_history: Dict[str, List[float]] = {}
    _circuit_states: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register_tool(cls, tool: ToolDefinition, db: Optional[Session] = None) -> ToolDefinition:
        """Register tool in persistent registry and memory cache."""
        cls._tools[tool.name] = tool
        if db is not None:
            from aurix_core.database.models.agents import ToolRegistryModel
            rec = db.query(ToolRegistryModel).filter(ToolRegistryModel.name == tool.name).first()
            if not rec:
                rec = ToolRegistryModel(
                    id=tool.tool_id,
                    name=tool.name,
                    version=tool.version,
                    endpoint_ref=tool.endpoint_ref,
                    risk_level=tool.risk_level.value,
                    rate_limit_per_min=tool.rate_limit_per_min,
                    circuit_state=tool.circuit_state.value,
                    failure_count=tool.failure_count,
                )
                db.add(rec)
            else:
                rec.rate_limit_per_min = tool.rate_limit_per_min
                rec.circuit_state = tool.circuit_state.value
            try:
                db.commit()
            except Exception:
                db.rollback()
        return tool

    @classmethod
    def get_tool(cls, tool_name: str, db: Optional[Session] = None) -> Optional[ToolDefinition]:
        """Retrieve tool definition from DB or cache."""
        if tool_name in cls._tools:
            return cls._tools[tool_name]
        if db is not None:
            from aurix_core.database.models.agents import ToolRegistryModel
            rec = db.query(ToolRegistryModel).filter(ToolRegistryModel.name == tool_name).first()
            if rec:
                t = ToolDefinition(
                    tool_id=rec.id,
                    name=rec.name,
                    version=rec.version,
                    endpoint_ref=rec.endpoint_ref,
                    risk_level=RiskLevel(rec.risk_level),
                    rate_limit_per_min=rec.rate_limit_per_min,
                    circuit_state=CircuitState(rec.circuit_state),
                    failure_count=rec.failure_count,
                )
                cls._tools[rec.name] = t
                return t
        return None

    @classmethod
    def check_rate_limit(cls, tool_name: str, tenant_id: str = "GLOBAL") -> bool:
        """Sliding-window rate limiter enforcing tool invocation quotas (Distributed Redis with In-Memory fallback)."""
        tool = cls.get_tool(tool_name)
        if not tool:
            return False

        now = time.time()
        key = f"aurix:ratelimit:{tenant_id}:{tool_name}"

        if _redis_client is not None:
            try:
                pipe = _redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, now - 60.0)
                pipe.zcard(key)
                pipe.zadd(key, {str(now): now})
                pipe.expire(key, 60)
                results = pipe.execute()
                current_count = results[1]
                if current_count >= tool.rate_limit_per_min:
                    return False
                return True
            except Exception:
                pass

        # Fallback in-memory sliding window
        local_key = f"{tenant_id}:{tool_name}"
        calls = cls._call_history.setdefault(local_key, [])
        cls._call_history[local_key] = [t for t in calls if now - t < 60.0]
        if len(cls._call_history[local_key]) >= tool.rate_limit_per_min:
            return False
        cls._call_history[local_key].append(now)
        return True

    @classmethod
    def record_tool_result(
        cls,
        tool_name: str,
        success: bool,
        tenant_id: str = "GLOBAL",
        cooldown_seconds: float = 60.0,
    ) -> None:
        """Update tenant-scoped circuit breaker state in distributed Redis and local cache."""
        tool = cls.get_tool(tool_name)
        now = time.time()
        key = f"aurix:circuit:{tenant_id}:{tool_name}"

        if _redis_client is not None:
            try:
                if success:
                    _redis_client.hset(key, mapping={"state": CircuitState.CLOSED.value, "failures": 0, "last_failure": 0.0})
                else:
                    curr_fail = int(_redis_client.hget(key, "failures") or 0) + 1
                    new_state = CircuitState.OPEN.value if curr_fail >= 5 else CircuitState.CLOSED.value
                    _redis_client.hset(key, mapping={"state": new_state, "failures": curr_fail, "last_failure": now})
            except Exception:
                pass

        # Maintain tenant-isolated local state
        local_key = f"{tenant_id}:{tool_name}"
        state_data = cls._circuit_states.setdefault(
            local_key, {"state": CircuitState.CLOSED, "failures": 0, "last_failure": 0.0}
        )
        if success:
            state_data["failures"] = 0
            state_data["state"] = CircuitState.CLOSED
            if tool:
                tool.circuit_state = CircuitState.CLOSED
                tool.failure_count = 0
        else:
            state_data["failures"] += 1
            state_data["last_failure"] = now
            if state_data["failures"] >= 5:
                state_data["state"] = CircuitState.OPEN
                if tool:
                    tool.circuit_state = CircuitState.OPEN
                    tool.failure_count = state_data["failures"]

    @classmethod
    def is_circuit_open(
        cls,
        tool_name: str,
        tenant_id: str = "GLOBAL",
        cooldown_seconds: float = 60.0,
    ) -> bool:
        """Check if tenant-scoped circuit breaker is actively blocking calls."""
        now = time.time()
        key = f"aurix:circuit:{tenant_id}:{tool_name}"

        if _redis_client is not None:
            try:
                data = _redis_client.hgetall(key)
                if data and data.get("state") == CircuitState.OPEN.value:
                    last_failure = float(data.get("last_failure") or 0.0)
                    if now - last_failure > cooldown_seconds:
                        _redis_client.hset(key, "state", CircuitState.HALF_OPEN.value)
                        return False
                    return True
                elif data and data.get("state") == CircuitState.HALF_OPEN.value:
                    return False
            except Exception:
                pass

        # Fallback in-memory check
        local_key = f"{tenant_id}:{tool_name}"
        state_data = cls._circuit_states.get(local_key)
        if not state_data or state_data["state"] == CircuitState.CLOSED:
            return False
        if state_data["state"] == CircuitState.OPEN:
            if now - state_data["last_failure"] > cooldown_seconds:
                state_data["state"] = CircuitState.HALF_OPEN
                return False
            return True
        return False
