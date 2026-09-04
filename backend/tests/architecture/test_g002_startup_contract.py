from __future__ import annotations

import os
import re
import shlex
import shutil
import signal
import stat
import subprocess
import time
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


def _shell_execution_facts(source: str) -> set[str]:
    facts: set[str] = set()
    assignments: dict[str, str] = {}
    for line in source.replace("\\\n", " ").splitlines():
        lexer = shlex.shlex(line, posix=True, punctuation_chars="|&;<>")
        lexer.commenters = "#"
        lexer.whitespace_split = True
        try:
            tokens = list(lexer)
        except ValueError:
            continue
        if not tokens:
            continue
        for token in tokens:
            match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)=(.*)", token, re.DOTALL)
            if match:
                value = match.group(2)
                for name, assigned in assignments.items():
                    value = value.replace(f"${{{name}}}", assigned)
                    value = re.sub(rf"\${re.escape(name)}\b", assigned, value)
                assignments[match.group(1)] = value
        expanded = line
        for name, assigned in assignments.items():
            expanded = expanded.replace(f"${{{name}}}", assigned)
            expanded = re.sub(rf"\${re.escape(name)}\b", assigned, expanded)
        expanded_lexer = shlex.shlex(
            expanded,
            posix=True,
            punctuation_chars="|&;<>",
        )
        expanded_lexer.commenters = "#"
        expanded_lexer.whitespace_split = True
        try:
            expanded_tokens = list(expanded_lexer)
        except ValueError:
            continue
        commands = [
            token
            for token in expanded_tokens
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", token, re.DOTALL)
            and token not in {"!", "env", "exec", "export", "if", "then"}
        ]
        if not commands:
            continue
        command = Path(commands[0]).name
        if command in {"echo", "printf"}:
            continue
        normalized = " ".join(expanded_tokens)
        if command == "alembic" or re.search(r"(?:^|\s)alembic(?:\s|$)", normalized):
            facts.add("alembic")
        if "app.scripts.setup_langgraph_checkpoints" in normalized:
            facts.add("checkpoint-installer")
        if "docker compose" in normalized or command in {"docker", "docker-compose"}:
            facts.add("docker")
        if any(
            name in normalized
            for name in (
                "ci_deploy_test",
                "ci_migration_test",
                "ci_upgrade_test",
            )
        ):
            facts.add("legacy-ci")
        if "pytest tests/architecture" in normalized:
            facts.add("architecture-gate")
        if "pytest --collect-only" in normalized:
            facts.add("collection-gate")
        if "ruff check app tests" in normalized:
            facts.add("ruff-gate")
        if "pyright app" in normalized:
            facts.add("pyright-gate")
    return facts


def _yaml_executable_commands(source: str) -> list[str]:
    parsed = yaml.safe_load(source)
    commands: list[str] = []

    def visit(value: object, *, executable: bool = False) -> None:
        if executable and isinstance(value, str):
            commands.append(value)
            return
        if isinstance(value, list):
            for item in value:
                visit(item, executable=executable)
            return
        if not isinstance(value, dict):
            return
        for raw_key, nested in value.items():
            visit(
                nested,
                executable=str(raw_key).casefold()
                in {"command", "commands", "run", "script"},
            )

    visit(parsed)
    return commands


def _exact_ci_gate_facts(commands: list[str]) -> set[str]:
    expected = {
        (
            "uv",
            "run",
            "--extra",
            "dev",
            "pytest",
            "tests/architecture",
        ): "architecture-gate",
        (
            "uv",
            "run",
            "--extra",
            "dev",
            "pytest",
            "--collect-only",
        ): "collection-gate",
        (
            "uv",
            "run",
            "--extra",
            "dev",
            "ruff",
            "check",
            "app",
            "tests",
        ): "ruff-gate",
        (
            "uv",
            "run",
            "--extra",
            "dev",
            "pyright",
            "app",
        ): "pyright-gate",
    }
    facts: set[str] = set()
    for command in commands:
        for line in command.splitlines():
            lexer = shlex.shlex(line, posix=True, punctuation_chars="|&;<>")
            lexer.commenters = "#"
            lexer.whitespace_split = True
            try:
                tokens = tuple(lexer)
            except ValueError:
                continue
            fact = expected.get(tokens)
            if fact is not None:
                facts.add(fact)
    return facts


