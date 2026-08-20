"""AURIX Enterprise Platform ORM model registry.

Importing this package registers every SQLAlchemy ORM model against the
single canonical Base.metadata instance.

This centralized registry is intentionally side-effectful at import time:
SQLAlchemy must know about all tables and foreign-key targets before
Base.metadata.create_all(), Alembic autogeneration, or schema inspection
is executed.
"""

from aurix_core.database.models import (
    economics,
    events,
    forecasting,
    ingestion,
    intelligence,
    inventory_intelligence,
    logistics_intelligence,
    network,
    network_intelligence,
    quota,
    supply_chain,
    supply_intelligence,
)
from aurix_core.database.engine import Base
from aurix_core.phase16 import models as phase16

__all__ = [
    "Base",
    "economics",
    "events",
    "forecasting",
    "ingestion",
    "intelligence",
    "inventory_intelligence",
    "logistics_intelligence",
    "network",
    "network_intelligence",
    "quota",
    "supply_chain",
    "supply_intelligence",
    "phase16",
]