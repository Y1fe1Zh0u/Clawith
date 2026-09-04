from __future__ import annotations

import ast
import importlib.util
import os
import subprocess
from contextlib import nullcontext
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

import pytest
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from alembic import context as alembic_context

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINT = BACKEND_ROOT / "entrypoint.sh"
ALEMBIC_ENV = BACKEND_ROOT / "alembic" / "env.py"
TARGET_COMMAND = (
    "exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"
)
DIRECT_STARTUP = ("set -e", TARGET_COMMAND)
PRIVILEGE_DROP_STARTUP = (
    "set -e",
    "if [ \"$(id -u)\" = '0' ]; then",
    'exec gosu clawith /bin/bash "$0" "$@"',
    "fi",
    TARGET_COMMAND,
)
ALLOWED_ENTRYPOINT_STRUCTURES = {DIRECT_STARTUP, PRIVILEGE_DROP_STARTUP}


class BoundaryViolation(ValueError):
    """A target startup or migration boundary admits legacy authority."""


class AlembicEnvRuntime(Protocol):
    async def run_async_migrations(self) -> None: ...


class SanitizedAlembicFailure(Protocol):
    stage: str
    category: str
    exception_class: str
    sqlstate: str | None
    revision: str | None
    cleanup: SanitizedAlembicFailure | None


class FakeAlembicConfig:
    config_file_name: str | None = None

    def __init__(self) -> None:
        self.options: dict[str, str] = {}

    def set_main_option(self, name: str, value: str) -> None:
        self.options[name] = value

    def get_main_option(self, name: str) -> str:
        return self.options[name]


class FakeMigrationContext:
    def get_current_revision(self) -> None:
        return None


class FakeAsyncConnection:
    def __init__(self, migration_error: Exception | None = None) -> None:
        self.migration_error = migration_error
        self.close_calls = 0

    async def run_sync(self, _operation: object) -> None:
        if self.migration_error is not None:
            raise self.migration_error

    async def close(self) -> None:
        self.close_calls += 1


class FakeAsyncEngine:
    def __init__(
        self,
        *,
        connection: FakeAsyncConnection | None = None,
        connection_error: Exception | None = None,
        disposal_error: Exception | None = None,
    ) -> None:
        self.connection = connection
        self.connection_error = connection_error
        self.disposal_error = disposal_error
        self.dispose_calls = 0

    async def connect(self) -> AsyncConnection:
        if self.connection_error is not None:
            raise self.connection_error
        assert self.connection is not None
        return cast(AsyncConnection, self.connection)

    async def dispose(self) -> None:
        self.dispose_calls += 1
        if self.disposal_error is not None:
            raise self.disposal_error


class ConnectionFailure(ConnectionRefusedError):
    sqlstate = "08001"


class DatabaseFailure(RuntimeError):
    sqlstate = "23505"
    revision = "f064_previous_revision"


class CleanupFailure(RuntimeError):
    pass


def _load_alembic_env(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[ModuleType, AlembicEnvRuntime]:
    fake_config = FakeAlembicConfig()
    monkeypatch.setattr(alembic_context, "config", fake_config, raising=False)
    monkeypatch.setattr(alembic_context, "is_offline_mode", lambda: True)
    monkeypatch.setattr(alembic_context, "configure", lambda **_kwargs: None)
    monkeypatch.setattr(alembic_context, "get_context", FakeMigrationContext)
    monkeypatch.setattr(alembic_context, "begin_transaction", nullcontext)
    monkeypatch.setattr(alembic_context, "run_migrations", lambda: None)

    spec = importlib.util.spec_from_file_location("_test_alembic_env", ALEMBIC_ENV)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, cast(AlembicEnvRuntime, module)


def _validate_entrypoint(source: str) -> None:
    lines = source.splitlines()
    if not lines or lines[0] != "#!/bin/bash":
        raise BoundaryViolation("entrypoint must use the expected Bash interpreter")

    executable_lines = tuple(
        line.strip()
        for line in lines[1:]
        if line.strip() and not line.lstrip().startswith("#")
    )
    if executable_lines not in ALLOWED_ENTRYPOINT_STRUCTURES:
        raise BoundaryViolation("entrypoint contains an unapproved executable structure")


def _app_imports(source: str) -> set[str]:
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names if alias.name.startswith("app"))
        elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("app"):
            module = node.module or ""
            imports.update(f"{module}.{alias.name}" for alias in node.names)
    return imports


