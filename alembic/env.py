"""Alembic database migration environment for AURIX Enterprise Platform."""

import logging
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from aurix_core.config.settings import settings
from aurix_core.database.engine import Base

# Import every ORM model module so SQLAlchemy registers all mapped tables
# in Base.metadata before Alembic performs autogeneration or migrations.
from aurix_core.database.models import (  # noqa: F401
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

logger = logging.getLogger("alembic.env")

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Respect an explicit ALEMBIC_DATABASE_URL first.
# Otherwise use the URL defined in alembic.ini.
# Only fall back to the application settings when neither exists.
configured_url = (
    os.getenv("ALEMBIC_DATABASE_URL")
    or config.get_main_option("sqlalchemy.url")
)

if not configured_url or configured_url.startswith("driver://"):
    configured_url = settings.database_url

config.set_main_option(
    "sqlalchemy.url",
    configured_url,
)


def run_migrations_offline() -> None:
    """Run Alembic migrations without opening a database connection."""
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run Alembic migrations using a live database connection."""
    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {},
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()