from __future__ import annotations

import ast
import os
import subprocess
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINT = BACKEND_ROOT / "entrypoint.sh"
ALEMBIC_ENV = BACKEND_ROOT / "alembic" / "env.py"
TARGET_COMMAND = (
    "exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"
)
FORBIDDEN_STARTUP_AUTHORITY = {
    "allow_migration_failure",
    "alembic upgrade",
    "alter table",
    "app_workers",
    "backfill",
    "bootstrap",
    "chown",
    "create table",
    "create_all",
    "migrate_",
    "process_role",
    "setup_langgraph_checkpoints",
    "start_command",
    "update ",
}


class BoundaryViolation(ValueError):
    """A target startup or migration boundary admits legacy authority."""


def _validate_entrypoint(source: str) -> None:
    normalized = source.lower()
    violations = sorted(
        token for token in FORBIDDEN_STARTUP_AUTHORITY if token in normalized
    )
    if violations:
        raise BoundaryViolation(f"startup contains legacy authority: {violations[0]}")

    executable_lines = [
        line.strip()
        for line in source.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not executable_lines or executable_lines[-1] != TARGET_COMMAND:
        raise BoundaryViolation("startup must end with the single-worker target ASGI command")


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


def _validate_alembic_imports(source: str) -> None:
    tree = ast.parse(source)
    imports = _app_imports(source)
    required = {
        "app.infrastructure.config.get_settings",
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


def test_target_entrypoint_has_no_schema_checkpoint_or_process_role_authority() -> None:
    _validate_entrypoint(ENTRYPOINT.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "legacy_line",
    [
        "alembic upgrade head",
        "python -m app.scripts.setup_langgraph_checkpoints",
        "python -m app.scripts.bootstrap_db",
        "python -m app.scripts.migrate_workspace",
        "python -c 'Base.metadata.create_all()'",
        "psql -c 'ALTER TABLE agents ADD COLUMN repaired bool'",
        "chown -R clawith:clawith /data/agents",
        "PROCESS_ROLE=worker",
    ],
)
def test_entrypoint_boundary_rejects_legacy_startup_authority(legacy_line: str) -> None:
    source = f"#!/bin/bash\n{legacy_line}\n{TARGET_COMMAND}\n"

    with pytest.raises(BoundaryViolation, match="startup contains legacy authority"):
        _validate_entrypoint(source)


def test_entrypoint_boundary_rejects_multiple_workers() -> None:
    source = "#!/bin/bash\nexec uvicorn app.main:app --workers 2\n"

    with pytest.raises(BoundaryViolation, match="single-worker target ASGI command"):
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
from app.infrastructure.database import Base
{legacy_import}
target_metadata = Base.metadata
"""

    with pytest.raises(BoundaryViolation, match="unexpected Alembic application imports"):
        _validate_alembic_imports(source)


def test_alembic_boundary_rejects_a_non_target_metadata_assignment() -> None:
    source = """from app.infrastructure.config import get_settings
from app.infrastructure.database import Base
target_metadata = object()
"""

    with pytest.raises(BoundaryViolation, match="target_metadata must be Base.metadata"):
        _validate_alembic_imports(source)
