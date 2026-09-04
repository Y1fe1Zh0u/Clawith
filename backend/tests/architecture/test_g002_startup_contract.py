from __future__ import annotations

import os
import re
import signal
import subprocess
from contextlib import suppress
from pathlib import Path

import pytest
import yaml

from app.infrastructure.config import BACKEND_ROOT as SETTINGS_BACKEND_ROOT
from app.infrastructure.config import ENV_FILE_PATH

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = BACKEND_ROOT.parent
SETUP = REPOSITORY_ROOT / "setup.sh"
RESTART = REPOSITORY_ROOT / "restart.sh"
BACKEND_ENV_EXAMPLE = BACKEND_ROOT / ".env.example"
ROOT_ENV_EXAMPLE = REPOSITORY_ROOT / ".env.example"
README = REPOSITORY_ROOT / "README.md"
TARGET_DATABASE = "clawith_target"
ACTIVE_DATABASE_CONFIGS = (
    BACKEND_ROOT / ".env.example",
    REPOSITORY_ROOT / "setup.sh",
    REPOSITORY_ROOT / "docker-compose.yml",
    REPOSITORY_ROOT / "docker-compose.ci.yml",
    REPOSITORY_ROOT / "docker-compose.cd.yml",
    REPOSITORY_ROOT / "deploy/.env.example",
    REPOSITORY_ROOT / "deploy/docker-compose.yml",
    REPOSITORY_ROOT / "deploy/docker-compose-multi.yml",
    REPOSITORY_ROOT / "helm/clawith/values.yaml",
)
COMPOSE_CONFIGS = (
    REPOSITORY_ROOT / "docker-compose.yml",
    REPOSITORY_ROOT / "docker-compose.ci.yml",
    REPOSITORY_ROOT / "docker-compose.cd.yml",
    REPOSITORY_ROOT / "deploy/docker-compose.yml",
    REPOSITORY_ROOT / "deploy/docker-compose-multi.yml",
)
LEGACY_CI_SCRIPTS = (
    REPOSITORY_ROOT / ".github/scripts/ci_deploy_test.sh",
    REPOSITORY_ROOT / ".github/scripts/ci_migration_test.sh",
    REPOSITORY_ROOT / ".github/scripts/ci_upgrade_test.sh",
)


class StartupContractError(RuntimeError):
    pass


def _validate_setup_source(source: str) -> None:
    required = (
        'BACKEND_ENV="$BACKEND_DIR/.env"',
        'BACKEND_ENV_EXAMPLE="$BACKEND_DIR/.env.example"',
        'TARGET_DATABASE="clawith_target"',
        "uv sync",
    )
    missing = [value for value in required if value not in source]
    forbidden = [
        value
        for value in (
            "$ROOT/.env",
            "alembic",
            "app.scripts.setup_langgraph_checkpoints",
            "create_all",
            "seed.py",
            "docker compose",
            "AGENT_RUNTIME",
        )
        if value in source
    ]
    if missing or forbidden or "/clawith?" in source:
        raise StartupContractError(
            f"invalid setup contract missing={missing} forbidden={forbidden}"
        )


def _validate_restart_source(source: str) -> None:
    command = "uv run uvicorn app.main:app"
    required = (
        'BACKEND_ENV="$BACKEND_DIR/.env"',
        "--workers 1",
        "/api/health",
        "Missing backend/.env",
    )
    missing = [value for value in required if value not in source]
    forbidden = [
        value
        for value in (
            "$ROOT/.env",
            "alembic",
            "app.scripts.setup_langgraph_checkpoints",
            "create_all",
            "seed.py",
            "docker",
            "frontend",
            "npm",
            "vite",
            "PROCESS_ROLE",
            "AGENT_RUNTIME",
            "lsof",
            "fuser",
            "kill -9",
        )
        if value.casefold() in source.casefold()
    ]
    if (
        missing
        or forbidden
        or source.count(command) != 1
        or source.index("Missing backend/.env") > source.index(command)
        or source.index(command) > source.index("/api/health")
    ):
        raise StartupContractError(
            f"invalid restart contract missing={missing} forbidden={forbidden}"
        )


