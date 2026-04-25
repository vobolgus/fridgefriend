# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false

"""Alembic environment.

Resolves the database URL from :mod:`app.core.config` so migrations always run
against the same database as the application. Supports async SQLAlchemy drivers
(``postgresql+asyncpg``, ``sqlite+aiosqlite``) by routing through
``async_engine_from_config`` + ``connection.run_sync``.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import the Base + all models so ``target_metadata`` is fully populated.
# Importing ``app.models`` triggers the side-effect imports for every model.
from app.core.config import settings
from app.models import Base

config = context.config

# Inject the runtime DATABASE_URL into the Alembic config so subsequent
# ``config.get_section(...)`` / ``async_engine_from_config`` calls see it.
# We never read ``sqlalchemy.url`` from alembic.ini in normal operation.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _is_async_url(url: str) -> bool:
    return "+asyncpg" in url or "+aiosqlite" in url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a DB connection)."""
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


def _do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def _run_async_migrations() -> None:
    section = config.get_section(config.config_ini_section, {}) or {}
    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode against a live database."""
    url = config.get_main_option("sqlalchemy.url") or ""
    if _is_async_url(url):
        asyncio.run(_run_async_migrations())
        return

    # Sync fallback (psycopg2 / pysqlite). Currently unused by the app, but kept
    # so operators can run alembic against a sync URL if desired.
    from sqlalchemy import engine_from_config

    section = config.get_section(config.config_ini_section, {}) or {}
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        _do_run_migrations(connection)
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
