import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api import atlassian as atlassian_api
from app.api import tools as tools_api


class _ScalarResult:
    def __init__(self, value: object) -> None:
        self._value = value

    def scalar_one_or_none(self) -> object:
        return self._value


class _RecordingDB:
    def __init__(self, existing: object | None = None) -> None:
        self.existing = existing
        self.events: list[str] = []

    async def execute(self, _statement: object) -> _ScalarResult:
        self.events.append("execute")
        return _ScalarResult(self.existing)

    def add(self, _value: object) -> None:
        self.events.append("add")

    async def commit(self) -> None:
        self.events.append("commit")

    async def rollback(self) -> None:
        self.events.append("rollback")


def _actor_and_agent() -> tuple[SimpleNamespace, SimpleNamespace]:
    actor = SimpleNamespace(id=uuid.uuid4())
    agent = SimpleNamespace(id=uuid.uuid4(), creator_id=actor.id)
    return actor, agent


@pytest.mark.asyncio
async def test_atlassian_category_config_rejects_missing_key_before_db_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor, agent = _actor_and_agent()
    db = _RecordingDB()

    async def require_manager(*_args: object) -> SimpleNamespace:
        return agent

    monkeypatch.setattr(tools_api, "_require_agent_tool_manager", require_manager)
    monkeypatch.setattr("app.core.permissions.is_agent_creator", lambda *_args: True)

    with pytest.raises(HTTPException) as exc_info:
        await tools_api.update_category_config(
            agent_id=agent.id,
            category="atlassian",
            data=tools_api.CategoryConfigUpdate(config={"cloud_id": "site"}),
            current_user=actor,
            db=db,
        )

    assert exc_info.value.status_code == 422
    assert db.events == []


@pytest.mark.asyncio
async def test_atlassian_category_config_syncs_before_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor, agent = _actor_and_agent()
    existing = SimpleNamespace(
        app_secret=None,
        extra_config={},
        is_configured=False,
    )
    db = _RecordingDB(existing)

    async def require_manager(*_args: object) -> SimpleNamespace:
        return agent

    async def sync_tools(agent_id: uuid.UUID, api_key: str) -> None:
        assert agent_id == agent.id
        assert api_key == "secret"
        db.events.append("sync")

    monkeypatch.setattr(tools_api, "_require_agent_tool_manager", require_manager)
    monkeypatch.setattr("app.core.permissions.is_agent_creator", lambda *_args: True)
    monkeypatch.setattr(tools_api, "_encrypt_sensitive_fields", lambda _config: {"api_key": "encrypted"})
    monkeypatch.setattr(atlassian_api, "_sync_atlassian_tools_for_agent", sync_tools)

    result = await tools_api.update_category_config(
        agent_id=agent.id,
        category="atlassian",
        data=tools_api.CategoryConfigUpdate(config={"api_key": " secret "}),
        current_user=actor,
        db=db,
    )

    assert result == {"ok": True}
    assert db.events == ["execute", "sync", "commit"]
    assert existing.app_secret == "encrypted"
    assert existing.is_configured is True


@pytest.mark.asyncio
async def test_atlassian_category_config_reports_sync_failure_without_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor, agent = _actor_and_agent()
    existing = SimpleNamespace(
        app_secret=None,
        extra_config={},
        is_configured=False,
    )
    db = _RecordingDB(existing)

    async def require_manager(*_args: object) -> SimpleNamespace:
        return agent

    async def fail_sync(_agent_id: uuid.UUID, _api_key: str) -> None:
        db.events.append("sync")
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(tools_api, "_require_agent_tool_manager", require_manager)
    monkeypatch.setattr("app.core.permissions.is_agent_creator", lambda *_args: True)
    monkeypatch.setattr(tools_api, "_encrypt_sensitive_fields", lambda _config: {"api_key": "encrypted"})
    monkeypatch.setattr(atlassian_api, "_sync_atlassian_tools_for_agent", fail_sync)

    with pytest.raises(HTTPException) as exc_info:
        await tools_api.update_category_config(
            agent_id=agent.id,
            category="atlassian",
            data=tools_api.CategoryConfigUpdate(config={"api_key": "secret"}),
            current_user=actor,
            db=db,
        )

    assert exc_info.value.status_code == 502
    assert db.events == ["execute", "sync", "rollback"]
    assert "commit" not in db.events
