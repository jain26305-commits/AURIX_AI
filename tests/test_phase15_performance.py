"""Empirical Micro-Benchmarking and Concurrency Load Test Suite for AURIX Platform (Phase 15)."""

import threading
import time
import unittest
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi.testclient import TestClient

from aurix_api.app import create_app
from aurix_api.runs.manager import RunManager
from aurix_api.security.auth import create_access_token
from aurix_core.actions.contracts import ActionCategory, ActionState, ActionType
from aurix_core.actions.executor import ActionExecutor
from aurix_core.database.engine import Base, SessionLocal, engine
from aurix_core.events.contracts import EventTaxonomy, InternalEvent
from aurix_core.events.processor import EventProcessor
from aurix_core.observability.metrics import MetricsRegistry


def compute_percentiles(latencies_ms: List[float]) -> Dict[str, float]:
    """Calculates deterministic p50, p95, and p99 latency percentiles from measured durations."""
    if not latencies_ms:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0}

    sorted_lat = sorted(latencies_ms)
    n = len(sorted_lat)
    p50 = sorted_lat[int(n * 0.50)]
    p95 = sorted_lat[min(int(n * 0.95), n - 1)]
    p99 = sorted_lat[min(int(n * 0.99), n - 1)]
    avg = sum(sorted_lat) / n

    return {
        "p50": round(p50, 3),
        "p95": round(p95, 3),
        "p99": round(p99, 3),
        "avg": round(avg, 3),
    }


