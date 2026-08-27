from __future__ import annotations

import importlib.util
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "remove_legacy_atlassian_agent_tool_secrets.py"


def _load_cleanup_module():
    spec = importlib.util.spec_from_file_location("atlassian_cleanup", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cleanup = _load_cleanup_module()


class _Result:
    def __init__(self, values: list[object]) -> None:
        self._values = values

    def scalars(self) -> _Result:
        return self

    def all(self) -> list[object]:
        return self._values


class _Session:
    def __init__(self, values: list[object], *, fail_commit: bool = False) -> None:
        self.values = values
        self.fail_commit = fail_commit
        self.commits = 0
        self.rollbacks = 0

    async def execute(self, _statement: object) -> _Result:
        return _Result(self.values)

    async def commit(self) -> None:
        self.commits += 1
        if self.fail_commit:
            raise RuntimeError("commit failed")

    async def rollback(self) -> None:
        self.rollbacks += 1


class _SessionContext:
    def __init__(self, session: _Session) -> None:
        self.session = session

    async def __aenter__(self) -> _Session:
        return self.session

    async def __aexit__(self, *_args: object) -> None:
        return None


class _SessionFactory:
    def __init__(self, sessions: list[_Session]) -> None:
        self.sessions = iter(sessions)

    def __call__(self) -> _SessionContext:
        return _SessionContext(next(self.sessions))


def _row(config: object) -> SimpleNamespace:
    return SimpleNamespace(id=uuid.uuid4(), config=config)


def _channel(extra_config: object) -> SimpleNamespace:
    return SimpleNamespace(id=uuid.uuid4(), extra_config=extra_config)


def _sessions(
    tool: object,
    assignment: object,
    channel: object,
) -> list[_Session]:
    return [
        _Session([tool]),
        _Session([]),
        _Session([assignment]),
        _Session([]),
        _Session([channel]),
        _Session([]),
    ]


@pytest.mark.asyncio
async def test_cleanup_dry_run_covers_all_secret_copies_without_mutation() -> None:
    tool = _row({"api_key": "tool-secret", "label": "shared"})
    assignment = _row({"atlassian_api_key": "agent-secret", "cloud_id": "site"})
    channel = _channel({"api_secret": "duplicate", "cloud_id": "site"})
    sessions = _sessions(tool, assignment, channel)
    assert await cleanup.process_data(100, False, session_factory=_SessionFactory(sessions)) == 0
    assert tool.config == {"api_key": "tool-secret", "label": "shared"}
    assert assignment.config == {"atlassian_api_key": "agent-secret", "cloud_id": "site"}
    assert channel.extra_config == {"api_secret": "duplicate", "cloud_id": "site"}
    assert all(session.commits == 0 for session in sessions)


@pytest.mark.asyncio
async def test_cleanup_apply_preserves_config_and_is_idempotent() -> None:
    tool = _row({"api_key": "legacy", "label": "shared"})
    assignment = _row({"atlassian_api_key": "legacy", "cloud_id": "site"})
    channel = _channel({"app_secret": "legacy", "cloud_id": "site"})
    first = _sessions(tool, assignment, channel)
    assert await cleanup.process_data(100, True, session_factory=_SessionFactory(first)) == 0
    assert tool.config == {"label": "shared"}
    assert assignment.config == {"cloud_id": "site"}
    assert channel.extra_config == {"cloud_id": "site"}
    assert first[0].commits == 1
    assert first[2].commits == 1
    assert first[4].commits == 1

    second = _sessions(tool, assignment, channel)
    assert await cleanup.process_data(100, True, session_factory=_SessionFactory(second)) == 0
    assert all(session.commits == 0 for session in second)


@pytest.mark.asyncio
@pytest.mark.parametrize("failure_scope", ["tool", "assignment", "channel"])
async def test_cleanup_rolls_back_failed_batch(failure_scope: str) -> None:
    sessions = _sessions(
        _row({"api_key": "legacy"}),
        _row({"api_key": "legacy"}),
        _channel({"api_key": "legacy"}),
    )
    failing_index = {"tool": 0, "assignment": 2, "channel": 4}[failure_scope]
    sessions[failing_index].fail_commit = True
    with pytest.raises(RuntimeError, match="commit failed"):
        await cleanup.process_data(100, True, session_factory=_SessionFactory(sessions))
    assert sessions[failing_index].commits == 1
    assert sessions[failing_index].rollbacks == 1


@pytest.mark.asyncio
async def test_cleanup_queries_cover_identity_variants_and_channel_duplicates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    statements: list[tuple[str, str]] = []

    async def capture(
        _model: object,
        statement: object,
        config_field: str,
        *_args: object,
    ) -> tuple[int, int, int]:
        statements.append((str(statement), config_field))
        return (0, 0, 0)

    monkeypatch.setattr(cleanup, "_process_batches", capture)
    assert await cleanup.process_data(100, False) == 0

    tool_sql, assignment_sql, channel_sql = [sql for sql, _field in statements]
    for sql in (tool_sql, assignment_sql):
        for field in ("category", "mcp_server_name", "mcp_server_url", "name"):
            assert field in sql
    assert "channel_type" in channel_sql
    assert [field for _sql, field in statements] == [
        "config",
        "config",
        "extra_config",
    ]
