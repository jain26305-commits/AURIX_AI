"""
AURIX Enterprise Platform — Frontend Contracts & Authoritative Multi-Table Search Test Suite
Validates dynamic search queries across live PostgreSQL entity models, tenant scoping,
and DTO contract integrity matching the 15-domain client experience.
"""

from typing import Generator
import pytest
from fastapi.testclient import TestClient

from aurix_api.app import app
from aurix_api.schemas.auth import Permission, TenantContext
from aurix_api.schemas.base import ResponseStatus
from aurix_api.security.auth import get_current_tenant_context
from aurix_core.database.engine import SessionLocal
from aurix_core.database.models.supply_chain import Customer, Product, Supplier

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_auth_dependencies() -> Generator[None, None, None]:
    """Injects an authorized TenantContext for test executions."""
    app.dependency_overrides[get_current_tenant_context] = lambda: TenantContext(
        tenant_id="tenant-contract-01",
        user_id="USR-CONTRACT-01",
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


@pytest.fixture(scope="module")
def seeded_db_entities() -> Generator[None, None, None]:
    """Seeds test records in PostgreSQL to verify live database search resolution."""
    db = SessionLocal()
    tenant_a = "tenant-contract-01"
    tenant_b = "tenant-isolated-02"

    try:
        # Seed Tenant A records
        c1 = Customer(id="CUST-T1", tenant_id=tenant_a, name="Apex Industrial Solutions", customer_number="C-100")
        p1 = Product(id="PROD-T1", tenant_id=tenant_a, sku="SKU-PUMP-PRO", name="Heavy Industrial Pump")
        s1 = Supplier(id="SUPP-T1", tenant_id=tenant_a, name="Precision Hydraulics Co", supplier_code="S-200")
        db.add_all([c1, p1, s1])

        # Seed Tenant B records (for isolation testing)
        c2 = Customer(id="CUST-T2", tenant_id=tenant_b, name="Isolated Apex Subsidiary", customer_number="C-999")
        db.add(c2)

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    yield


def test_authoritative_database_search_multi_table(seeded_db_entities: None) -> None:
    """Test searching across customers, products, and suppliers in the database."""
    headers = {"X-Tenant-ID": "tenant-contract-01"}

    # Search for customer
    res = client.get("/api/v1/search?q=Apex", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) >= 1
    assert any("Apex" in item["title"] for item in data)

    # Search for SKU
    res_sku = client.get("/api/v1/search?q=PUMP", headers=headers)
    assert res_sku.status_code == 200
    sku_data = res_sku.json()["data"]
    assert len(sku_data) >= 1
    assert any("PUMP" in item["title"] for item in sku_data)


def test_authoritative_search_tenant_isolation(seeded_db_entities: None) -> None:
    """Ensure search queries never leak records from another tenant."""
    headers = {"X-Tenant-ID": "tenant-contract-01"}

    # Tenant B has 'Isolated Apex Subsidiary' — Tenant A query must not return it
    res = client.get("/api/v1/search?q=Isolated", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) == 0


def test_domain_analytics_dto_contracts() -> None:
    """Validate that domain analytics payloads adhere strictly to expected schemas."""
    headers = {"X-Tenant-ID": "tenant-contract-01"}

    res = client.get("/api/v1/economics", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["status"] == ResponseStatus.SUCCESS.value
    assert "portfolio_working_capital" in payload["data"]
    assert "portfolio_annual_holding_cost" in payload["data"]
