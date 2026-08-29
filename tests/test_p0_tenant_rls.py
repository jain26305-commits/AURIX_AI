"""PostgreSQL RLS proof tests for P0 tenant isolation hardening across all domains."""

from __future__ import annotations

import os
from collections.abc import Generator
import datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from aurix_core.database.engine import TenantAwareSession
from aurix_core.database.models.quota import AIUsagePolicy
from aurix_core.database.models.actions import Phase14ActionModel
from aurix_core.database.models.connectors import ConnectorModel
from aurix_core.phase16.models import Phase16CaseModel
from aurix_core.database.tenant_context import tenant_scope


@pytest.fixture(scope="module")
def postgres_engine() -> Generator[Engine, None, None]:
    url = os.getenv("AURIX_RLS_TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not url or "sqlite" in url:
        pytest.skip("PostgreSQL connection string (AURIX_RLS_TEST_DATABASE_URL / DATABASE_URL) required for RLS test suite")
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        engine.dispose()
        pytest.skip(f"PostgreSQL RLS test database unavailable: {exc}")
    yield engine
    engine.dispose()


@pytest.fixture()
def db(postgres_engine: Engine) -> Generator[Session, None, None]:
    SessionLocal = sessionmaker(
        bind=postgres_engine,
        class_=TenantAwareSession,
        autoflush=False,
        expire_on_commit=False,
    )
    with SessionLocal() as session:
        yield session
        session.rollback()


def _clear_rows(db: Session) -> None:
    for tenant_id in ("p0-tenant-a", "p0-tenant-b"):
        with tenant_scope(tenant_id):
            db.query(AIUsagePolicy).filter(AIUsagePolicy.tenant_id == tenant_id).delete(synchronize_session=False)
            db.query(Phase14ActionModel).filter(Phase14ActionModel.tenant_id == tenant_id).delete(synchronize_session=False)
            db.query(ConnectorModel).filter(ConnectorModel.tenant_id == tenant_id).delete(synchronize_session=False)
            db.query(Phase16CaseModel).filter(Phase16CaseModel.tenant_id == tenant_id).delete(synchronize_session=False)
            db.commit()


def test_tenant_a_cannot_read_tenant_b_rows(db: Session) -> None:
    _clear_rows(db)

    with tenant_scope("p0-tenant-a"):
        db.add(AIUsagePolicy(tenant_id="p0-tenant-a"))
        db.commit()

    with tenant_scope("p0-tenant-b"):
        db.add(AIUsagePolicy(tenant_id="p0-tenant-b"))
        db.commit()

    with tenant_scope("p0-tenant-a"):
        own = db.query(AIUsagePolicy).filter(AIUsagePolicy.tenant_id == "p0-tenant-a").all()
        foreign = db.query(AIUsagePolicy).filter(AIUsagePolicy.tenant_id == "p0-tenant-b").all()
        assert len(own) == 1
        assert foreign == []


def test_tenant_scope_rejects_cross_tenant_write(db: Session) -> None:
    _clear_rows(db)

    with tenant_scope("p0-tenant-a"):
        db.add(AIUsagePolicy(tenant_id="p0-tenant-b"))
        with pytest.raises(Exception):
            db.commit()
        db.rollback()


def test_missing_tenant_context_cannot_read_tenant_rows(db: Session) -> None:
    _clear_rows(db)

    with tenant_scope("p0-tenant-a"):
        db.add(AIUsagePolicy(tenant_id="p0-tenant-a"))
        db.commit()

    assert db.query(AIUsagePolicy).all() == []


def test_phase14_actions_tenant_isolation(db: Session) -> None:
    _clear_rows(db)
    now = datetime.datetime.now(datetime.timezone.utc)

    # Insert action for Tenant A
    with tenant_scope("p0-tenant-a"):
        act_a = Phase14ActionModel(
            id="ACT-RLS-TEST-A",
            tenant_id="p0-tenant-a",
            title="Tenant A Action",
            domain="INVENTORY",
            target_entity_id="SKU-A",
            target_entity_name="SKU A",
            prescriptive_payload_json={"action": "HOLD"},
            initiated_by="Test Suite",
            preflight_checks_json=[],
            audit_trail_json=[],
            created_at=now,
            updated_at=now
        )
        db.add(act_a)
        db.commit()

    # Query from Tenant B scope
    with tenant_scope("p0-tenant-b"):
        actions_b = db.query(Phase14ActionModel).filter(Phase14ActionModel.id == "ACT-RLS-TEST-A").all()
        assert actions_b == []


def test_phase16_cases_tenant_isolation(db: Session) -> None:
    _clear_rows(db)
    now = datetime.datetime.now(datetime.timezone.utc)

    # Insert case for Tenant A
    with tenant_scope("p0-tenant-a"):
        case_a = Phase16CaseModel(
            id="CASE-RLS-TEST-A",
            tenant_id="p0-tenant-a",
            case_type="SUPPLY",
            severity="HIGH",
            status="OPEN",
            title="Tenant A Supply Disruption",
            created_at=now,
            updated_at=now
        )
        db.add(case_a)
        db.commit()

    # Query from Tenant B scope
    with tenant_scope("p0-tenant-b"):
        cases_b = db.query(Phase16CaseModel).filter(Phase16CaseModel.id == "CASE-RLS-TEST-A").all()
        assert cases_b == []