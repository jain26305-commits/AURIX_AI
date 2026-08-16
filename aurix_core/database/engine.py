"""Database engine and session management for AURIX Enterprise Platform.

The engine is configured centrally from application settings. Session creation
and cleanup are deliberately explicit so failed request-scoped transactions
cannot leak uncommitted state into later work.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from aurix_core.config.settings import settings


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
connect_args = {"check_same_thread": False} if _is_sqlite else {}

engine_kwargs = {
    "pool_pre_ping": True,
    # Always return pooled connections with their transactional state reset.
    "pool_reset_on_return": "rollback",
}

if _is_sqlite_memory:
    # A single shared connection is required for an in-memory SQLite database
    # so metadata and data remain visible across multiple Session instances.
    engine_kwargs["poolclass"] = StaticPool

engine = create_engine(
    _DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
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