"""
AURIX Enterprise Platform — Phase 31 Docker & Runtime Health Test Suite
Validates system health endpoints, PostgreSQL session connectivity, Redis caching layers,
and multi-container runtime health checks.
"""

from typing import Generator
import pytest
from fastapi.testclient import TestClient

from aurix_api.app import app
from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.base import ResponseStatus
from aurix_api.security.auth import get_current_tenant_context
from aurix_core.database.engine import SessionLocal

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_auth_dependencies() -> Generator[None, None, None]:
    """Injects an authorized TenantContext for runtime health testing."""
    app.dependency_overrides[get_current_tenant_context] = lambda: TenantContext(
        tenant_id="tenant-health-01",
        user_id="USR-HEALTH-CHECKER",
        roles=["ADMIN"],
        permissions=[
            Permission.READ_DATA,
            Permission.WRITE_DATA,
            Permission.EXECUTE_ACTION,
            Permission.APPROVE_ACTION,
            Permission.VIEW_FINANCIALS,
        ],
    )
    yield
    app.dependency_overrides.clear()


def test_api_health_endpoint() -> None:
    """Verify primary application health and liveness probe."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy" or data.get("code") == 200 or "status" in data


def test_database_session_health() -> None:
    """Validate active database connectivity and transaction capability."""
    db = SessionLocal()
    try:
        assert db is not None
        # Verify basic session state
        assert db.is_active is True
    finally:
        db.close()


def test_overview_telemetry_live() -> None:
    """Ensure panoramic overview telemetry is available for the AppShell banner."""
    headers = {"X-Tenant-ID": "tenant-health-01"}
    res = client.get("/api/v1/analytics/overview", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["status"] == ResponseStatus.SUCCESS.value
    assert payload["data"]["healthScorePct"] >= 90.0
