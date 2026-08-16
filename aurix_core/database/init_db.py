"""Database initialization and legacy bootstrap compatibility for AURIX.

Alembic is the canonical schema-management mechanism. This module only:
1. registers ORM models before metadata inspection;
2. verifies database schema state;
3. optionally supports explicit non-production legacy/autocreate bootstrap.

Production startup must never silently create or mutate the schema.
"""

from __future__ import annotations

import logging
import os
from typing import Tuple

from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from aurix_core.database.engine import Base, engine
from aurix_core.database.models import (
    economics,
    events,
    forecasting,
    ingestion,
    intelligence,
    inventory_intelligence,
    logistics_intelligence,
    network_intelligence,
    quota,
    supply_chain,
    supply_intelligence,
)

logger = logging.getLogger(__name__)


def _register_models() -> None:
    """Ensure the canonical ORM registry is imported before metadata inspection."""
    # Explicit references keep model modules imported and registered in
    # Base.metadata before schema inspection.
    _ = (
        supply_chain,
        ingestion,
        forecasting,
        inventory_intelligence,
        supply_intelligence,
        logistics_intelligence,
        network_intelligence,
        economics,
        intelligence,
        quota,
        events,
    )


def _schema_state() -> Tuple[bool, bool]:
    """Return whether application tables and the Alembic marker exist."""
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    has_alembic_version = "alembic_version" in table_names

    application_tables = {
        table.name
        for table in Base.metadata.sorted_tables
    }

    has_application_tables = bool(
        table_names.intersection(application_tables)
    )

    return has_application_tables, has_alembic_version


def create_development_schema() -> None:
    """Explicitly create ORM metadata for development/test use only."""
    _register_models()

    environment = os.getenv(
        "AURIX_ENVIRONMENT",
        "development",
    ).strip().lower()

    if environment == "production":
        raise RuntimeError(
            "ORM metadata schema creation is disabled in production. "
            "Use `alembic upgrade head`."
        )

    logger.warning(
        "Creating AURIX schema directly from ORM metadata. "
        "This path is intended only for explicit development/test use."
    )
    Base.metadata.create_all(bind=engine)
    logger.info("Development/test ORM schema creation completed.")


def initialize_database() -> None:
    """Validate database initialization state without competing with Alembic."""
    _register_models()

    allow_autocreate = os.getenv(
        "AURIX_ALLOW_SCHEMA_AUTOCREATE",
        "false",
    ).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    environment = os.getenv(
        "AURIX_ENVIRONMENT",
        "development",
    ).strip().lower()

    try:
        logger.info("Checking AURIX database schema state...")

        has_application_tables, has_alembic_version = _schema_state()

        # Alembic is authoritative. Never call create_all() on an Alembic DB.
        if has_alembic_version:
            logger.info(
                "Alembic-managed database detected; "
                "schema creation delegated to Alembic."
            )
            return

        # Existing legacy schema without Alembic marker.
        if has_application_tables:
            if environment == "production":
                raise RuntimeError(
                    "Production database contains application tables but "
                    "has no alembic_version marker. Refusing implicit schema "
                    "mutation. Run the appropriate Alembic migration/stamp "
                    "procedure before application startup."
                )

            if not allow_autocreate:
                raise RuntimeError(
                    "Legacy application tables were detected without an "
                    "alembic_version marker. Automatic schema mutation is "
                    "disabled. Resolve the database with Alembic or explicitly "
                    "set AURIX_ALLOW_SCHEMA_AUTOCREATE=true for development."
                )

            logger.warning(
                "Legacy non-production database detected and explicit "
                "schema-autocreate permission is enabled."
            )
            create_development_schema()
            return

        # Completely fresh database.
        if allow_autocreate:
            create_development_schema()
            return

        raise RuntimeError(
            "AURIX database is uninitialized and automatic schema creation "
            "is disabled. Run `alembic upgrade head` before startup, or "
            "explicitly set AURIX_ALLOW_SCHEMA_AUTOCREATE=true for "
            "development/test use."
        )

    except SQLAlchemyError as exc:
        logger.exception("Database schema inspection/initialization failed.")
        raise RuntimeError(
            "AURIX database initialization failed."
        ) from exc


if __name__ == "__main__":
    initialize_database()