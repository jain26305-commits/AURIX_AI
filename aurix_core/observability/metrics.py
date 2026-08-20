"""Operational, Performance, and AI Cost Metrics Collector for AURIX Enterprise Platform."""

import logging
import threading
from pydantic import BaseModel

logger = logging.getLogger("aurix_core.observability.metrics")


class MetricsSnapshot(BaseModel):
    """Container for system-wide performance and operational metrics snapshot."""
    api_requests_total: int = 0
    api_errors_total: int = 0
    api_latency_seconds_sum: float = 0.0

    run_executions_total: int = 0
    run_failures_total: int = 0

    ai_requests_total: int = 0
    ai_tokens_input_total: int = 0
    ai_tokens_output_total: int = 0
    ai_estimated_cost_usd: float = 0.0
    ai_fallbacks_total: int = 0

    integration_syncs_total: int = 0
    integration_failures_total: int = 0

    events_processed_total: int = 0
    events_quarantined_total: int = 0

    actions_created_total: int = 0
    actions_approved_total: int = 0
    actions_executed_total: int = 0
    actions_failed_total: int = 0
    actions_compensated_total: int = 0

    deterministic_queries_total: int = 0
    deterministic_query_success_total: int = 0
    ai_escalations_total: int = 0
    tool_calls_total: int = 0
    tool_failures_total: int = 0
    agent_runs_total: int = 0
    agent_failures_total: int = 0
    decisions_total: int = 0


class MetricsRegistry:
    """Thread-safe global metrics registry tracking operational and AI cost telemetry."""

    _lock = threading.Lock()
    _metrics = MetricsSnapshot()

    @classmethod
    def increment_api_request(cls, is_error: bool = False, latency_seconds: float = 0.0) -> None:
        """Records an API request count, latency, and error state."""
        with cls._lock:
            cls._metrics.api_requests_total += 1
            if is_error:
                cls._metrics.api_errors_total += 1
            cls._metrics.api_latency_seconds_sum += latency_seconds

    @classmethod
    def record_run_execution(cls, success: bool) -> None:
        """Records an analytical run execution result."""
        with cls._lock:
            cls._metrics.run_executions_total += 1
            if not success:
                cls._metrics.run_failures_total += 1

    @classmethod
    def record_ai_usage(
        cls,
        input_tokens: int,
        output_tokens: int,
        provider: str,
        is_fallback: bool = False,
        estimated_cost_usd: float = 0.0,
    ) -> None:
        """Tracks AI usage using the authoritative settled cost when available."""
        _ = provider
        with cls._lock:
            cls._metrics.ai_requests_total += 1
            cls._metrics.ai_tokens_input_total += input_tokens
            cls._metrics.ai_tokens_output_total += output_tokens
            if is_fallback:
                cls._metrics.ai_fallbacks_total += 1

            cost = estimated_cost_usd
            if cost <= 0:
                cost = (
                    input_tokens / 1_000_000 * 0.15
                    + output_tokens / 1_000_000 * 0.60
                )
            cls._metrics.ai_estimated_cost_usd += cost

    @classmethod
    def record_integration_sync(cls, success: bool) -> None:
        """Records an external integration sync outcome."""
        with cls._lock:
            cls._metrics.integration_syncs_total += 1
            if not success:
                cls._metrics.integration_failures_total += 1

    @classmethod
    def record_event_processing(cls, quarantined: bool = False) -> None:
        """Records real-time event processing outcome."""
        with cls._lock:
            cls._metrics.events_processed_total += 1
            if quarantined:
                cls._metrics.events_quarantined_total += 1

    @classmethod
    def record_action_lifecycle(cls, state: str) -> None:
        """Records operational action state transitions."""
        with cls._lock:
            state_upper = state.upper()
            if state_upper == "CREATED":
                cls._metrics.actions_created_total += 1
            elif state_upper == "APPROVED":
                cls._metrics.actions_approved_total += 1
            elif state_upper in ("VERIFIED", "EXECUTED"):
                cls._metrics.actions_executed_total += 1
            elif state_upper in ("FAILED", "VERIFICATION_FAILED"):
                cls._metrics.actions_failed_total += 1
            elif state_upper == "COMPENSATION_REQUIRED":
                cls._metrics.actions_compensated_total += 1

    @classmethod
    def record_query_resolution(cls, deterministic: bool, success: bool) -> None:
        """Records whether a query was resolved by AURIX or escalated to AI."""
        with cls._lock:
            if deterministic:
                cls._metrics.deterministic_queries_total += 1
                if success:
                    cls._metrics.deterministic_query_success_total += 1
            else:
                cls._metrics.ai_escalations_total += 1

    @classmethod
    def record_tool_call(cls, success: bool) -> None:
        """Records deterministic tool-call outcomes."""
        with cls._lock:
            cls._metrics.tool_calls_total += 1
            if not success:
                cls._metrics.tool_failures_total += 1

    @classmethod
    def record_agent_run(cls, success: bool) -> None:
        """Records supervised agent-run outcomes."""
        with cls._lock:
            cls._metrics.agent_runs_total += 1
            if not success:
                cls._metrics.agent_failures_total += 1

    @classmethod
    def record_decision(cls) -> None:
        """Records a persisted Phase 16 decision record."""
        with cls._lock:
            cls._metrics.decisions_total += 1

    @classmethod
    def get_snapshot(cls) -> MetricsSnapshot:
        """Returns a thread-safe copy of the current metrics snapshot."""
        with cls._lock:
            return cls._metrics.model_copy()

    @classmethod
    def reset(cls) -> None:
        """Resets all metrics counters for clean test runs."""
        with cls._lock:
            cls._metrics = MetricsSnapshot()