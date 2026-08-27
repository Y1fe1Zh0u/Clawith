import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api import atlassian as atlassian_api
from app.api import tools as tools_api
from app.models.tool import AgentTool, Tool
from app.services import agent_tools, resource_discovery
from app.services import atlassian_tool_service as atlassian_service
from app.services.mcp_client import MCPClient


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
    def __init__(
        self,
        existing: object | None = None,
        *,
        fail_commit: bool = False,
    ) -> None:
        self.existing = existing
        self.fail_commit = fail_commit
        self.events: list[str] = []

    async def execute(self, _statement: object) -> _ScalarResult:
        self.events.append("execute")
        return _ScalarResult(self.existing)

    def add(self, _value: object) -> None:
        self.events.append("add")

    async def flush(self) -> None:
        self.events.append("flush")

    async def delete(self, _value: object) -> None:
        self.events.append("delete")

    async def commit(self) -> None:
        self.events.append("commit")
        if self.fail_commit:
            raise RuntimeError("commit failed")

    async def rollback(self) -> None:
        self.events.append("rollback")


class _SequenceDB(_RecordingDB):
    def __init__(self, results: list[object]) -> None:
        super().__init__()
        self.results = iter(results)

    async def execute(self, _statement: object) -> object:
        self.events.append("execute")
        return next(self.results)


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
    monkeypatch.setattr(atlassian_service, "encrypt_data", lambda _value, _secret: "encrypted")
    monkeypatch.setattr(atlassian_service, "sync_atlassian_tools_for_agent", sync_tools)

    result = await tools_api.update_category_config(
        agent_id=agent.id,
        category="atlassian",
        data=tools_api.CategoryConfigUpdate(config={"api_key": " secret "}),
        current_user=actor,
        db=db,
    )

    assert result == {"ok": True}
    assert db.events == ["execute", "flush", "sync", "commit"]
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
        raise atlassian_service.AtlassianSyncError("provider unavailable")

    monkeypatch.setattr(tools_api, "_require_agent_tool_manager", require_manager)
    monkeypatch.setattr("app.core.permissions.is_agent_creator", lambda *_args: True)
    monkeypatch.setattr(atlassian_service, "encrypt_data", lambda _value, _secret: "encrypted")
    monkeypatch.setattr(atlassian_service, "sync_atlassian_tools_for_agent", fail_sync)

    with pytest.raises(HTTPException) as exc_info:
        await tools_api.update_category_config(
            agent_id=agent.id,
            category="atlassian",
            data=tools_api.CategoryConfigUpdate(config={"api_key": "secret"}),
            current_user=actor,
            db=db,
        )

    assert exc_info.value.status_code == 502
    assert db.events == ["execute", "flush", "sync", "rollback"]
    assert "commit" not in db.events


@pytest.mark.asyncio
async def test_atlassian_category_config_reports_commit_failure_after_rollback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor, agent = _actor_and_agent()
    existing = SimpleNamespace(
        app_secret=None,
        extra_config={},
        is_configured=False,
    )
    db = _RecordingDB(existing, fail_commit=True)

    async def require_manager(*_args: object) -> SimpleNamespace:
        return agent

    async def sync_tools(*_args: object) -> None:
        db.events.append("sync")

    monkeypatch.setattr(tools_api, "_require_agent_tool_manager", require_manager)
    monkeypatch.setattr("app.core.permissions.is_agent_creator", lambda *_args: True)
    monkeypatch.setattr(atlassian_service, "encrypt_data", lambda *_args: "encrypted")
    monkeypatch.setattr(atlassian_service, "sync_atlassian_tools_for_agent", sync_tools)

    with pytest.raises(HTTPException) as exc_info:
        await tools_api.update_category_config(
            agent_id=agent.id,
            category="atlassian",
            data=tools_api.CategoryConfigUpdate(config={"api_key": "secret"}),
            current_user=actor,
            db=db,
        )

    assert exc_info.value.status_code == 500
    assert db.events == ["execute", "flush", "sync", "commit", "rollback"]


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
    monkeypatch.setattr(atlassian_service, "encrypt_data", lambda _value, _secret: "ciphertext-value")
    monkeypatch.setattr(atlassian_service, "sync_atlassian_tools_for_agent", sync_tools)

    result = await atlassian_api.configure_atlassian_channel(
        agent_id=agent.id,
        data={"api_key": "secret", "cloud_id": "site"},
        current_user=actor,
        db=db,
    )

    assert result["is_configured"] is True
    assert db.events == ["execute", "flush", "sync", "commit"]
    assert existing.app_secret == "ciphertext-value"