class TestPhase15Performance(unittest.TestCase):
    """Performance benchmarks measuring empirical execution latencies and concurrency contention."""

    app: Any
    client: TestClient
    token_admin: str

    @classmethod
    def setUpClass(cls) -> None:
        """Initializes test harness, database schema, and test tokens."""
        Base.metadata.create_all(bind=engine)
        cls.app = create_app()
        cls.client = TestClient(cls.app)
        cls.token_admin = create_access_token({
            "sub": "perf_admin",
            "tenant_id": "tenant_perf",
            "roles": ["ADMIN"],
            "permissions": [
                "READ_DATA",
                "WRITE_DATA",
                "RUN_ANALYSIS",
                "APPROVE_ACTION",
                "EXECUTE_ACTION",
                "VIEW_ACTION",
                "VIEW_ACTION_AUDIT",
            ],
        })

    def setUp(self) -> None:
        """Resets in-memory stores between benchmark runs."""
        ActionExecutor._ACTIONS_STORE.clear()
        ActionExecutor._AUDIT_STORE.clear()
        RunManager._RUNS_STORE.clear()

    def test_01_api_health_latency_benchmarks(self) -> None:
        """Measures empirical latency distributions for /live and /ready health endpoints."""
        live_latencies: List[float] = []
        ready_latencies: List[float] = []

        # Warm-up run
        self.client.get("/api/v1/health/live")
        self.client.get("/api/v1/health/ready")

        iterations = 50

        # Benchmark /api/v1/health/live
        for _ in range(iterations):
            start = time.perf_counter()
            res = self.client.get("/api/v1/health/live")
            duration_ms = (time.perf_counter() - start) * 1000.0
            self.assertEqual(res.status_code, 200)
            live_latencies.append(duration_ms)

        # Benchmark /api/v1/health/ready (includes DB query)
        for _ in range(iterations):
            start = time.perf_counter()
            res = self.client.get("/api/v1/health/ready")
            duration_ms = (time.perf_counter() - start) * 1000.0
            self.assertEqual(res.status_code, 200)
            ready_latencies.append(duration_ms)

        live_pct = compute_percentiles(live_latencies)
        ready_pct = compute_percentiles(ready_latencies)

        # Verify operational latency bounds
        self.assertLess(live_pct["p95"], 50.0)
        self.assertLess(ready_pct["p95"], 100.0)

    def test_02_action_preflight_latency_distribution(self) -> None:
        """Measures in-process latency for operational action creation and policy preflight evaluation."""
        preflight_latencies: List[float] = []
        db = SessionLocal()

        try:
            for i in range(50):
                action = ActionExecutor.create_action(
                    tenant_id="tenant_perf",
                    action_type=ActionType.TRANSFER_STOCK,
                    action_category=ActionCategory.EXECUTABLE,
                    entity_type="inventory_levels",
                    entity_id=f"SKU-PERF-{i}",
                    requested_by="perf_admin",
                    payload={"quantity": 10 + i, "unit_price": 15.0},
                )

                start = time.perf_counter()
                allowed, _, _ = ActionExecutor.preflight_action(
                    db,
                    tenant_id="tenant_perf",
                    action_id=action.action_id,
                    actor_id="perf_admin",
                    actor_roles=["ADMIN"],
                )
                duration_ms = (time.perf_counter() - start) * 1000.0

                self.assertTrue(allowed)
                preflight_latencies.append(duration_ms)

            pct = compute_percentiles(preflight_latencies)
            self.assertLess(pct["p95"], 25.0)
        finally:
            db.close()

    def test_03_event_processing_latency_distribution(self) -> None:
        """Measures latency percentiles for real-time event idempotency and pipeline routing."""
        event_latencies: List[float] = []
        db = SessionLocal()

        try:
            for i in range(50):
                event_id = f"EVT-PERF-{i}-{time.time_ns()}"
                event_ts = datetime.now(timezone.utc).isoformat()
                p_hash = uuid.uuid5(uuid.NAMESPACE_DNS, f"{event_id}:{event_ts}").hex

                event = InternalEvent(
                    event_id=event_id,
                    tenant_id="tenant_perf",
                    source_system="PERF_TEST_HARNESS",
                    event_type=EventTaxonomy.INVENTORY_UPDATED,
                    entity_type="inventory_levels",
                    entity_id=f"SKU-EVENT-{i}",
                    changed_fields=["quantity"],
                    event_timestamp=event_ts,
                    payload_hash=p_hash,
                    payload={"old_qty": 100, "new_qty": 80},
                )

                start = time.perf_counter()
                res = EventProcessor.process_event(db, event)
                duration_ms = (time.perf_counter() - start) * 1000.0

                self.assertIsNotNone(res)
                event_latencies.append(duration_ms)

            pct = compute_percentiles(event_latencies)
            self.assertLess(pct["p95"], 30.0)
        finally:
            db.close()

    def test_04_concurrent_thread_safety_and_contention(self) -> None:
        """Simulates 20 concurrent threads executing runs, actions, and metrics increments simultaneously."""
        thread_count = 20
        threads: List[threading.Thread] = []
        errors: List[Exception] = []

        def worker_task(thread_idx: int) -> None:
            try:
                tenant = f"tenant_worker_{thread_idx % 4}"
                # 1. Run creation
                run = RunManager.create_run(tenant_id=tenant, capability_name="DEMAND_FORECAST")
                RunManager.start_run(tenant_id=tenant, run_id=run.run_id)
                RunManager.complete_run(tenant_id=tenant, run_id=run.run_id, result_summary={"status": "OK"})

                # 2. Action creation
                action = ActionExecutor.create_action(
                    tenant_id=tenant,
                    action_type=ActionType.TRANSFER_STOCK,
                    action_category=ActionCategory.EXECUTABLE,
                    entity_type="inventory_levels",
                    entity_id=f"SKU-CONCURRENT-{thread_idx}",
                    requested_by="concurrent_worker",
                    payload={"quantity": 25},
                )
                self.assertEqual(action.execution_state, ActionState.CREATED)

                # 3. Metrics recording
                MetricsRegistry.increment_api_request(is_error=False, latency_seconds=0.01)
                MetricsRegistry.record_run_execution(success=True)
            except Exception as e:
                errors.append(e)

        for i in range(thread_count):
            t = threading.Thread(target=worker_task, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent execution errors encountered: {errors}")

        snapshot = MetricsRegistry.get_snapshot()
        self.assertGreaterEqual(snapshot.api_requests_total, thread_count)
        self.assertGreaterEqual(snapshot.run_executions_total, thread_count)


if __name__ == "__main__":
    unittest.main()