def _write_executable(path: Path, source: str) -> None:
    path.write_text(source, encoding="utf-8")
    path.chmod(0o755)


def _validate_compose_quarantine(source: str) -> None:
    config = yaml.safe_load(source)
    unguarded = [
        name
        for name, service in config["services"].items()
        if service.get("profiles") != ["deferred-product"]
    ]
    if unguarded:
        raise StartupContractError(f"Compose services are not deferred: {unguarded}")


def _validate_ci_gate_sources(
    drone: str,
    github: str,
    *,
    legacy_script_exists: bool,
) -> None:
    required = (
        "pytest tests/architecture",
        "pytest --collect-only",
        "ruff check app tests",
        "pyright app",
    )
    forbidden = (
        "alembic",
        "docker compose",
        "ci_migration_test",
        "ci_deploy_test",
        "ci_upgrade_test",
    )
    invalid = legacy_script_exists or any(
        value not in source for source in (drone, github) for value in required
    ) or any(value in source for source in (drone, github) for value in forbidden)
    if invalid or "push:" not in github or "- develop" not in github or "tag" in github:
        raise StartupContractError("CI does not match the G002 gate-only contract")


def test_target_settings_owns_only_backend_dotenv() -> None:
    assert SETTINGS_BACKEND_ROOT == BACKEND_ROOT
    assert ENV_FILE_PATH == BACKEND_ROOT / ".env"


def test_backend_environment_template_is_target_only() -> None:
    assignments = {
        line.split("=", 1)[0]: line.split("=", 1)[1]
        for line in BACKEND_ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    }
    assert set(assignments) == {
        "APP_NAME",
        "DEBUG",
        "DATABASE_URL",
        "CONTROL_DATABASE_POOL_SIZE",
        "EXECUTION_DATABASE_POOL_SIZE",
        "DATABASE_POOL_MAX_OVERFLOW",
    }
    assert assignments["DATABASE_URL"].endswith(
        f"/{TARGET_DATABASE}?ssl=disable"
    )
    assert "DATABASE_URL=" not in ROOT_ENV_EXAMPLE.read_text(encoding="utf-8")


def test_setup_and_restart_match_health_only_contract() -> None:
    _validate_setup_source(SETUP.read_text(encoding="utf-8"))
    _validate_restart_source(RESTART.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "forbidden",
    [
        'cp "$ROOT/.env.example" "$ROOT/.env"',
        "uv run alembic upgrade head",
        "python -m app.scripts.setup_langgraph_checkpoints",
        "python backend/seed.py",
        "docker compose up -d",
        "DATABASE_URL=postgresql+asyncpg://clawith:clawith@localhost:5432/clawith?ssl=disable",
    ],
)
def test_setup_contract_rejects_legacy_behavior(forbidden: str) -> None:
    with pytest.raises(StartupContractError):
        _validate_setup_source(SETUP.read_text(encoding="utf-8") + forbidden)


@pytest.mark.parametrize(
    "forbidden",
    [
        "uv run alembic upgrade head",
        "python -m app.scripts.setup_langgraph_checkpoints",
        "docker compose up -d",
        "npm run dev",
        "AGENT_RUNTIME_V2_ENABLED=true",
        "kill -9 123",
    ],
)
def test_restart_contract_rejects_non_health_startup(forbidden: str) -> None:
    with pytest.raises(StartupContractError):
        _validate_restart_source(RESTART.read_text(encoding="utf-8") + forbidden)


