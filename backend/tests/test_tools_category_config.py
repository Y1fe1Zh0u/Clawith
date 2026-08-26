import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api import atlassian as atlassian_api
from app.api import tools as tools_api
from app.models.tool import AgentTool, Tool
from app.services import agent_tools


class _ScalarResult:
    def __init__(self, value: object) -> None:
        self._value = value

    def scalar_one_or_none(self) -> object:
        return self._value


class _ListResult:
    def __init__(self, values: list[object]) -> None:
        self._values = values

    def scalars(self) -> "_ListResult":
        return self

    def all(self) -> list[object]:
        return self._values


class _RecordingDB:
    def __init__(self, existing: object | None = None) -> None:
        self.existing = existing
        self.events: list[str] = []

    async def execute(self, _statement: object) -> _ScalarResult:
        self.events.append("execute")
        return _ScalarResult(self.existing)

    def add(self, _value: object) -> None:
        self.events.append("add")

    async def delete(self, _value: object) -> None:
        self.events.append("delete")

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

    async def sync_tools(agent_id: uuid.UUID, api_key: str, sync_db: object) -> None:
        assert agent_id == agent.id
        assert api_key == "secret"
        assert sync_db is db
        db.events.append("sync")

    monkeypatch.setattr(tools_api, "_require_agent_tool_manager", require_manager)
    monkeypatch.setattr("app.core.permissions.is_agent_creator", lambda *_args: True)
    monkeypatch.setattr(tools_api, "_encrypt_sensitive_fields", lambda _config: {"api_key": "encrypted"})
    monkeypatch.setattr("app.core.security.encrypt_data", lambda _value, _secret: "encrypted")
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

    async def fail_sync(
        _agent_id: uuid.UUID,
        _api_key: str,
        sync_db: object,
    ) -> None:
        assert sync_db is db
        db.events.append("sync")
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(tools_api, "_require_agent_tool_manager", require_manager)
    monkeypatch.setattr("app.core.permissions.is_agent_creator", lambda *_args: True)
    monkeypatch.setattr(tools_api, "_encrypt_sensitive_fields", lambda _config: {"api_key": "encrypted"})
    monkeypatch.setattr("app.core.security.encrypt_data", lambda _value, _secret: "encrypted")
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


@pytest.mark.asyncio
async def test_legacy_atlassian_config_uses_owned_sync_before_single_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor, agent = _actor_and_agent()
    existing = SimpleNamespace(
        id=uuid.uuid4(),
        agent_id=agent.id,
        channel_type="atlassian",
        app_secret=None,
        extra_config={},
        is_configured=False,
        is_connected=False,
        created_at=None,
    )
    db = _RecordingDB(existing)

    async def check_access(*_args: object) -> tuple[SimpleNamespace, str]:
        return agent, "manage"

    async def sync_tools(
        sync_agent_id: uuid.UUID,
        api_key: str,
        sync_db: object,
    ) -> None:
        assert sync_agent_id == agent.id
        assert api_key == "secret"
        assert sync_db is db
        db.events.append("sync")

    monkeypatch.setattr(atlassian_api, "check_agent_access", check_access)
    monkeypatch.setattr(atlassian_api, "is_agent_creator", lambda *_args: True)
    monkeypatch.setattr("app.core.security.encrypt_data", lambda _value, _secret: "ciphertext-value")
    monkeypatch.setattr(atlassian_api, "_sync_atlassian_tools_for_agent", sync_tools)

    result = await atlassian_api.configure_atlassian_channel(
        agent_id=agent.id,
        data={"api_key": "secret", "cloud_id": "site"},
        current_user=actor,
        db=db,
    )

    assert result["is_configured"] is True
    assert db.events == ["execute", "sync", "commit"]
    assert existing.app_secret == "ciphertext-value"


@pytest.mark.asyncio
async def test_atlassian_sync_persists_only_encrypted_agent_tool_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent_id = uuid.uuid4()
    added: list[object] = []
    commits: list[object] = []
    query_results = iter((_ScalarResult(None), _ScalarResult(None)))
    sync_db = object()

    class FakeMCPClient:
        def __init__(self, _url: str, *, api_key: str) -> None:
            assert api_key == "plaintext-secret"

        async def list_tools(self) -> list[dict[str, object]]:
            return [
                {
                    "name": "search",
                    "description": "Search Atlassian",
                    "inputSchema": {"type": "object", "properties": {}},
                }
            ]

    async def execute(db: object, _statement: object) -> _ScalarResult:
        assert db is sync_db
        return next(query_results)

    def add(db: object, value: object) -> None:
        assert db is sync_db
        if isinstance(value, Tool) and value.id is None:
            value.id = uuid.uuid4()
        added.append(value)

    async def flush(db: object) -> None:
        assert db is sync_db

    async def commit(db: object) -> None:
        commits.append(db)

    monkeypatch.setattr("app.services.mcp_client.MCPClient", FakeMCPClient)
    monkeypatch.setattr(atlassian_api.query_dao, "execute", execute)
    monkeypatch.setattr(atlassian_api.query_dao, "add", add)
    monkeypatch.setattr(atlassian_api.query_dao, "flush", flush)
    monkeypatch.setattr(atlassian_api.query_dao, "commit", commit)
    monkeypatch.setattr("app.core.security.encrypt_data", lambda _value, _secret: "ciphertext-value")

    await atlassian_api._sync_atlassian_tools_for_agent(
        agent_id,
        "plaintext-secret",
        sync_db,
    )

    assignment = next(value for value in added if isinstance(value, AgentTool))
    assert assignment.config == {"api_key": "ciphertext-value"}
    assert "plaintext-secret" not in assignment.config.values()
    assert commits == []