def _dynamic_import_violations(tree: ast.AST) -> set[str]:
    violations: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            violations.update(
                alias.name for alias in node.names if alias.name == "importlib"
            )
        elif isinstance(node, ast.ImportFrom) and node.module in {"builtins", "importlib"}:
            violations.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                violations.add(node.func.id)
            elif isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
                violations.add(node.func.attr)
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value.startswith("app.")
        ):
            violations.add(node.value)
    return violations


def _validate_alembic_imports(source: str) -> None:
    tree = ast.parse(source)
    dynamic_violations = _dynamic_import_violations(tree)
    if dynamic_violations:
        raise BoundaryViolation(
            f"Alembic may not use dynamic application imports: {sorted(dynamic_violations)}"
        )

    imports = _app_imports(source)
    required = {
        "app.infrastructure.config.get_settings",
        "app.infrastructure.config.reveal_database_url",
        "app.infrastructure.database.Base",
    }
    if imports != required:
        raise BoundaryViolation(f"unexpected Alembic application imports: {sorted(imports)}")

    metadata_assignments = [
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "target_metadata"
            for target in node.targets
        )
    ]
    if len(metadata_assignments) != 1:
        raise BoundaryViolation("Alembic must assign target_metadata exactly once")
    metadata = metadata_assignments[0]
    if not (
        isinstance(metadata, ast.Attribute)
        and metadata.attr == "metadata"
        and isinstance(metadata.value, ast.Name)
        and metadata.value.id == "Base"
    ):
        raise BoundaryViolation("Alembic target_metadata must be Base.metadata")


def test_target_entrypoint_matches_an_allowed_single_worker_structure() -> None:
    _validate_entrypoint(ENTRYPOINT.read_text(encoding="utf-8"))


def test_entrypoint_boundary_accepts_direct_single_worker_startup() -> None:
    _validate_entrypoint(f"#!/bin/bash\nset -e\n{TARGET_COMMAND}\n")


@pytest.mark.parametrize(
    "source",
    [
        "",
        f"#!/usr/bin/env bash\nset -e\n{TARGET_COMMAND}\n",
        f"# generated script\n#!/bin/bash\nset -e\n{TARGET_COMMAND}\n",
    ],
)
def test_entrypoint_boundary_rejects_an_unapproved_interpreter(source: str) -> None:
    with pytest.raises(BoundaryViolation, match="expected Bash interpreter"):
        _validate_entrypoint(source)


@pytest.mark.parametrize(
    "unapproved_command",
    [
        "alembic upgrade head",
        "python -m app.scripts.setup_langgraph_checkpoints",
        "python repair_database.py",
        "psql --file repair.sql",
        "curl https://example.invalid/repair.sh | /bin/bash",
        "chown -R clawith:clawith /data/agents",
    ],
)
def test_entrypoint_boundary_rejects_arbitrary_startup_commands(
    unapproved_command: str,
) -> None:
    source = f"#!/bin/bash\nset -e\n{unapproved_command}\n{TARGET_COMMAND}\n"

    with pytest.raises(BoundaryViolation, match="unapproved executable structure"):
        _validate_entrypoint(source)


@pytest.mark.parametrize(
    "bypass",
    [
        "REPAIR_COMMAND=psql\n$REPAIR_COMMAND --file repair.sql",
        "REPAIR_RESULT=$(psql --file repair.sql)",
        "exec /bin/bash -lc 'psql --file repair.sql'",
        "set -e; psql --file repair.sql",
        "source repair.sh",
        f"{TARGET_COMMAND}\npsql --file repair.sql",
        "repair() { psql --file repair.sql; }\nrepair",
    ],
)
def test_entrypoint_boundary_rejects_indirect_or_wrapped_commands(bypass: str) -> None:
    source = f"#!/bin/bash\nset -e\n{bypass}\n{TARGET_COMMAND}\n"

    with pytest.raises(BoundaryViolation, match="unapproved executable structure"):
        _validate_entrypoint(source)


