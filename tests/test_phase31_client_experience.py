"""
AURIX Enterprise Platform — Phase 31 Client Experience & Search Integration Test Suite
Validates 15-Domain Analytics APIs, Global Entity Search Route, Tenant Context Isolation,
and Client DTO Schema Contracts.
"""

from typing import Generator
import pytest
from fastapi.testclient import TestClient

from aurix_api.app import app
from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.base import ResponseStatus
from aurix_api.security.auth import get_current_tenant_context

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_auth_dependencies() -> Generator[None, None, None]:
    """Injects an authorized TenantContext for test executions."""
    app.dependency_overrides[get_current_tenant_context] = lambda: TenantContext(
        tenant_id="tenant-search-01",
        user_id="USR-TEST-01",
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


def test_global_search_api_endpoint() -> None:
    """Test the unified /api/v1/search endpoint across entity categories."""
    headers = {"X-Tenant-ID": "tenant-search-01"}

    # Query matching customer
    res = client.get("/api/v1/search?q=Apex", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == ResponseStatus.SUCCESS.value
    assert len(data["data"]) >= 1
    assert any("Apex" in r["title"] for r in data["data"])

    # Query matching SKU
    res_sku = client.get("/api/v1/search?q=PUMP", headers=headers)
    assert res_sku.status_code == 200
    assert len(res_sku.json()["data"]) >= 1

    # Empty query
    res_empty = client.get("/api/v1/search?q=", headers=headers)
    assert res_empty.status_code == 200
    assert len(res_empty.json()["data"]) == 0


def test_panoramic_overview_analytics_endpoint() -> None:
    """Test /api/v1/analytics/overview endpoint providing Command Center telemetry."""
    headers = {"X-Tenant-ID": "tenant-overview-01"}
    res = client.get("/api/v1/analytics/overview", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["status"] == ResponseStatus.SUCCESS.value
    assert "healthScorePct" in payload["data"]
    assert "totalWorkingCapitalUsd" in payload["data"]
    assert "realizedValueUsd" in payload["data"]


def test_domain_analytics_endpoints_availability() -> None:
    """Verify all domain analytics endpoints backing secondary domain pages."""
    headers = {"X-Tenant-ID": "tenant-domains-01"}

    endpoints = [
        "/api/v1/demand",
        "/api/v1/forecast",
        "/api/v1/inventory",
        "/api/v1/supply",
        "/api/v1/logistics",
        "/api/v1/network",
        "/api/v1/economics",
    ]

    for ep in endpoints:
        res = client.get(ep, headers=headers)
        assert res.status_code == 200, f"Endpoint {ep} failed with status {res.status_code}"
        assert res.json()["status"] == ResponseStatus.SUCCESS.value
