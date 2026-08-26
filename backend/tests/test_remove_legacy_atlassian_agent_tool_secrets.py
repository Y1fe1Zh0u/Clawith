from __future__ import annotations

import importlib.util
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "remove_legacy_atlassian_agent_tool_secrets.py"
)


def _load_cleanup_module():
    spec = importlib.util.spec_from_file_location(
        "remove_legacy_atlassian_agent_tool_secrets",
        SCRIPT_PATH,
    )
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
    def __init__(
        self,
        values: list[object],
        *,
        fail_commit: bool = False,
    ) -> None:
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


def _assignment(config: object) -> SimpleNamespace:
    return SimpleNamespace(id=uuid.uuid4(), config=config)


def test_cleanup_preserves_unrelated_config_and_removes_both_legacy_keys() -> None:
    cleaned, changed = cleanup._without_legacy_secret_fields(
        {
            "api_key": "legacy-plaintext",
            "atlassian_api_key": "legacy-ciphertext",
            "cloud_id": "site-1",
            "async_completion": {"mode": "poll"},
        }
    )

    assert changed is True
    assert cleaned == {
        "cloud_id": "site-1",
        "async_completion": {"mode": "poll"},
    }


@pytest.mark.asyncio
async def test_cleanup_defaults_to_dry_run_without_mutation() -> None:
    assignment = _assignment({"api_key": "legacy", "cloud_id": "site-1"})
    batch = _Session([assignment])
    empty = _Session([])

    result = await cleanup.process_data(
        100,
        False,
        session_factory=_SessionFactory([batch, empty]),
    )

    assert result == 0
    assert assignment.config == {"api_key": "legacy", "cloud_id": "site-1"}
    assert batch.commits == 0


@pytest.mark.asyncio
async def test_cleanup_apply_is_idempotent() -> None:
    assignment = _assignment({"api_key": "legacy", "cloud_id": "site-1"})
    first_batch = _Session([assignment])
    first_empty = _Session([])

    assert (
        await cleanup.process_data(
            100,
            True,
            session_factory=_SessionFactory([first_batch, first_empty]),
        )
        == 0
    )
    assert assignment.config == {"cloud_id": "site-1"}
    assert first_batch.commits == 1

    second_batch = _Session([assignment])
    second_empty = _Session([])
    assert (
        await cleanup.process_data(
            100,
            True,
            session_factory=_SessionFactory([second_batch, second_empty]),
        )
        == 0
    )
    assert assignment.config == {"cloud_id": "site-1"}
    assert second_batch.commits == 0


@pytest.mark.asyncio
async def test_cleanup_rolls_back_failed_batch() -> None:
    assignment = _assignment({"api_key": "legacy"})
    batch = _Session([assignment], fail_commit=True)

    with pytest.raises(RuntimeError, match="commit failed"):
        await cleanup.process_data(
            100,
            True,
            session_factory=_SessionFactory([batch]),
        )

    assert batch.commits == 1
    assert batch.rollbacks == 1
