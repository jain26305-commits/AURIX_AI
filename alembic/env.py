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
    phase16,
    quota,
    supply_chain,
    supply_intelligence,
)

logger = logging.getLogger("alembic.env")

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# 1. Resolve database URL priority
configured_url = (
    os.getenv("ALEMBIC_DATABASE_URL")
    or config.get_main_option("sqlalchemy.url")
)

if not configured_url or configured_url.startswith("driver://"):
    configured_url = str(settings.alembic_database_url or settings.database_url)

# 2. Sanitize async drivers for Alembic's sync engine
if configured_url.startswith("postgresql+asyncpg://"):
    configured_url = configured_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
elif configured_url.startswith("sqlite+aiosqlite://"):
    configured_url = configured_url.replace("sqlite+aiosqlite://", "sqlite://")

config.set_main_option("sqlalchemy.url", configured_url)


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
        render_as_batch=True,  # Enables ALTER/DROP compatibility on SQLite
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run Alembic migrations using a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,  # Enables ALTER/DROP compatibility on SQLite
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()