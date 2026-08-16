"""Database engine and session management for AURIX Enterprise Platform.

The engine is configured centrally from application settings. Session creation
and cleanup are deliberately explicit so failed request-scoped transactions
cannot leak uncommitted state into later work.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Connection
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from aurix_core.config.settings import settings
from aurix_core.database.tenant_context import get_current_tenant_id


_DATABASE_URL = settings.database_url
_is_sqlite = _DATABASE_URL.startswith("sqlite://")
_is_sqlite_memory = (
    _is_sqlite
    and (
        ":memory:" in _DATABASE_URL
        or _DATABASE_URL.rstrip("/").endswith("sqlite://")
    )
)

# SQLite requires this for sessions that may be used across the application
# thread boundary (e.g. FastAPI/TestClient scenarios).
connect_args: dict[str, Any] = (
    {"check_same_thread": False}
    if _is_sqlite
    else {
        "connect_timeout": settings.database_connect_timeout_seconds,
    }
)

# Some PostgreSQL connection-pooling modes, including transaction-pooling
# configurations, require prepared statements to be disabled. This behavior is
# explicitly configuration-driven rather than inferred from a pooler port.
if not _is_sqlite and settings.database_disable_prepared_statements:
    connect_args["prepare_threshold"] = None

engine_kwargs: dict[str, Any] = {
    "pool_pre_ping": True,
    "pool_reset_on_return": "rollback",
    "pool_size": settings.database_pool_size,
    "max_overflow": settings.database_max_overflow,
    "pool_timeout": settings.database_pool_timeout_seconds,
    "pool_recycle": settings.database_pool_recycle_seconds,
}

if not _is_sqlite:
    # PostgreSQL-level statement_timeout applies to every statement on the
    # connection and prevents runaway analytical queries from pinning a pool.
    connect_args["options"] = (
        f"-c statement_timeout={settings.database_statement_timeout_ms}"
    )

if _is_sqlite_memory:
    # A single shared connection is required for an in-memory SQLite database
    # so metadata and data remain visible across multiple Session instances.
    engine_kwargs["poolclass"] = StaticPool

engine = create_engine(
    _DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs,
)


class TenantAwareSession(Session):
    """SQLAlchemy session that carries request/background tenant identity."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        tenant_id = get_current_tenant_id()
        if tenant_id:
            self.info["tenant_id"] = tenant_id


SessionLocal = sessionmaker(
    bind=engine,
    class_=TenantAwareSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@event.listens_for(TenantAwareSession, "after_begin")
def _bind_postgres_rls_tenant(
    session: TenantAwareSession,
    transaction: Any,
    connection: Connection,
) -> None:
    """Bind the tenant to the current PostgreSQL transaction for RLS."""
    _ = transaction

    if connection.dialect.name != "postgresql":
        return

    tenant_id = session.info.get("tenant_id") or get_current_tenant_id()

    if not tenant_id:
        return

    connection.execute(
        text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
        {"tenant_id": tenant_id},
    )


class Base(DeclarativeBase):
    """Declarative base class for all AURIX SQLAlchemy ORM models."""

    pass


def get_db() -> Generator[Session, None, None]:
    """
    Provide a request-scoped SQLAlchemy session.

    The dependency rolls back an unhandled transaction before closing the
    session. This prevents a failed request from leaving a dirty transactional
    state behind when the session is reused by surrounding infrastructure.
    """
    db = SessionLocal()

    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()