def _validate_setup_source(source: str) -> None:
    required = (
        'BACKEND_ENV="$BACKEND_DIR/.env"',
        'BACKEND_ENV_EXAMPLE="$BACKEND_DIR/.env.example"',
        'TARGET_DATABASE="clawith_target"',
        "uv sync",
    )
    missing = [value for value in required if value not in source]
    forbidden = sorted(_shell_execution_facts(source))
    forbidden.extend(
        value
        for value in ("$ROOT/.env", "create_all", "seed.py", "AGENT_RUNTIME")
        if value in source
    )
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
    forbidden = sorted(_shell_execution_facts(source))
    forbidden.extend(
        value
        for value in (
            "$ROOT/.env",
            "create_all",
            "seed.py",
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
    )
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


def _read_process_pid(process_file: Path) -> int:
    fields = dict(
        line.split("=", 1)
        for line in process_file.read_text(encoding="utf-8").splitlines()
    )
    return int(fields["pid"])


def _wait_for_path(path: Path, *, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.02)
    raise AssertionError(f"timed out waiting for {path}")


def _process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def _restart_fixture(
    tmp_path: Path,
    *,
    uv_source: str,
    curl_source: str,
) -> tuple[Path, Path, dict[str, str]]:
    repository = tmp_path / "repo"
    backend = repository / "backend"
    fake_bin = tmp_path / "bin"
    backend.mkdir(parents=True)
    fake_bin.mkdir()
    restart = repository / "restart.sh"
    restart.write_text(RESTART.read_text(encoding="utf-8"), encoding="utf-8")
    (backend / ".env").write_text("DATABASE_URL=target\n", encoding="utf-8")
    _write_executable(fake_bin / "uv", uv_source)
    _write_executable(fake_bin / "curl", curl_source)
    environment = os.environ.copy()
    environment["PATH"] = f"{fake_bin}:{environment['PATH']}"
    environment["CLAWITH_STOP_ATTEMPTS"] = "20"
    return repository, fake_bin, environment


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
    required_facts = {
        "architecture-gate",
        "collection-gate",
        "pyright-gate",
        "ruff-gate",
    }
    try:
        drone_config = yaml.load(drone, Loader=yaml.BaseLoader)
        github_config = yaml.load(github, Loader=yaml.BaseLoader)
        drone_commands = _yaml_executable_commands(drone)
        github_commands = _yaml_executable_commands(github)
    except yaml.YAMLError as exc:
        raise StartupContractError("CI configuration is invalid YAML") from exc
    drone_facts = _shell_execution_facts("\n".join(drone_commands))
    github_facts = _shell_execution_facts("\n".join(github_commands))
    drone_gate_facts = _exact_ci_gate_facts(drone_commands)
    github_gate_facts = _exact_ci_gate_facts(github_commands)
    forbidden_facts = {"alembic", "checkpoint-installer", "docker", "legacy-ci"}
    drone_events = set(drone_config.get("trigger", {}).get("event", []))
    github_triggers = github_config.get("on", {})
    github_push_branches = github_triggers.get("push", {}).get("branches", [])
    invalid = (
        legacy_script_exists
        or not required_facts <= drone_gate_facts
        or not required_facts <= github_gate_facts
        or bool(forbidden_facts & (drone_facts | github_facts))
        or drone_events != {"pull_request", "push"}
        or set(github_triggers) != {"pull_request", "push", "workflow_dispatch"}
        or github_push_branches != ["develop"]
    )
    if invalid:
        raise StartupContractError("CI does not match the G002 gate-only contract")


def _validate_helm_template_quarantine(source: str) -> None:
    condition_stack: list[tuple[str, bool]] = []
    directive = re.compile(r"^\{\{-?\s*(if|range|with)\s+(.+?)\s*\}\}$")
    for line_number, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped == "---" or stripped.startswith("#"):
            continue
        opened = directive.match(stripped)
        if opened:
            condition_stack.append(
                (opened.group(2) if opened.group(1) == "if" else "", False)
            )
            continue
        if re.fullmatch(r"\{\{-?\s*else\s*\}\}", stripped):
            if not condition_stack:
                raise StartupContractError("Helm template has an unmatched else")
            condition, in_else = condition_stack[-1]
            condition_stack[-1] = (condition, not in_else)
            continue
        if re.fullmatch(r"\{\{-?\s*end\s*\}\}", stripped):
            if not condition_stack:
                raise StartupContractError("Helm template has an unmatched end")
            condition_stack.pop()
            continue
        if re.search(r"\{\{-?\s*(?:else|end|if|range|with)\b", stripped):
            raise StartupContractError("Helm control directive must occupy one line")
        if stripped.startswith("{{-") and re.fullmatch(
                r"\{\{-\s*(?:include|template|toYaml)\b.+?-?\}\}",
                stripped,
            ) is None:
            raise StartupContractError("Helm template syntax is not recognized")
        if not any(
            "not .Values.g002Deferred" in condition and not in_else
            for condition, in_else in condition_stack
        ):
            raise StartupContractError(
                f"Helm resource content is not quarantined at line {line_number}"
            )
    if condition_stack:
        raise StartupContractError("Helm template has an unclosed control block")


def _inject_drone_commands(source: str, commands: list[str]) -> str:
    config = yaml.safe_load(source)
    config["steps"][0]["commands"] = [
        *commands,
        *config["steps"][0]["commands"],
    ]
    return yaml.safe_dump(config, sort_keys=False)


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
    assert SETUP.stat().st_mode & stat.S_IXUSR
    assert RESTART.stat().st_mode & stat.S_IXUSR


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


@pytest.mark.parametrize(
    "split_command",
    [
        'MIG=alem\nMIG="${MIG}bic"\n"$MIG" upgrade head\n',
        (
            "MODULE=app.scripts.setup_langgraph_\n"
            'MODULE="${MODULE}checkpoints"\n'
            'python -m "$MODULE"\n'
        ),
    ],
)
def test_startup_contract_rejects_split_token_migration_commands(
    split_command: str,
) -> None:
    with pytest.raises(StartupContractError):
        _validate_setup_source(SETUP.read_text(encoding="utf-8") + split_command)
    with pytest.raises(StartupContractError):
        _validate_restart_source(RESTART.read_text(encoding="utf-8") + split_command)


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
    assert not (tmp_path / ".data/backend.process").exists()


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

    process_file = repository / ".data/backend.process"
    pid = _read_process_pid(process_file)
    try:
        assert completed.returncode == 0, completed.stderr
        commands = command_log.read_text(encoding="utf-8")
        assert commands.count("uv run uvicorn app.main:app") == 1
        assert "--workers 1" in commands
        assert "/api/health" in commands
    finally:
        with suppress(ProcessLookupError):
            os.kill(pid, signal.SIGTERM)


def test_restart_refuses_to_signal_reused_stale_pid(tmp_path: Path) -> None:
    repository, _fake_bin, environment = _restart_fixture(
        tmp_path,
        uv_source="#!/bin/sh\nexit 99\n",
        curl_source="#!/bin/sh\nexit 99\n",
    )
    process_file = repository / ".data/backend.process"
    process_file.parent.mkdir()
    process_file.write_text(
        f"pid={os.getpid()}\nstart=stale-start-identity\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        ["bash", str(repository / "restart.sh")],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "Refusing to signal" in completed.stderr
    assert _process_exists(os.getpid())
    assert process_file.exists()


def test_restart_identity_capture_failure_stops_pending_child(tmp_path: Path) -> None:
    term_log = tmp_path / "term.log"
    repository, fake_bin, environment = _restart_fixture(
        tmp_path,
        uv_source=(
            "#!/bin/sh\n"
            "trap 'printf terminated > \"$TERM_LOG\"; exit 0' TERM\n"
            "while :; do sleep 0.1; done\n"
        ),
        curl_source="#!/bin/sh\nexit 1\n",
    )
    real_ps = shutil.which("ps")
    assert real_ps is not None
    _write_executable(
        fake_bin / "ps",
        (
            "#!/bin/sh\n"
            "case \"$*\" in\n"
            "  *lstart=*) exit 0 ;;\n"
            "  *) exec \"$REAL_PS\" \"$@\" ;;\n"
            "esac\n"
        ),
    )
    environment.update({"REAL_PS": real_ps, "TERM_LOG": str(term_log)})

    completed = subprocess.run(
        ["bash", str(repository / "restart.sh")],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "Could not capture" in completed.stderr
    match = re.search(r"pid=(\d+)", completed.stderr)
    assert match is not None
    assert not _process_exists(int(match.group(1)))
    assert not (repository / ".data/backend.process").exists()


def test_restart_timeout_stops_owned_child_and_removes_evidence(tmp_path: Path) -> None:
    term_log = tmp_path / "term.log"
    repository, _fake_bin, environment = _restart_fixture(
        tmp_path,
        uv_source=(
            "#!/bin/sh\n"
            "trap 'printf terminated > \"$TERM_LOG\"; exit 0' TERM\n"
            "while :; do sleep 0.1; done\n"
        ),
        curl_source="#!/bin/sh\nexit 1\n",
    )
    environment.update(
        {
            "CLAWITH_HEALTH_ATTEMPTS": "1",
            "TERM_LOG": str(term_log),
        }
    )

    completed = subprocess.run(
        ["bash", str(repository / "restart.sh")],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "timed out" in completed.stderr
    assert term_log.read_text(encoding="utf-8") == "terminated"
    assert not (repository / ".data/backend.process").exists()


def test_restart_child_failure_removes_terminal_evidence(tmp_path: Path) -> None:
    repository, _fake_bin, environment = _restart_fixture(
        tmp_path,
        uv_source="#!/bin/sh\nsleep 0.1\nexit 7\n",
        curl_source="#!/bin/sh\nsleep 0.2\nexit 1\n",
    )

    completed = subprocess.run(
        ["bash", str(repository / "restart.sh")],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "exited before becoming healthy" in completed.stderr
    assert not (repository / ".data/backend.process").exists()


@pytest.mark.parametrize(
    ("sent_signal", "expected_status"),
    [(signal.SIGINT, 130), (signal.SIGTERM, 143)],
)
def test_restart_signal_stops_owned_child(
    tmp_path: Path,
    sent_signal: signal.Signals,
    expected_status: int,
) -> None:
    term_log = tmp_path / "term.log"
    ready_log = tmp_path / "ready.log"
    repository, _fake_bin, environment = _restart_fixture(
        tmp_path,
        uv_source=(
            "#!/bin/sh\n"
            "trap 'printf terminated > \"$TERM_LOG\"; exit 0' TERM\n"
            "printf ready > \"$READY_LOG\"\n"
            "while :; do sleep 0.1; done\n"
        ),
        curl_source="#!/bin/sh\nsleep 0.1\nexit 1\n",
    )
    environment.update(
        {
            "CLAWITH_HEALTH_ATTEMPTS": "1000",
            "READY_LOG": str(ready_log),
            "TERM_LOG": str(term_log),
        }
    )
    process = subprocess.Popen(
        ["bash", str(repository / "restart.sh")],
        cwd=repository,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    process_file = repository / ".data/backend.process"
    _wait_for_path(process_file)
    _wait_for_path(ready_log)

    process.send_signal(sent_signal)
    _stdout, stderr = process.communicate(timeout=5)

    assert process.returncode == expected_status, stderr
    assert term_log.read_text(encoding="utf-8") == "terminated"
    assert not process_file.exists()


def test_restart_retains_evidence_when_owned_child_cannot_stop(tmp_path: Path) -> None:
    repository, _fake_bin, environment = _restart_fixture(
        tmp_path,
        uv_source=(
            "#!/bin/sh\n"
            "trap '' TERM\n"
            "while :; do sleep 0.1; done\n"
        ),
        curl_source="#!/bin/sh\nexit 1\n",
    )
    environment.update(
        {
            "CLAWITH_HEALTH_ATTEMPTS": "1",
            "CLAWITH_STOP_ATTEMPTS": "1",
        }
    )

    completed = subprocess.run(
        ["bash", str(repository / "restart.sh")],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    process_file = repository / ".data/backend.process"
    pid = _read_process_pid(process_file)
    try:
        assert completed.returncode == 1
        assert "evidence retained" in completed.stderr
        assert _process_exists(pid)
    finally:
        with suppress(ProcessLookupError):
            os.kill(pid, signal.SIGKILL)


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
        _validate_helm_template_quarantine(template)
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
    poisoned_drone = _inject_drone_commands(drone, [forbidden])
    with pytest.raises(StartupContractError, match="gate-only"):
        _validate_ci_gate_sources(
            poisoned_drone,
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


@pytest.mark.parametrize(
    "split_commands",
    [
        ["MIG=alem", 'MIG="${MIG}bic"', '"$MIG" upgrade head'],
        [
            "MODULE=app.scripts.setup_langgraph_",
            'MODULE="${MODULE}checkpoints"',
            'python -m "$MODULE"',
        ],
    ],
)
def test_ci_gate_contract_rejects_split_token_commands(
    split_commands: list[str],
) -> None:
    drone = (REPOSITORY_ROOT / ".github/drone.yml").read_text(encoding="utf-8")
    github = (REPOSITORY_ROOT / ".github/workflows/release.yml").read_text(
        encoding="utf-8"
    )
    poisoned_drone = _inject_drone_commands(drone, split_commands)
    with pytest.raises(StartupContractError, match="gate-only"):
        _validate_ci_gate_sources(
            poisoned_drone,
            github,
            legacy_script_exists=False,
        )


def test_ci_gate_contract_allows_inert_migration_prose() -> None:
    drone = (REPOSITORY_ROOT / ".github/drone.yml").read_text(encoding="utf-8")
    github = (REPOSITORY_ROOT / ".github/workflows/release.yml").read_text(
        encoding="utf-8"
    )
    documented_drone = f"description: alembic and checkpoint installers are disabled\n{drone}"
    _validate_ci_gate_sources(
        documented_drone,
        github,
        legacy_script_exists=False,
    )


def test_ci_comments_cannot_supply_required_gate_or_trigger() -> None:
    drone = (REPOSITORY_ROOT / ".github/drone.yml").read_text(encoding="utf-8")
    github = (REPOSITORY_ROOT / ".github/workflows/release.yml").read_text(
        encoding="utf-8"
    )
    missing_gate = github.replace(
        "uv run --extra dev pyright app",
        "echo pyright-disabled",
    )
    missing_gate = f"# uv run --extra dev pyright app\n{missing_gate}"
    with pytest.raises(StartupContractError, match="gate-only"):
        _validate_ci_gate_sources(
            drone,
            missing_gate,
            legacy_script_exists=False,
        )
    missing_push = github.replace(
        "  push:\n    branches:\n      - develop\n",
        "  # push:\n  #   branches: [develop]\n",
    )
    with pytest.raises(StartupContractError, match="gate-only"):
        _validate_ci_gate_sources(
            drone,
            missing_push,
            legacy_script_exists=False,
        )


def test_ci_short_circuit_or_echo_cannot_supply_required_gate() -> None:
    drone = (REPOSITORY_ROOT / ".github/drone.yml").read_text(encoding="utf-8")
    github = (REPOSITORY_ROOT / ".github/workflows/release.yml").read_text(
        encoding="utf-8"
    )
    spoofed = github.replace(
        "uv run --extra dev pyright app",
        "true || echo 'uv run --extra dev pyright app'",
    )
    with pytest.raises(StartupContractError, match="gate-only"):
        _validate_ci_gate_sources(
            drone,
            spoofed,
            legacy_script_exists=False,
        )


def test_helm_quarantine_rejects_comment_spoof_and_unguarded_resource() -> None:
    source = (
        "# {{- if not .Values.g002Deferred }}\n"
        "apiVersion: v1\n"
        "kind: Secret\n"
    )
    with pytest.raises(StartupContractError, match="not quarantined"):
        _validate_helm_template_quarantine(source)


@pytest.mark.parametrize(
    "source",
    [
        (
            "{{- if not .Values.g002Deferred }}\n"
            "{{- else }}\n"
            "apiVersion: v1\nkind: Secret\n"
            "{{- end }}\n"
        ),
        "{{- if not .Values.g002Deferred }} kind: Secret\n",
        "{{- unknown .Values.g002Deferred }}\nkind: Secret\n",
        "{{- if not .Values.g002Deferred }}\nkind: Secret\n",
    ],
)
def test_helm_quarantine_rejects_else_inline_unknown_and_unclosed_templates(
    source: str,
) -> None:
    with pytest.raises(StartupContractError):
        _validate_helm_template_quarantine(source)


def test_helm_quarantine_allows_inert_comments_without_resources() -> None:
    _validate_helm_template_quarantine(
        "# kind: Secret\n# not .Values.g002Deferred\n"
    )
