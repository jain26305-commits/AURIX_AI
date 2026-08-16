"""System health, readiness, and liveness probe API router with runtime build metadata."""

import time
from typing import Any, Dict, Generator
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from aurix_api.schemas.base import ApiResponse, ResponseMetadata, ResponseStatus
from aurix_core.config.settings import settings
from aurix_core.database.engine import SessionLocal

router = APIRouter(prefix="/api/v1/health", tags=["System Health"])


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
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

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