def test_setup_synchronizes_backend_env_and_prepares_target_database(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    backend = repository / "backend"
    fake_bin = tmp_path / "bin"
    backend.mkdir(parents=True)
    fake_bin.mkdir()
    (repository / "setup.sh").write_text(SETUP.read_text(encoding="utf-8"), encoding="utf-8")
    (backend / ".env.example").write_text(
        BACKEND_ENV_EXAMPLE.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (backend / ".env").write_text(
        "DEBUG=true\nLEGACY_RUNTIME=true\n"
        "DATABASE_URL=postgresql+asyncpg://clawith:clawith@localhost:5432/clawith\n",
        encoding="utf-8",
    )
    command_log = tmp_path / "commands.log"
    _write_executable(
        fake_bin / "psql",
        '#!/bin/sh\nprintf "psql %s\\n" "$*" >> "$COMMAND_LOG"\n',
    )
    for command in ("createuser", "createdb", "uv"):
        _write_executable(
            fake_bin / command,
            f'#!/bin/sh\nprintf "{command} %s\\n" "$*" >> "$COMMAND_LOG"\n',
        )
    environment = os.environ.copy()
    environment.update(
        {
            "COMMAND_LOG": str(command_log),
            "PATH": f"{fake_bin}:{environment['PATH']}",
            "USER": "test-admin",
        }
    )

    completed = subprocess.run(
        ["bash", str(repository / "setup.sh"), "--dev"],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    backend_env = (backend / ".env").read_text(encoding="utf-8")
    assert "DEBUG=true" in backend_env
    assert "LEGACY_RUNTIME" not in backend_env
    assert f"/{TARGET_DATABASE}?ssl=disable" in backend_env
    assert not (repository / ".env").exists()
    commands = command_log.read_text(encoding="utf-8")
    assert f"createdb --host localhost --port 5432 --username test-admin --owner clawith {TARGET_DATABASE}" in commands
    assert "uv sync --extra dev" in commands


def test_restart_fails_before_start_when_backend_env_is_missing(tmp_path: Path) -> None:
    restart = tmp_path / "restart.sh"
    restart.write_text(RESTART.read_text(encoding="utf-8"), encoding="utf-8")

    completed = subprocess.run(
        ["bash", str(restart)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "Missing backend/.env" in completed.stderr
    assert not (tmp_path / ".data/backend.pid").exists()


def test_restart_starts_one_worker_and_checks_health(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    backend = repository / "backend"
    fake_bin = tmp_path / "bin"
    backend.mkdir(parents=True)
    fake_bin.mkdir()
    restart = repository / "restart.sh"
    restart.write_text(RESTART.read_text(encoding="utf-8"), encoding="utf-8")
    (backend / ".env").write_text("DATABASE_URL=target\n", encoding="utf-8")
    command_log = tmp_path / "restart-commands.log"
    _write_executable(
        fake_bin / "uv",
        '#!/bin/sh\nprintf "uv %s\\n" "$*" >> "$COMMAND_LOG"\nsleep 5\n',
    )
    _write_executable(
        fake_bin / "curl",
        '#!/bin/sh\nprintf "curl %s\\n" "$*" >> "$COMMAND_LOG"\nprintf \'{"status":"ok"}\\n\'\n',
    )
    environment = os.environ.copy()
    environment.update(
        {
            "COMMAND_LOG": str(command_log),
            "PATH": f"{fake_bin}:{environment['PATH']}",
        }
    )

    completed = subprocess.run(
        ["bash", str(restart)],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    pid = int((repository / ".data/backend.pid").read_text(encoding="utf-8"))
    try:
        assert completed.returncode == 0, completed.stderr
        commands = command_log.read_text(encoding="utf-8")
        assert commands.count("uv run uvicorn app.main:app") == 1
        assert "--workers 1" in commands
        assert "/api/health" in commands
    finally:
        with suppress(ProcessLookupError):
            os.kill(pid, signal.SIGTERM)


def test_public_readme_describes_health_only_state() -> None:
    source = README.read_text(encoding="utf-8")
    assert "current `develop` branch is at G002" in source
    assert "health-only Backend" in source
    assert "not a supported G002 product-start path" in source
    assert "Product APIs" in source and "not available" in source


def test_active_database_configs_use_target_namespace() -> None:
    legacy_patterns = (
        re.compile(r"postgresql\+asyncpg://[^\s]+/clawith(?:[?\"'\s]|$)"),
        re.compile(r"^\s*POSTGRES_DB:\s*[\"']?clawith[\"']?\s*$", re.MULTILINE),
        re.compile(r"^\s*database:\s*[\"']?clawith[\"']?\s*$", re.MULTILINE),
        re.compile(r"\bpsql\b[^\n]*\s-d\s+clawith(?:\s|$)"),
    )
    for config_path in ACTIVE_DATABASE_CONFIGS:
        source = config_path.read_text(encoding="utf-8")
        assert TARGET_DATABASE in source, config_path
        assert not any(pattern.search(source) for pattern in legacy_patterns), config_path


def test_helm_templates_resolve_database_from_target_values() -> None:
    values = yaml.safe_load(
        (REPOSITORY_ROOT / "helm/clawith/values.yaml").read_text(encoding="utf-8")
    )
    assert values["postgresql"]["auth"]["database"] == TARGET_DATABASE
    assert values["postgresql"]["external"]["database"] == TARGET_DATABASE
    backend_template = (
        REPOSITORY_ROOT / "helm/clawith/templates/backend.yaml"
    ).read_text(encoding="utf-8")
    postgres_template = (
        REPOSITORY_ROOT / "helm/clawith/templates/postgresql.yaml"
    ).read_text(encoding="utf-8")
    assert 'include "clawith.postgresql.database"' in backend_template
    assert ".Values.postgresql.auth.database" in postgres_template


def test_deferred_compose_and_helm_paths_require_explicit_opt_in() -> None:
    for config_path in COMPOSE_CONFIGS:
        _validate_compose_quarantine(config_path.read_text(encoding="utf-8"))
    values = yaml.safe_load(
        (REPOSITORY_ROOT / "helm/clawith/values.yaml").read_text(encoding="utf-8")
    )
    assert values["g002Deferred"] is True
    templates_root = REPOSITORY_ROOT / "helm/clawith/templates"
    for template_path in sorted(templates_root.glob("*.yaml")):
        template = template_path.read_text(encoding="utf-8")
        if "kind:" not in template:
            continue
        assert "not .Values.g002Deferred" in template, template_path.name
        assert template.index("not .Values.g002Deferred") < template.index("kind:"), (
            template_path.name
        )
    namespace_template = (
        REPOSITORY_ROOT / "helm/clawith/templates/namespace.yaml"
    ).read_text(encoding="utf-8")
    assert namespace_template.count("not .Values.g002Deferred") == 2
    assert namespace_template.count("kind:") == 2


def test_legacy_ci_product_workflows_are_replaced_by_g002_gates() -> None:
    drone = (REPOSITORY_ROOT / ".github/drone.yml").read_text(encoding="utf-8")
    github = (REPOSITORY_ROOT / ".github/workflows/release.yml").read_text(
        encoding="utf-8"
    )
    assert isinstance(yaml.safe_load(drone), dict)
    assert isinstance(yaml.safe_load(github), dict)
    _validate_ci_gate_sources(
        drone,
        github,
        legacy_script_exists=any(path.exists() for path in LEGACY_CI_SCRIPTS),
    )


def test_compose_quarantine_rejects_an_unguarded_service() -> None:
    source = "services:\n  backend:\n    image: target\n"
    with pytest.raises(StartupContractError, match="not deferred"):
        _validate_compose_quarantine(source)


@pytest.mark.parametrize("forbidden", ["alembic", "docker compose", "ci_upgrade_test"])
def test_ci_gate_contract_rejects_legacy_work(forbidden: str) -> None:
    drone = (REPOSITORY_ROOT / ".github/drone.yml").read_text(encoding="utf-8")
    github = (REPOSITORY_ROOT / ".github/workflows/release.yml").read_text(
        encoding="utf-8"
    )
    with pytest.raises(StartupContractError, match="gate-only"):
        _validate_ci_gate_sources(
            f"{drone}\n{forbidden}",
            github,
            legacy_script_exists=False,
        )


def test_ci_gate_contract_rejects_a_restored_legacy_script() -> None:
    drone = (REPOSITORY_ROOT / ".github/drone.yml").read_text(encoding="utf-8")
    github = (REPOSITORY_ROOT / ".github/workflows/release.yml").read_text(
        encoding="utf-8"
    )
    with pytest.raises(StartupContractError, match="gate-only"):
        _validate_ci_gate_sources(
            drone,
            github,
            legacy_script_exists=True,
        )
