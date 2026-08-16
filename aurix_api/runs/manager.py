"""Master Analytical Run Execution Manager with Worker Crash Reconciliation and Stuck-Job Recovery."""

import logging
import threading
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("aurix_api.runs.manager")


class RunStatus(str, Enum):
    """Execution status lifecycle states for analytical runs."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    INTERRUPTED = "INTERRUPTED"


class RunRecord(BaseModel):
    """Container tracking analytical run execution metadata, progress, and results."""
    run_id: str
    tenant_id: str
    capability_name: str
    status: RunStatus = RunStatus.PENDING
    parameters: Dict[str, Any] = Field(default_factory=dict)
    result_summary: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    heartbeat_at: Optional[str] = None


class RunManager:
    """Coordinates thread-safe execution tracking, worker crash recovery, and execution state persistence."""

    _lock = threading.Lock()
    _RUNS_STORE: Dict[str, Dict[str, RunRecord]] = {}

    # Default threshold after which a job without heartbeat is considered dead/stuck
    DEFAULT_STUCK_JOB_TIMEOUT_SECONDS: int = 300  # 5 minutes

    @classmethod
    def create_run(
        cls,
        tenant_id: str,
        capability_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> RunRecord:
        """Initializes and registers a new analytical execution run in PENDING state."""
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        record = RunRecord(
            run_id=run_id,
            tenant_id=tenant_id,
            capability_name=capability_name,
            status=RunStatus.PENDING,
            parameters=parameters or {},
            heartbeat_at=datetime.now(timezone.utc).isoformat(),
        )

        with cls._lock:
            tenant_runs = cls._RUNS_STORE.setdefault(tenant_id, {})
            tenant_runs[run_id] = record

        logger.info("Initialized analytical run [%s] for tenant [%s] (Capability: %s)", run_id, tenant_id, capability_name)
        return record

    @classmethod
    def start_run(cls, tenant_id: str, run_id: str) -> RunRecord:
        """Transitions run state to RUNNING and initializes heartbeat timestamp."""
        with cls._lock:
            record = cls._get_run_unlocked(tenant_id, run_id)
            record.status = RunStatus.RUNNING
            record.started_at = datetime.now(timezone.utc).isoformat()
            record.heartbeat_at = record.started_at

        logger.info("Started analytical run execution [%s] for tenant [%s]", run_id, tenant_id)
        return record

    @classmethod
    def record_heartbeat(cls, tenant_id: str, run_id: str) -> None:
        """Updates active execution heartbeat to prevent stuck-job timeout classification."""
        with cls._lock:
            record = cls._get_run_unlocked(tenant_id, run_id)
            if record.status == RunStatus.RUNNING:
                record.heartbeat_at = datetime.now(timezone.utc).isoformat()

    @classmethod
    def complete_run(
        cls,
        tenant_id: str,
        run_id: str,
        result_summary: Optional[Dict[str, Any]] = None,
    ) -> RunRecord:
        """Marks run as COMPLETED with output payload."""
        with cls._lock:
            record = cls._get_run_unlocked(tenant_id, run_id)
            record.status = RunStatus.COMPLETED
            record.completed_at = datetime.now(timezone.utc).isoformat()
            record.result_summary = result_summary or {}

        logger.info("Completed analytical run [%s] for tenant [%s] successfully", run_id, tenant_id)
        return record

    @classmethod
    def fail_run(
        cls,
        tenant_id: str,
        run_id: str,
        error_message: str,
    ) -> RunRecord:
        """Marks run as FAILED with captured error diagnostics."""
        with cls._lock:
            record = cls._get_run_unlocked(tenant_id, run_id)
            record.status = RunStatus.FAILED
            record.completed_at = datetime.now(timezone.utc).isoformat()
            record.error_message = error_message

        logger.error("Failed analytical run [%s] for tenant [%s]: %s", run_id, tenant_id, error_message)
        return record

    @classmethod
    def get_run(cls, tenant_id: str, run_id: str) -> RunRecord:
        """Retrieves a specific run by ID within tenant isolation boundary."""
        with cls._lock:
            return cls._get_run_unlocked(tenant_id, run_id)

    @classmethod
    def list_runs(cls, tenant_id: str, limit: int = 50) -> List[RunRecord]:
        """Lists runs for a specific tenant sorted descending by creation time."""
        with cls._lock:
            tenant_runs = list(cls._RUNS_STORE.get(tenant_id, {}).values())
            tenant_runs.sort(key=lambda x: x.created_at, reverse=True)
            return tenant_runs[:limit]

    @classmethod
    def reconcile_crashed_runs(
        cls,
        stuck_timeout_seconds: Optional[int] = None,
    ) -> Dict[str, int]:
        """
        Scans all tenant stores on startup or scheduled maintenance sweeps.
        Transitions abandoned PENDING or RUNNING jobs without recent heartbeats to INTERRUPTED/FAILED.
        """
        timeout_sec = stuck_timeout_seconds or cls.DEFAULT_STUCK_JOB_TIMEOUT_SECONDS
        cutoff_dt = datetime.now(timezone.utc) - timedelta(seconds=timeout_sec)
        reconciled_count = 0

        with cls._lock:
            for tenant_id, runs in cls._RUNS_STORE.items():
                for run_id, record in runs.items():
                    if record.status in (RunStatus.PENDING, RunStatus.RUNNING):
                        # Determine timestamp anchor (heartbeat, started_at, or created_at)
                        ts_str = record.heartbeat_at or record.started_at or record.created_at
                        try:
                            record_dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            if record_dt < cutoff_dt:
                                record.status = RunStatus.INTERRUPTED
                                record.completed_at = datetime.now(timezone.utc).isoformat()
                                record.error_message = (
                                    f"Execution interrupted: Worker process terminated ungracefully or "
                                    f"exceeded stuck-job timeout ({timeout_sec}s)."
                                )
                                reconciled_count += 1
                                logger.warning(
                                    "Reconciled abandoned run [%s] for tenant [%s] -> Status: INTERRUPTED",
                                    run_id,
                                    tenant_id,
                                )
                        except Exception as e:
                            logger.error("Failed parsing timestamp for run [%s]: %s", run_id, str(e))

        logger.info("Worker crash reconciliation completed: %d abandoned runs reconciled", reconciled_count)
        return {"reconciled_runs": reconciled_count}

    @classmethod
    def _get_run_unlocked(cls, tenant_id: str, run_id: str) -> RunRecord:
        """Internal helper resolving run record within lock."""
        tenant_runs = cls._RUNS_STORE.get(tenant_id, {})
        record = tenant_runs.get(run_id)
        if not record:
            raise KeyError(f"Analytical run '{run_id}' not found for tenant '{tenant_id}'.")
        return record