@pytest.mark.asyncio
async def test_atlassian_sync_persists_no_tool_or_assignment_secret(
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

    monkeypatch.setattr(atlassian_service, "MCPClient", FakeMCPClient)
    monkeypatch.setattr(atlassian_service.query_dao, "execute", execute)
    monkeypatch.setattr(atlassian_service.query_dao, "add", add)
    monkeypatch.setattr(atlassian_service.query_dao, "flush", flush)
    monkeypatch.setattr(atlassian_service.query_dao, "commit", commit)

    await atlassian_service.sync_atlassian_tools_for_agent(
        agent_id,
        "plaintext-secret",
        sync_db,
    )

    assignment = next(value for value in added if isinstance(value, AgentTool))
    assert assignment.config == {}
    assert "plaintext-secret" not in assignment.config.values()
    shared_tool = next(value for value in added if isinstance(value, Tool))
    assert shared_tool.config == {}
    assert commits == []


def test_atlassian_identity_owner_covers_all_persisted_variants() -> None:
    assert atlassian_service.is_atlassian_tool_identity(category="atlassian")
    assert atlassian_service.is_atlassian_tool_identity(server_name="Atlassian Rovo")
    assert atlassian_service.is_atlassian_tool_identity(server_url=f"{atlassian_service.ATLASSIAN_MCP_URL}/")
    assert atlassian_service.is_atlassian_mcp_url(f"{atlassian_service.ATLASSIAN_MCP_URL}?apiKey=legacy")
    assert atlassian_service.is_atlassian_mcp_url("https://mcp.atlassian.com:443/v1/mcp#legacy")
    assert atlassian_service.is_safe_atlassian_runtime_url(atlassian_service.ATLASSIAN_MCP_URL)
    assert not atlassian_service.is_safe_atlassian_runtime_url(f"{atlassian_service.ATLASSIAN_MCP_URL}?apiKey=legacy")
    assert not atlassian_service.is_atlassian_mcp_url("https://mcp.atlassian.com.evil.example/v1/mcp")
    assert atlassian_service.is_atlassian_tool_identity(name="atlassian_rovo_search")
    assert not atlassian_service.is_atlassian_tool_identity(
        category="mcp",
        name="search",
        server_name="Other MCP",
        server_url="https://example.com/mcp",
    )

    compiled = str(atlassian_service.atlassian_tool_clause())
    for field in ("category", "mcp_server_name", "mcp_server_url", "name"):
        assert field in compiled
    params = atlassian_service.atlassian_tool_clause().compile().params
    assert any("?%" in str(value) for value in params.values())
    assert any(":443/v1/mcp" in str(value) for value in params.values())


@pytest.mark.asyncio
async def test_existing_atlassian_tool_is_repaired_to_canonical_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = SimpleNamespace(
        id=uuid.uuid4(),
        name="atlassian_rovo_search",
        display_name="Wrong",
        description="Wrong",
        type="mcp",
        category="mcp",
        icon="wrong",
        parameters_schema={},
        mcp_server_url="https://attacker.example/mcp",
        mcp_server_name="Wrong",
        mcp_tool_name="wrong",
        enabled=False,
        is_default=True,
        source="agent",
        tenant_id=uuid.uuid4(),
        config={"api_key": "legacy"},
    )

    async def execute(_db: object, _statement: object) -> _ScalarResult:
        return _ScalarResult(tool)

    monkeypatch.setattr(atlassian_service.query_dao, "execute", execute)
    tools, created = await atlassian_service.upsert_atlassian_shared_tools(
        object(),
        [
            {
                "name": "search",
                "description": "Search",
                "parameters_schema": {"type": "object"},
                "icon": "search",
            }
        ],
    )

    assert tools == [tool]
    assert created == 0
    assert tool.category == "atlassian"
    assert tool.mcp_server_url == atlassian_service.ATLASSIAN_MCP_URL
    assert tool.mcp_server_name == atlassian_service.ATLASSIAN_SERVER_NAME
    assert tool.mcp_tool_name == "search"
    assert tool.source == "admin"
    assert tool.tenant_id is None
    assert tool.config == {}


@pytest.mark.asyncio
async def test_agent_tools_with_config_never_returns_atlassian_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor, agent = _actor_and_agent()
    agent.tenant_id = uuid.uuid4()
    agent.is_system = False
    tool_id = uuid.uuid4()
    tool = SimpleNamespace(
        id=tool_id,
        name="atlassian_rovo_search",
        display_name="Atlassian: search",
        description="Search Atlassian",
        type="mcp",
        category="atlassian",
        icon="search",
        enabled=True,
        is_default=False,
        mcp_server_name="Atlassian Rovo",
        mcp_server_url=atlassian_service.ATLASSIAN_MCP_URL,
        config_schema={},
        config={"api_key": "legacy-global-secret"},
        source="admin",
        tenant_id=agent.tenant_id,
    )
    assignment = SimpleNamespace(
        id=uuid.uuid4(),
        enabled=True,
        config={
            "atlassian_api_key": "legacy-agent-secret",
            "cloud_id": "site-agent",
        },
    )

    class WithConfigDB:
        async def execute(self, _statement: object) -> _ListResult:
            return _ListResult([tool])

    async def require_manager(*_args: object) -> SimpleNamespace:
        return agent

    async def load_assignments(
        _db: object,
        loaded_agent_id: uuid.UUID,
    ) -> dict[str, SimpleNamespace]:
        assert loaded_agent_id == agent.id
        return {str(tool_id): assignment}

    async def company_config(
        _db: object,
        loaded_tool: object,
        tenant_id: uuid.UUID,
    ) -> dict[str, object]:
        assert loaded_tool is tool
        assert tenant_id == agent.tenant_id
        return {
            "api_key": "legacy-company-secret",
            "cloud_id": "site-global",
        }

    async def no_feishu(_agent_id: uuid.UUID) -> bool:
        return False

    monkeypatch.setattr(tools_api, "_require_agent_tool_manager", require_manager)
    monkeypatch.setattr(tools_api, "_load_agent_tool_assignments", load_assignments)
    monkeypatch.setattr(tools_api, "get_tool_company_config", company_config)
    monkeypatch.setattr("app.services.agent_tools._agent_has_feishu", no_feishu)

    result = await tools_api.get_agent_tools_with_config(
        agent_id=agent.id,
        current_user=actor,
        db=WithConfigDB(),
    )

    assert len(result) == 1
    assert result[0]["global_config"] == {"cloud_id": "site-global"}
    assert result[0]["agent_config"] == {"cloud_id": "site-agent"}
    assert "legacy" not in repr(result)


@pytest.mark.asyncio
async def test_category_config_returns_only_non_secret_atlassian_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor, agent = _actor_and_agent()
    config = SimpleNamespace(
        id=uuid.uuid4(),
        app_secret="encrypted-authoritative-secret",
        extra_config={
            "api_key": "legacy-duplicate",
            "api_secret": "legacy-alias",
            "cloud_id": "site",
        },
        is_configured=True,
    )
    db = _RecordingDB(config)

    async def require_manager(*_args: object) -> SimpleNamespace:
        return agent

    monkeypatch.setattr(tools_api, "_require_agent_tool_manager", require_manager)
    result = await tools_api.get_category_config(
        agent_id=agent.id,
        category="AtLaSsIaN",
        current_user=actor,
        db=db,
    )

    assert result["is_configured"] is True
    assert result["config"] == {"cloud_id": "site"}
    assert result["agent_config"] == {"cloud_id": "site"}
    assert "secret" not in repr(result)
    assert "api_key" not in repr(result)


@pytest.mark.asyncio
async def test_generic_tool_config_read_redacts_legacy_atlassian_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor, agent = _actor_and_agent()
    agent.tenant_id = uuid.uuid4()
    tool_id = uuid.uuid4()
    tool = SimpleNamespace(
        id=tool_id,
        category="mcp",
        name="legacy_import",
        mcp_server_name="Different display name",
        mcp_server_url=atlassian_service.ATLASSIAN_MCP_URL,
        config_schema={},
    )
    assignment = SimpleNamespace(config={"atlassian_api_key": "legacy-agent", "cloud_id": "agent-site"})
    db = _SequenceDB([_ScalarResult(tool), _ScalarResult(assignment)])

    async def require_manager(*_args: object) -> SimpleNamespace:
        return agent

    async def load_assignments(*_args: object) -> dict[str, object]:
        return {}

    async def company_config(*_args: object) -> dict[str, object]:
        return {"api_key": "legacy-global", "cloud_id": "global-site"}

    monkeypatch.setattr(tools_api, "_require_agent_tool_manager", require_manager)
    monkeypatch.setattr(tools_api, "_load_agent_tool_assignments", load_assignments)
    monkeypatch.setattr(
        tools_api,
        "_tool_record_visible_to_agent",
        lambda *_args: True,
    )
    monkeypatch.setattr(tools_api, "get_tool_company_config", company_config)
    monkeypatch.setattr(
        tools_api,
        "_decrypt_sensitive_fields",
        lambda config, _schema: dict(config),
    )

    result = await tools_api.get_agent_tool_config(
        agent_id=agent.id,
        tool_id=tool_id,
        current_user=actor,
        db=db,
    )

    assert result["global_config"] == {"cloud_id": "global-site"}
    assert result["agent_config"] == {"cloud_id": "agent-site"}
    assert "legacy" not in repr(result)


@pytest.mark.asyncio
async def test_generic_agent_tool_config_rejects_atlassian_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor, agent = _actor_and_agent()
    agent.tenant_id = uuid.uuid4()
    tool = SimpleNamespace(
        id=uuid.uuid4(),
        category="atlassian",
        name="atlassian_rovo_search",
        mcp_server_name="Atlassian Rovo",
        mcp_server_url=atlassian_service.ATLASSIAN_MCP_URL,
        config_schema={},
    )
    db = _RecordingDB(tool)

    async def require_manager(*_args: object) -> SimpleNamespace:
        return agent

    async def load_assignments(
        _db: object,
        _agent_id: uuid.UUID,
    ) -> dict[str, object]:
        return {}

    monkeypatch.setattr(tools_api, "_require_agent_tool_manager", require_manager)
    monkeypatch.setattr(tools_api, "_load_agent_tool_assignments", load_assignments)
    monkeypatch.setattr(
        tools_api,
        "_tool_record_visible_to_agent",
        lambda *_args: True,
    )

    with pytest.raises(HTTPException) as exc_info:
        await tools_api.update_agent_tool_config(
            agent_id=agent.id,
            tool_id=tool.id,
            data=tools_api.AgentToolConfigUpdate(
                config={"api_key": "must-not-persist"},
            ),
            current_user=actor,
            db=db,
        )

    assert exc_info.value.status_code == 422
    assert db.events == ["execute"]


@pytest.mark.asyncio
async def test_mcp_server_update_rejects_atlassian_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor = SimpleNamespace(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        role="platform_admin",
    )
    tool = SimpleNamespace(
        category="atlassian",
        name="atlassian_rovo_search",
        mcp_server_name="Atlassian Rovo",
        mcp_server_url=atlassian_service.ATLASSIAN_MCP_URL,
    )

    class MCPServerDB:
        def __init__(self) -> None:
            self.commits = 0

        async def execute(self, _statement: object) -> _ListResult:
            return _ListResult([tool])

        async def commit(self) -> None:
            self.commits += 1

    db = MCPServerDB()
    monkeypatch.setattr(tools_api, "_require_tool_manager", lambda *_args: None)

    with pytest.raises(HTTPException) as exc_info:
        await tools_api.update_mcp_server(
            data=tools_api.MCPServerUpdate(
                server_name="Atlassian Rovo",
                server_url=atlassian_service.ATLASSIAN_MCP_URL,
                api_key="must-not-persist",
            ),
            current_user=actor,
            db=db,
        )

    assert exc_info.value.status_code == 422
    assert db.commits == 0


@pytest.mark.asyncio
async def test_mcp_server_update_rejects_proposed_atlassian_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor = SimpleNamespace(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        role="platform_admin",
    )
    tool = SimpleNamespace(
        category="mcp",
        name="ordinary_search",
        mcp_server_name="Ordinary MCP",
        mcp_server_url="https://ordinary.example/mcp",
    )

    class MCPServerDB:
        def __init__(self) -> None:
            self.commits = 0

        async def execute(self, _statement: object) -> _ListResult:
            return _ListResult([tool])

        async def commit(self) -> None:
            self.commits += 1

    db = MCPServerDB()
    monkeypatch.setattr(tools_api, "_require_tool_manager", lambda *_args: None)

    with pytest.raises(HTTPException) as exc_info:
        await tools_api.update_mcp_server(
            data=tools_api.MCPServerUpdate(
                server_name="Ordinary MCP",
                server_url=(f"{atlassian_service.ATLASSIAN_MCP_URL}?apiKey=legacy"),
                api_key="must-not-persist",
            ),
            current_user=actor,
            db=db,
        )

    assert exc_info.value.status_code == 422
    assert tool.mcp_server_url == "https://ordinary.example/mcp"
    assert db.commits == 0


@pytest.mark.asyncio
async def test_org_admin_cannot_retarget_shared_atlassian_tool() -> None:
    actor = SimpleNamespace(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        role="org_admin",
    )
    tool = SimpleNamespace(
        id=uuid.uuid4(),
        category="atlassian",
        name="atlassian_rovo_search",
        mcp_server_name="Atlassian Rovo",
        mcp_server_url=atlassian_service.ATLASSIAN_MCP_URL,
        tenant_id=None,
    )
    db = _RecordingDB(tool)

    with pytest.raises(HTTPException) as exc_info:
        await tools_api.update_tool(
            tool_id=tool.id,
            data=tools_api.ToolUpdate(
                mcp_server_url="https://attacker.example/mcp",
            ),
            current_user=actor,
            db=db,
        )

    assert exc_info.value.status_code == 422
    assert db.events == ["execute"]


@pytest.mark.asyncio
async def test_atlassian_display_name_with_attacker_url_never_reads_owned_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def forbidden_secret_read(*_args: object) -> None:
        raise AssertionError("authoritative Atlassian secret was read")

    async def forbidden_call(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("attacker route was dispatched")

    monkeypatch.setattr(
        atlassian_service,
        "get_atlassian_api_key_for_agent",
        forbidden_secret_read,
    )
    monkeypatch.setattr(MCPClient, "call_tool_result", forbidden_call)

    outcome = await agent_tools._execute_resolved_mcp_target_outcome(
        {
            "full_name": "attacker_search",
            "raw_name": "search",
            "server_url": "https://attacker.example/mcp",
            "server_name": "Atlassian Rovo",
            "config": {},
            "async_completion": None,
        },
        {"query": "x"},
        agent_id=uuid.uuid4(),
    )

    assert outcome.status == "failed"
    assert outcome.error_code == "mcp_configuration_invalid"


@pytest.mark.asyncio
async def test_direct_atlassian_import_cannot_create_a_second_secret_owner() -> None:
    outcome = await resource_discovery.import_mcp_direct_outcome(
        atlassian_service.ATLASSIAN_MCP_URL,
        uuid.uuid4(),
        server_name="Atlassian Rovo",
        api_key="must-not-persist",
    )

    assert outcome.status == "failed"
    assert outcome.error_code == "mcp_configuration_invalid"
    assert "category settings" in (outcome.result_summary or "")


@pytest.mark.asyncio
async def test_direct_import_rejects_existing_atlassian_record_before_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = SimpleNamespace(
        id=uuid.uuid4(),
        category="mcp",
        name="legacy_direct",
        mcp_server_name="Legacy",
        mcp_server_url=(f"{atlassian_service.ATLASSIAN_MCP_URL}?apiKey=legacy"),
    )

    class DB:
        def __init__(self) -> None:
            self.commits = 0

        async def execute(self, _statement: object) -> _ScalarResult:
            return _ScalarResult(existing)

        async def commit(self) -> None:
            self.commits += 1

    class Context:
        def __init__(self, db: DB) -> None:
            self.db = db

        async def __aenter__(self) -> DB:
            return self.db

        async def __aexit__(self, *_args: object) -> None:
            return None

    db = DB()

    async def no_tools(_client: MCPClient) -> list[dict[str, object]]:
        return []

    monkeypatch.setattr(MCPClient, "list_tools", no_tools)
    monkeypatch.setattr(resource_discovery, "async_session", lambda: Context(db))

    outcome = await resource_discovery.import_mcp_direct_outcome(
        "https://ordinary.example/mcp",
        uuid.uuid4(),
        server_name="Legacy",
        api_key="must-not-persist",
    )

    assert outcome.status == "failed"
    assert outcome.error_code == "mcp_configuration_invalid"
    assert existing.mcp_server_url.endswith("?apiKey=legacy")
    assert db.commits == 0


@pytest.mark.asyncio
async def test_smithery_import_rejects_existing_atlassian_record_before_config_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tenant_id = uuid.uuid4()
    existing = SimpleNamespace(
        id=uuid.uuid4(),
        category="mcp",
        name="mcp_legacy",
        mcp_server_name="Legacy",
        mcp_server_url="https://mcp.atlassian.com:443/v1/mcp#legacy",
    )

    class DB:
        def __init__(self, results: list[object]) -> None:
            self.results = iter(results)
            self.commits = 0

        async def execute(self, _statement: object) -> object:
            return next(self.results)

        async def commit(self) -> None:
            self.commits += 1

    class Context:
        def __init__(self, db: DB) -> None:
            self.db = db

        async def __aenter__(self) -> DB:
            return self.db

        async def __aexit__(self, *_args: object) -> None:
            return None

    config_db = DB(
        [
            _ScalarResult(tenant_id),
            _ScalarResult(None),
            _ScalarResult(None),
        ]
    )
    existing_db = DB([_ListResult([existing])])
    contexts = iter((Context(config_db), Context(existing_db)))
    monkeypatch.setattr(resource_discovery, "async_session", lambda: next(contexts))

    outcome = await resource_discovery.import_mcp_from_smithery_outcome(
        "legacy",
        uuid.uuid4(),
        config={"smithery_api_key": "smithery-key"},
    )

    assert outcome.status == "failed"
    assert outcome.error_code == "mcp_configuration_invalid"
    assert existing.mcp_server_url.endswith("#legacy")
    assert existing_db.commits == 0


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
    with pytest.raises(atlassian_service.AtlassianSecretError):
        await atlassian_service.get_atlassian_api_key_for_agent(agent_id, db)

    async def reject_runtime_secret(
        _agent_id: uuid.UUID,
        _db: object | None = None,
    ) -> str | None:
        raise atlassian_service.AtlassianSecretError("invalid ciphertext")

    monkeypatch.setattr(
        atlassian_service,
        "get_atlassian_api_key_for_agent",
        reject_runtime_secret,
    )
    outcome = await agent_tools._execute_resolved_mcp_target_outcome(
        {
            "full_name": "atlassian_rovo_search",
            "raw_name": "search",
            "server_url": atlassian_service.ATLASSIAN_MCP_URL,
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

    monkeypatch.setattr(atlassian_service.query_dao, "execute", execute)
    monkeypatch.setattr(atlassian_service.query_dao, "delete", delete)

    removed = await atlassian_service.remove_atlassian_tool_assignments(
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

    async def delete_command(
        cleanup_agent_id: uuid.UUID,
        cleanup_db: object,
    ) -> bool:
        assert cleanup_agent_id == agent.id
        assert cleanup_db is db
        db.events.append("service")
        if cleanup_fails:
            raise atlassian_service.AtlassianConfigurationError("cleanup failed")
        return False

    monkeypatch.setattr(tools_api, "_require_agent_tool_manager", require_manager)
    monkeypatch.setattr("app.core.permissions.is_agent_creator", lambda *_args: True)
    monkeypatch.setattr(atlassian_service, "delete_atlassian_for_agent", delete_command)

    if cleanup_fails:
        with pytest.raises(HTTPException) as exc_info:
            await tools_api.delete_category_config(
                agent_id=agent.id,
                category="atlassian",
                current_user=actor,
                db=db,
            )
        assert exc_info.value.status_code == 500
        assert db.events == ["service"]
    else:
        await tools_api.delete_category_config(
            agent_id=agent.id,
            category="atlassian",
            current_user=actor,
            db=db,
        )
        assert db.events == ["service"]


@pytest.mark.asyncio
@pytest.mark.parametrize("cleanup_fails", [False, True])
async def test_legacy_atlassian_delete_owns_assignment_cleanup(
    monkeypatch: pytest.MonkeyPatch,
    cleanup_fails: bool,
) -> None:
    actor, agent = _actor_and_agent()
    db = _RecordingDB()

    async def check_access(*_args: object) -> tuple[SimpleNamespace, str]:
        return agent, "manage"

    async def delete_command(
        cleanup_agent_id: uuid.UUID,
        cleanup_db: object,
    ) -> bool:
        assert cleanup_agent_id == agent.id
        assert cleanup_db is db
        db.events.append("service")
        if cleanup_fails:
            raise atlassian_service.AtlassianConfigurationError("cleanup failed")
        return True

    monkeypatch.setattr(atlassian_api, "check_agent_access", check_access)
    monkeypatch.setattr(atlassian_api, "is_agent_creator", lambda *_args: True)
    monkeypatch.setattr(atlassian_api, "delete_atlassian_for_agent", delete_command)

    if cleanup_fails:
        with pytest.raises(HTTPException) as exc_info:
            await atlassian_api.delete_atlassian_channel(
                agent_id=agent.id,
                current_user=actor,
                db=db,
            )
        assert exc_info.value.status_code == 500
        assert db.events == ["service"]
    else:
        await atlassian_api.delete_atlassian_channel(
            agent_id=agent.id,
            current_user=actor,
            db=db,
        )
        assert db.events == ["service"]
