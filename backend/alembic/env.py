"""Alembic environment configuration for async SQLAlchemy."""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import context
from app.infrastructure.config import get_settings, reveal_database_url
from app.infrastructure.database import Base

config = context.config
settings = get_settings()
database_url = reveal_database_url(settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

config.set_main_option(
    "sqlalchemy.url",
    str(database_url).replace("%", "%%"),
)


class AlembicMigrationError(RuntimeError):
    """A non-secret diagnostic for migration connection or execution failure."""


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable: AsyncEngine | None = None
    try:
        connectable = create_async_engine(database_url, poolclass=pool.NullPool)
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    except Exception:  # noqa: BLE001 - this boundary must redact every failure.
        raise AlembicMigrationError(
            "Alembic migration failed while connecting to or updating the target database"
        ) from None
    finally:
        if connectable is not None:
            try:
                await connectable.dispose()
            except Exception:  # noqa: BLE001 - disposal may retain connection details.
                raise AlembicMigrationError(
                    "Alembic migration failed while releasing the target database connection"
                ) from None


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
