"""Declarative base definitions and multi-tenancy mixins for AURIX database models."""

from sqlalchemy import Column, String


class TenantMixin:
    """Mixin enforcing explicit server-side multi-tenant data isolation."""

    tenant_id = Column(
        String(64),
        nullable=False,
        index=True,
        comment=(
            "Logical tenant identifier required for strict "
            "data boundary isolation."
        ),
    )