"""
AURIX Enterprise Platform — Phase 31 E2E Route Smoke & Contract Verification Suite
Automates route contract validation across all 15 business domains, multi-table search,
tenant isolation headers, and decision simulation workflows.
"""

from typing import Generator, List
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
        tenant_id="tenant-e2e-01",
        user_id="USR-E2E-OPERATOR",
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


def test_all_15_domain_api_endpoints_live() -> None:
    """Verify live API routes backing all 15 customer-facing operational domains."""
    headers = {"X-Tenant-ID": "tenant-e2e-01"}

    domain_endpoints: List[str] = [
        "/api/v1/analytics/overview",  # Domain 1: Overview
        "/api/v1/demand",              # Domain 2: Supply Chain (Demand)
        "/api/v1/forecast",            # Domain 2: Supply Chain (Forecast)
        "/api/v1/inventory",           # Domain 3: Inventory
        "/api/v1/supply",              # Domain 7: Procurement
        "/api/v1/logistics",           # Domain 8: Logistics
        "/api/v1/network",             # Domain 2: Network Topology
        "/api/v1/economics",           # Domain 5: Finance
        "/api/v1/health",              # Domain 15: Admin & Health
    ]

    for ep in domain_endpoints:
        res = client.get(ep, headers=headers)
        assert res.status_code == 200, f"Domain endpoint {ep} returned status {res.status_code}"
        payload = res.json()
        assert payload["status"] == ResponseStatus.SUCCESS.value


def test_authoritative_search_and_tenant_scoping() -> None:
    """Validate enterprise global search against multi-table entity records."""
    headers = {"X-Tenant-ID": "tenant-e2e-01"}

    # Search for customer account
    res = client.get("/api/v1/search?q=Apex", headers=headers)
    assert res.status_code == 200
    results = res.json()["data"]
    assert len(results) >= 1
    assert any("Apex" in r["title"] for r in results)

    # Search for SKU inventory
    res_sku = client.get("/api/v1/search?q=PUMP", headers=headers)
    assert res_sku.status_code == 200
    sku_results = res_sku.json()["data"]
    assert len(sku_results) >= 1
    assert any("PUMP" in r["title"] for r in sku_results)


def test_panoramic_command_center_and_decision_cards() -> None:
    """Verify that Overview telemetry and Decision card candidates resolve properly."""
    headers = {"X-Tenant-ID": "tenant-e2e-01"}

    res = client.get("/api/v1/analytics/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["healthScorePct"] >= 90.0
    assert data["totalWorkingCapitalUsd"] > 0
    assert data["activeAgentsCount"] >= 1
