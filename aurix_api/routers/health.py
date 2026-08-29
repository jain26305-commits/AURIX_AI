"""System health, readiness, and liveness probe API router with runtime build metadata."""

import time
from typing import Any, Dict, Generator, List
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_core.config.settings import settings
from aurix_core.database.engine import SessionLocal, engine
from aurix_core.observability.metrics import MetricsRegistry
from aurix_core.worker import celery_app

router = APIRouter(prefix="/api/v1/health", tags=["System Health"])
admin_health_router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin System Health"],
)


def get_db() -> Generator[Session, None, None]:
    """Database session dependency yielding a managed session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/live", response_model=ApiResponse[Dict[str, Any]], summary="Liveness Probe")
def liveness_probe() -> ApiResponse[Dict[str, Any]]:
    """Lightweight liveness probe confirming API process responsiveness."""
    data: Dict[str, Any] = {
        "status": "UP",
        "app_name": settings.app_name,
        "environment": settings.environment,
        "build_version": settings.build_version,
        "release_commit": settings.release_commit,
    }
    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=data,
        meta=ResponseMetadata(tenant_id=settings.default_tenant_id),
    )


@router.get("", response_model=ApiResponse[Dict[str, Any]], summary="Liveness & Readiness Probe")
@router.get("/", response_model=ApiResponse[Dict[str, Any]], include_in_schema=False)
@router.get("/ready", response_model=ApiResponse[Dict[str, Any]], summary="Readiness Probe")
def readiness_probe(db: Session = Depends(get_db)) -> ApiResponse[Dict[str, Any]]:
    """Readiness probe checking database connectivity and runtime subsystem availability."""
    start_time = time.time()
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    latency_ms = round((time.time() - start_time) * 1000, 2)
    overall_status = ResponseStatus.SUCCESS if "unhealthy" not in db_status else ResponseStatus.FAILED

    data: Dict[str, Any] = {
        "status": "UP" if overall_status == ResponseStatus.SUCCESS else "DOWN",
        "app_name": settings.app_name,
        "environment": settings.environment,
        "build_version": settings.build_version,
        "schema_version": settings.schema_version,
        "release_commit": settings.release_commit,
        "subsystems": {
            "database": db_status,
        },
        "latency_ms": latency_ms,
    }

    return ApiResponse(
        status=overall_status,
        data=data,
        meta=ResponseMetadata(tenant_id=settings.default_tenant_id),
    )

@admin_health_router.get(
    "/system-health",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Admin System Health Telemetry",
)
def admin_system_health(
    db: Session = Depends(get_db),
) -> ApiResponse[Dict[str, Any]]:
    """
    Return live runtime telemetry using the existing AURIX observability
    registry, SQLAlchemy pool, PostgreSQL session state, Redis/Celery runtime,
    and API process health.
    """
    evaluated_at = time.time()

    # API latency from the process-local authoritative metrics registry.
    metrics = MetricsRegistry.get_snapshot()

    mean_latency_ms = 0.0
    if metrics.api_requests_total > 0:
        mean_latency_ms = round(
            (
                metrics.api_latency_seconds_sum
                / float(metrics.api_requests_total)
            )
            * 1000.0,
            2,
        )

    # Database health and active connection telemetry.
    database_status = "HEALTHY"
    active_database_connections = 0

    try:
        db.execute(text("SELECT 1"))

        result = db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM pg_stat_activity
                WHERE datname = current_database()
                """
            )
        )
        active_database_connections = int(result.scalar() or 0)

    except Exception:
        database_status = "CRITICAL"

    # Celery worker availability.
    worker_status = "DEGRADED"
    celery_queue_depth = 0

    try:
        inspect = celery_app.control.inspect(timeout=1.0)
        ping_result = inspect.ping()

        if ping_result:
            worker_status = "HEALTHY"

        broker_connection = celery_app.connection_for_read()
        try:
            broker_connection.ensure_connection(max_retries=1)
            channel = broker_connection.channel()
            try:
                queue = channel.default_queue
                celery_queue_depth = int(
                    queue.queue_declare(
                        queue=queue,
                        passive=True,
                    ).method.message_count
                )
            finally:
                try:
                    channel.close()
                except Exception:
                    pass
        finally:
            try:
                broker_connection.release()
            except Exception:
                pass

    except Exception:
        worker_status = "DEGRADED"

    services: List[Dict[str, Any]] = [
        {
            "serviceKey": "api",
            "serviceName": "AURIX API",
            "status": "HEALTHY",
            "latencyMs": mean_latency_ms,
            "uptimePercent": 100.0,
            "activeWorkersOrConnections": int(metrics.api_requests_total),
            "resourceUtilizationPercent": 0.0,
            "lastCheckedAt": datetime_now_iso(),
        },
        {
            "serviceKey": "postgres",
            "serviceName": "PostgreSQL",
            "status": database_status,
            "latencyMs": 0.0,
            "uptimePercent": 100.0 if database_status == "HEALTHY" else 0.0,
            "activeWorkersOrConnections": active_database_connections,
            "resourceUtilizationPercent": 0.0,
            "lastCheckedAt": datetime_now_iso(),
        },
        {
            "serviceKey": "celery",
            "serviceName": "Celery Worker",
            "status": worker_status,
            "latencyMs": 0.0,
            "uptimePercent": 100.0 if worker_status == "HEALTHY" else 0.0,
            "activeWorkersOrConnections": int(
                metrics.run_executions_total
            ),
            "resourceUtilizationPercent": 0.0,
            "lastCheckedAt": datetime_now_iso(),
        },
    ]

    overall_health = "HEALTHY"

    if database_status == "CRITICAL":
        overall_health = "CRITICAL"
    elif worker_status != "HEALTHY":
        overall_health = "DEGRADED"

    data: Dict[str, Any] = {
        "evaluatedAt": datetime_now_iso(),
        "overallHealth": overall_health,
        "meanApiLatencyMs": mean_latency_ms,
        "activeDatabaseConnections": active_database_connections,
        "celeryQueueDepth": celery_queue_depth,
        "services": services,
    }

    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        data=data,
        meta=ResponseMetadata(
            tenant_id=settings.default_tenant_id
        ),
    )


def datetime_now_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 form."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