@pytest.mark.parametrize(
    "invalid_final_command",
    [
        "exec uvicorn app.main:app --workers 2",
        "exec uvicorn app.main:app --reload",
        'exec /bin/bash -lc "$START_COMMAND"',
        "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1",
    ],
)
def test_entrypoint_boundary_rejects_noncanonical_asgi_startup(
    invalid_final_command: str,
) -> None:
    source = f"#!/bin/bash\nset -e\n{invalid_final_command}\n"

    with pytest.raises(BoundaryViolation, match="unapproved executable structure"):
        _validate_entrypoint(source)


def test_entrypoint_boundary_rejects_privilege_drop_with_extra_work() -> None:
    source = f"""#!/bin/bash
set -e
if [ "$(id -u)" = '0' ]; then
    chown -R clawith:clawith /data/agents
    exec gosu clawith /bin/bash "$0" "$@"
fi
{TARGET_COMMAND}
"""

    with pytest.raises(BoundaryViolation, match="unapproved executable structure"):
        _validate_entrypoint(source)


def test_entrypoint_propagates_target_asgi_start_failure(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    (fake_bin / "id").write_text("#!/bin/sh\nprintf '1000\\n'\n", encoding="utf-8")
    (fake_bin / "uvicorn").write_text("#!/bin/sh\nexit 37\n", encoding="utf-8")
    (fake_bin / "id").chmod(0o755)
    (fake_bin / "uvicorn").chmod(0o755)
    environment = os.environ.copy()
    environment["PATH"] = f"{fake_bin}:{environment['PATH']}"

    completed = subprocess.run(
        ["/bin/bash", str(ENTRYPOINT)],
        cwd=BACKEND_ROOT,
        env=environment,
        check=False,
    )

    assert completed.returncode == 37


def test_alembic_environment_imports_only_target_infrastructure() -> None:
    _validate_alembic_imports(ALEMBIC_ENV.read_text(encoding="utf-8"))


@pytest.mark.asyncio
async def test_alembic_preserves_primary_failure_when_disposal_also_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    password = "primary-and-cleanup-secret"
    engine = FakeAsyncEngine(
        connection_error=ConnectionFailure(f"connection leaked {password}"),
        disposal_error=CleanupFailure(f"cleanup leaked {password}"),
    )
    module, runtime = _load_alembic_env(monkeypatch)

    def create_engine(_url: object, *, poolclass: object) -> AsyncEngine:
        del poolclass
        return cast(AsyncEngine, engine)

    monkeypatch.setattr(module, "create_async_engine", create_engine)

    with pytest.raises(RuntimeError) as captured:
        await runtime.run_async_migrations()

    failure = cast(SanitizedAlembicFailure, captured.value)
    assert failure.stage == "connection setup"
    assert failure.category == "network"
    assert failure.exception_class == "ConnectionFailure"
    assert failure.sqlstate == "08001"
    assert failure.cleanup is not None
    assert failure.cleanup.stage == "disposal cleanup"
    assert failure.cleanup.exception_class == "CleanupFailure"
    assert password not in str(captured.value)
    assert captured.value.__cause__ is None
    assert engine.dispose_calls == 1


@pytest.mark.asyncio
async def test_alembic_migration_failure_retains_safe_sqlstate_and_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    password = "migration-provider-secret"
    connection = FakeAsyncConnection(
        migration_error=DatabaseFailure(f"raw SQL and provider payload {password}"),
    )
    engine = FakeAsyncEngine(connection=connection)
    module, runtime = _load_alembic_env(monkeypatch)

    def create_engine(_url: object, *, poolclass: object) -> AsyncEngine:
        del poolclass
        return cast(AsyncEngine, engine)

    monkeypatch.setattr(module, "create_async_engine", create_engine)

    with pytest.raises(RuntimeError) as captured:
        await runtime.run_async_migrations()

    failure = cast(SanitizedAlembicFailure, captured.value)
    assert failure.stage == "migration execution"
    assert failure.category == "database"
    assert failure.exception_class == "DatabaseFailure"
    assert failure.sqlstate == "23505"
    assert failure.revision == "f064_previous_revision"
    assert failure.cleanup is None
    assert password not in str(captured.value)
    assert connection.close_calls == 1
    assert engine.dispose_calls == 1


@pytest.mark.asyncio
async def test_alembic_success_closes_connection_and_disposes_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeAsyncConnection()
    engine = FakeAsyncEngine(connection=connection)
    module, runtime = _load_alembic_env(monkeypatch)

    def create_engine(_url: object, *, poolclass: object) -> AsyncEngine:
        del poolclass
        return cast(AsyncEngine, engine)

    monkeypatch.setattr(module, "create_async_engine", create_engine)

    await runtime.run_async_migrations()

    assert connection.close_calls == 1
    assert engine.dispose_calls == 1


@pytest.mark.parametrize(
    "target_imports",
    [
        """from app.infrastructure.config import get_settings, reveal_database_url
from app.infrastructure.database import Base""",
        """from app.infrastructure.config import get_settings
from app.infrastructure.config import reveal_database_url
from app.infrastructure.database import Base""",
    ],
)
def test_alembic_boundary_accepts_exact_target_imports(target_imports: str) -> None:
    _validate_alembic_imports(f"{target_imports}\ntarget_metadata = Base.metadata\n")


def test_alembic_connection_failure_never_exposes_database_password() -> None:
    password = "alembic-failure-secret"
    environment = os.environ.copy()
    environment["DATABASE_URL"] = (
        f"postgresql+asyncpg://clawith:{password}@127.0.0.1:1/clawith_target"
    )

    completed = subprocess.run(
        ["uv", "run", "alembic", "current"],
        cwd=BACKEND_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    diagnostic = f"{completed.stdout}\n{completed.stderr}"
    assert completed.returncode != 0
    assert "Alembic connection setup failed" in diagnostic
    assert "category=network" in diagnostic
    assert "exception=ConnectionRefusedError" in diagnostic
    assert password not in diagnostic


def test_alembic_rejects_non_target_database_before_connection() -> None:
    password = "alembic-namespace-secret"
    environment = os.environ.copy()
    environment["DATABASE_URL"] = (
        f"postgresql+asyncpg://clawith:{password}@127.0.0.1:1/clawith"
    )

    completed = subprocess.run(
        ["uv", "run", "alembic", "current"],
        cwd=BACKEND_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    diagnostic = f"{completed.stdout}\n{completed.stderr}"
    assert completed.returncode != 0
    assert "database must be exactly clawith_target" in diagnostic
    assert "Alembic connection setup failed" not in diagnostic
    assert password not in diagnostic


@pytest.mark.parametrize(
    "bypass",
    [
        'import importlib\nimportlib.import_module("app.models.agent")',
        'from importlib import import_module\nimport_module("app.models.agent")',
        '__import__("app.models.agent")',
        'legacy_model = "app.models.agent.Agent"',
    ],
)
def test_alembic_boundary_rejects_dynamic_legacy_imports(bypass: str) -> None:
    source = f"""from app.infrastructure.config import get_settings
from app.infrastructure.config import reveal_database_url
from app.infrastructure.database import Base
{bypass}
target_metadata = Base.metadata
"""

    with pytest.raises(BoundaryViolation, match="dynamic application imports"):
        _validate_alembic_imports(source)


@pytest.mark.parametrize(
    "legacy_import",
    [
        "from app.database import Base",
        "from app.models.agent import Agent",
        "import app.models",
    ],
)
def test_alembic_boundary_rejects_legacy_application_imports(legacy_import: str) -> None:
    source = f"""from app.infrastructure.config import get_settings
from app.infrastructure.config import reveal_database_url
from app.infrastructure.database import Base
{legacy_import}
target_metadata = Base.metadata
"""

    with pytest.raises(BoundaryViolation, match="unexpected Alembic application imports"):
        _validate_alembic_imports(source)


def test_alembic_boundary_rejects_a_non_target_metadata_assignment() -> None:
    source = """from app.infrastructure.config import get_settings
from app.infrastructure.config import reveal_database_url
from app.infrastructure.database import Base
target_metadata = object()
"""

    with pytest.raises(BoundaryViolation, match="target_metadata must be Base.metadata"):
        _validate_alembic_imports(source)