@pytest.mark.asyncio
async def test_corrupt_atlassian_ciphertext_is_rejected_before_runtime_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent_id = uuid.uuid4()
    config = SimpleNamespace(app_secret="corrupt-ciphertext")
    db = _RecordingDB(config)

    def reject_ciphertext(_value: str, _secret: str) -> str:
        raise ValueError("invalid ciphertext")

    monkeypatch.setattr("app.core.security.decrypt_data", reject_ciphertext)
    with pytest.raises(atlassian_api.AtlassianSecretError):
        await atlassian_api.get_atlassian_api_key_for_agent(agent_id, db)

    async def reject_runtime_secret(
        _agent_id: uuid.UUID,
        _db: object | None = None,
    ) -> str | None:
        raise atlassian_api.AtlassianSecretError("invalid ciphertext")

    monkeypatch.setattr(
        atlassian_api,
        "get_atlassian_api_key_for_agent",
        reject_runtime_secret,
    )
    outcome = await agent_tools._execute_resolved_mcp_target_outcome(
        {
            "full_name": "atlassian_rovo_search",
            "raw_name": "search",
            "server_url": atlassian_api.ATLASSIAN_MCP_URL,
            "server_name": "Atlassian Rovo",
            "config": {"api_key": "corrupt-ciphertext"},
            "async_completion": None,
        },
        {},
        agent_id=agent_id,
    )

    assert outcome.status == "failed"
    assert outcome.error_code == "mcp_configuration_invalid"


@pytest.mark.asyncio
async def test_atlassian_assignment_cleanup_preserves_shared_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent_id = uuid.uuid4()
    assignment = SimpleNamespace(agent_id=agent_id, enabled=True)
    shared_tool = SimpleNamespace(id=uuid.uuid4(), category="atlassian")
    deleted: list[object] = []
    db = object()

    async def execute(cleanup_db: object, _statement: object) -> _ListResult:
        assert cleanup_db is db
        return _ListResult([assignment])

    async def delete(cleanup_db: object, value: object) -> None:
        assert cleanup_db is db
        deleted.append(value)

    monkeypatch.setattr(atlassian_api.query_dao, "execute", execute)
    monkeypatch.setattr(atlassian_api.query_dao, "delete", delete)

    removed = await atlassian_api._remove_atlassian_tool_assignments(
        agent_id,
        db,
    )

    assert removed == 1
    assert deleted == [assignment]
    assert shared_tool not in deleted


@pytest.mark.asyncio
@pytest.mark.parametrize("cleanup_fails", [False, True])
async def test_category_config_delete_owns_atlassian_assignment_cleanup(
    monkeypatch: pytest.MonkeyPatch,
    cleanup_fails: bool,
) -> None:
    actor, agent = _actor_and_agent()
    db = _RecordingDB()

    async def require_manager(*_args: object) -> SimpleNamespace:
        return agent

    async def cleanup(
        cleanup_agent_id: uuid.UUID,
        cleanup_db: object,
    ) -> int:
        assert cleanup_agent_id == agent.id
        assert cleanup_db is db
        db.events.append("cleanup")
        if cleanup_fails:
            raise RuntimeError("cleanup failed")
        return 1

    monkeypatch.setattr(tools_api, "_require_agent_tool_manager", require_manager)
    monkeypatch.setattr("app.core.permissions.is_agent_creator", lambda *_args: True)
    monkeypatch.setattr(atlassian_api, "_remove_atlassian_tool_assignments", cleanup)

    if cleanup_fails:
        with pytest.raises(HTTPException) as exc_info:
            await tools_api.delete_category_config(
                agent_id=agent.id,
                category="atlassian",
                current_user=actor,
                db=db,
            )
        assert exc_info.value.status_code == 500
        assert db.events == ["execute", "cleanup", "rollback"]
    else:
        await tools_api.delete_category_config(
            agent_id=agent.id,
            category="atlassian",
            current_user=actor,
            db=db,
        )
        assert db.events == ["execute", "cleanup", "commit"]


@pytest.mark.asyncio
@pytest.mark.parametrize("cleanup_fails", [False, True])
async def test_legacy_atlassian_delete_owns_assignment_cleanup(
    monkeypatch: pytest.MonkeyPatch,
    cleanup_fails: bool,
) -> None:
    actor, agent = _actor_and_agent()
    config = SimpleNamespace(id=uuid.uuid4())
    db = _RecordingDB(config)

    async def check_access(*_args: object) -> tuple[SimpleNamespace, str]:
        return agent, "manage"

    async def cleanup(
        cleanup_agent_id: uuid.UUID,
        cleanup_db: object,
    ) -> int:
        assert cleanup_agent_id == agent.id
        assert cleanup_db is db
        db.events.append("cleanup")
        if cleanup_fails:
            raise RuntimeError("cleanup failed")
        return 1

    monkeypatch.setattr(atlassian_api, "check_agent_access", check_access)
    monkeypatch.setattr(atlassian_api, "is_agent_creator", lambda *_args: True)
    monkeypatch.setattr(atlassian_api, "_remove_atlassian_tool_assignments", cleanup)

    if cleanup_fails:
        with pytest.raises(HTTPException) as exc_info:
            await atlassian_api.delete_atlassian_channel(
                agent_id=agent.id,
                current_user=actor,
                db=db,
            )
        assert exc_info.value.status_code == 500
        assert db.events == ["execute", "delete", "cleanup", "rollback"]
    else:
        await atlassian_api.delete_atlassian_channel(
            agent_id=agent.id,
            current_user=actor,
            db=db,
        )
        assert db.events == ["execute", "delete", "cleanup", "commit"]
