"""Alembic environment configuration for async SQLAlchemy."""

from __future__ import annotations

import asyncio
import re
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

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
    """A bounded Alembic failure retaining only safe diagnostic metadata."""

    def __init__(
        self,
        *,
        stage: str,
        category: str,
        exception_class: str,
        sqlstate: str | None = None,
        revision: str | None = None,
    ) -> None:
        self.stage = stage
        self.category = category
        self.exception_class = exception_class
        self.sqlstate = sqlstate
        self.revision = revision
        self.cleanup: AlembicMigrationError | None = None
        super().__init__(self._render())

    def attach_cleanup(self, cleanup: AlembicMigrationError) -> None:
        """Retain cleanup context without replacing the primary failure."""
        self.cleanup = cleanup
        self.args = (self._render(),)

    def detached(self) -> AlembicMigrationError:
        """Copy safe fields without retaining a suppressed provider exception context."""
        detached = AlembicMigrationError(
            stage=self.stage,
            category=self.category,
            exception_class=self.exception_class,
            sqlstate=self.sqlstate,
            revision=self.revision,
        )
        if self.cleanup is not None:
            detached.attach_cleanup(self.cleanup.detached())
        return detached

    def _render(self) -> str:
        details = [
            f"stage={self.stage}",
            f"category={self.category}",
            f"exception={self.exception_class}",
        ]
        if self.sqlstate is not None:
            details.append(f"sqlstate={self.sqlstate}")
        if self.revision is not None:
            details.append(f"revision={self.revision}")
        if self.cleanup is not None:
            details.append(
                "cleanup="
                f"{self.cleanup.category}/{self.cleanup.exception_class}"
            )
        return f"Alembic {self.stage} failed [{'; '.join(details)}]"


SAFE_DIAGNOSTIC_TOKEN = re.compile(r"[A-Za-z0-9_.-]{1,64}\Z")
SAFE_SQLSTATE = re.compile(r"[A-Z0-9]{5}\Z")


def _safe_token(value: object) -> str | None:
    if not isinstance(value, str) or SAFE_DIAGNOSTIC_TOKEN.fullmatch(value) is None:
        return None
    return value


def _safe_sqlstate(error: Exception) -> str | None:
    candidates = [getattr(error, "sqlstate", None)]
    original = getattr(error, "orig", None)
    if original is not None:
        candidates.append(getattr(original, "sqlstate", None))
    for candidate in candidates:
        if isinstance(candidate, str):
            normalized = candidate.upper()
            if SAFE_SQLSTATE.fullmatch(normalized) is not None:
                return normalized
    return None


def _failure_category(error: Exception) -> str:
    if isinstance(error, OSError):
        return "network"
    if _safe_sqlstate(error) is not None:
        return "database"
    module = type(error).__module__
    if module.startswith(("asyncpg", "psycopg", "sqlalchemy")):
        return "database"
    if module.startswith("alembic"):
        return "migration"
    return "runtime"


def _sanitize_failure(
    stage: str,
    error: Exception,
    *,
    revision: object = None,
) -> AlembicMigrationError:
    exception_class = _safe_token(type(error).__name__) or "Exception"
    error_revision = revision if revision is not None else getattr(error, "revision", None)
    return AlembicMigrationError(
        stage=stage,
        category=_failure_category(error),
        exception_class=exception_class,
        sqlstate=_safe_sqlstate(error),
        revision=_safe_token(error_revision),
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    revision: str | None = None
    try:
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )
        revision = context.get_context().get_current_revision()
        with context.begin_transaction():
            context.run_migrations()
    except Exception as error:  # noqa: BLE001 - raw migration failures may contain SQL.
        raise _sanitize_failure(
            "migration execution",
            error,
            revision=revision,
        ) from None


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    revision: str | None = None
    try:
        revision = context.get_context().get_current_revision()
        with context.begin_transaction():
            context.run_migrations()
    except Exception as error:  # noqa: BLE001 - raw migration failures may contain SQL.
        raise _sanitize_failure(
            "migration execution",
            error,
            revision=revision,
        ) from None


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable: AsyncEngine | None = None
    connection: AsyncConnection | None = None
    primary_failure: AlembicMigrationError | None = None
    cleanup_failure: AlembicMigrationError | None = None
    try:
        try:
            connectable = create_async_engine(database_url, poolclass=pool.NullPool)
            connection = await connectable.connect()
        except Exception as error:  # noqa: BLE001 - connection errors may retain the URL.
            primary_failure = _sanitize_failure("connection setup", error)

        if connection is not None:
            try:
                await connection.run_sync(do_run_migrations)
            except AlembicMigrationError as error:
                primary_failure = error.detached()
            except Exception as error:  # noqa: BLE001 - provider failures may contain SQL.
                primary_failure = _sanitize_failure("migration execution", error)
    finally:
        if connection is not None:
            try:
                await connection.close()
            except Exception as error:  # noqa: BLE001 - cleanup may retain connection data.
                cleanup_failure = _sanitize_failure("disposal cleanup", error)
        if connectable is not None:
            try:
                await connectable.dispose()
            except Exception as error:  # noqa: BLE001 - cleanup may retain connection data.
                if cleanup_failure is None:
                    cleanup_failure = _sanitize_failure("disposal cleanup", error)

    if primary_failure is not None:
        if cleanup_failure is not None:
            primary_failure.attach_cleanup(cleanup_failure)
        raise primary_failure from None
    if cleanup_failure is not None:
        raise cleanup_failure from None


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
