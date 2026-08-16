"""PostgreSQL RLS proof tests for P0 tenant isolation hardening."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from aurix_core.database.engine import TenantAwareSession

from aurix_core.database.models.quota import AIUsagePolicy
from aurix_core.database.tenant_context import tenant_scope


@pytest.fixture(scope="module")
def postgres_engine() -> Generator[Engine, None, None]:
    url = os.getenv("AURIX_RLS_TEST_DATABASE_URL")
    if not url:
        pytest.skip("AURIX_RLS_TEST_DATABASE_URL is not configured")
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - environment-dependent
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
    # The test role has DML rights only. Existing rows are isolated by tenant;
    # clearing via TRUNCATE would bypass the RLS contract, so delete within a scope.
    for tenant_id in ("p0-tenant-a", "p0-tenant-b"):
        with tenant_scope(tenant_id):
            db.query(AIUsagePolicy).filter(AIUsagePolicy.tenant_id == tenant_id).delete(
                synchronize_session=False
            )
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
