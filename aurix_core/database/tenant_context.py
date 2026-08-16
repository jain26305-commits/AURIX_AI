"""Request/background tenant context and PostgreSQL RLS session binding."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator, Optional

_current_tenant_id: ContextVar[Optional[str]] = ContextVar(
    "aurix_current_tenant_id",
    default=None,
)


def get_current_tenant_id() -> Optional[str]:
    """Return the tenant ID bound to the current execution context."""
    return _current_tenant_id.get()


def set_current_tenant_id(tenant_id: str) -> Token[Optional[str]]:
    """Bind a tenant ID to the current execution context."""
    clean_tenant_id = tenant_id.strip()
    if not clean_tenant_id:
        raise ValueError("tenant_id cannot be empty")
    return _current_tenant_id.set(clean_tenant_id)


def reset_current_tenant_id(token: Token[Optional[str]]) -> None:
    """Restore the previous tenant context."""
    _current_tenant_id.reset(token)


@contextmanager
def tenant_scope(tenant_id: str) -> Iterator[None]:
    """Temporarily bind a tenant ID for a request or background job."""
    token = set_current_tenant_id(tenant_id)
    try:
        yield
    finally:
        reset_current_tenant_id(token)
