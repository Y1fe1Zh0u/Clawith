"""Atlassian credential, discovery, assignment, and cleanup ownership."""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from typing import TypedDict
from urllib.parse import urlsplit

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import decrypt_data, encrypt_data
from app.dao import query_dao
from app.models.channel_config import ChannelConfig
from app.models.tool import AgentTool, Tool
from app.services.mcp_client import MCPClient

ATLASSIAN_MCP_URL = "https://mcp.atlassian.com/v1/mcp"
ATLASSIAN_SERVER_NAME = "Atlassian Rovo"
ATLASSIAN_TOOL_PREFIX = "atlassian_rovo_"
ATLASSIAN_SECRET_FIELDS = frozenset({"api_key", "atlassian_api_key", "api_secret", "app_secret"})


class AtlassianSecretError(RuntimeError):
    """Stored Atlassian credentials cannot be decrypted safely."""


class AtlassianSyncError(RuntimeError):
    """Atlassian tools could not be discovered for synchronization."""


class AtlassianConfigurationError(RuntimeError):
    """Atlassian configuration could not be persisted atomically."""


class AtlassianNotConfiguredError(RuntimeError):
    """The Agent has no authoritative Atlassian configuration."""


class AtlassianToolDefinition(TypedDict):
    name: str
    description: str
    parameters_schema: dict[str, object]
    icon: str


class AtlassianConfigurationView(TypedDict):
    id: str | None
    agent_id: str
    category: str
    is_configured: bool
    config: dict[str, object]
    global_config: dict[str, object]
    agent_config: dict[str, object]


def is_atlassian_tool_identity(
    *,
    category: object = None,
    name: object = None,
    server_name: object = None,
    server_url: object = None,
) -> bool:
    normalized_name = str(name or "").strip().lower()
    normalized_server_name = str(server_name or "").strip().lower()
    return (
        is_atlassian_category(category)
        or normalized_server_name == ATLASSIAN_SERVER_NAME.lower()
        or is_atlassian_mcp_url(server_url)
        or normalized_name == "atlassian_rovo"
        or normalized_name.startswith(ATLASSIAN_TOOL_PREFIX)
    )


def is_atlassian_category(category: object) -> bool:
    return str(category or "").strip().lower() == "atlassian"


def is_atlassian_runtime_target(
    *,
    name: object = None,
    server_name: object = None,
    server_url: object = None,
) -> bool:
    return is_atlassian_tool_identity(
        name=name,
        server_name=server_name,
        server_url=server_url,
    ) and is_safe_atlassian_runtime_url(server_url)


def _parsed_atlassian_url(server_url: object):
    try:
        parsed = urlsplit(str(server_url or "").strip())
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme.lower() != "https"
        or (parsed.hostname or "").lower() != "mcp.atlassian.com"
        or port not in (None, 443)
        or parsed.path.rstrip("/").lower() != "/v1/mcp"
    ):
        return None
    return parsed


def is_safe_atlassian_runtime_url(server_url: object) -> bool:
    parsed = _parsed_atlassian_url(server_url)
    return bool(
        parsed is not None
        and parsed.username is None
        and parsed.password is None
        and not parsed.query
        and not parsed.fragment
    )


def is_atlassian_mcp_url(server_url: object) -> bool:
    return _parsed_atlassian_url(server_url) is not None


def atlassian_tool_clause() -> ColumnElement[bool]:
    normalized_url = func.lower(func.trim(Tool.mcp_server_url))
    url_clauses = []
    for base in (
        ATLASSIAN_MCP_URL.lower(),
        "https://mcp.atlassian.com:443/v1/mcp",
    ):
        url_clauses.extend(
            (
                normalized_url == base,
                normalized_url == f"{base}/",
                normalized_url.like(f"{base}?%"),
                normalized_url.like(f"{base}#%"),
                normalized_url.like(f"{base}/?%"),
                normalized_url.like(f"{base}/#%"),
            )
        )
    return or_(
        func.lower(func.trim(Tool.category)) == "atlassian",
        func.lower(Tool.mcp_server_name) == ATLASSIAN_SERVER_NAME.lower(),
        *url_clauses,
        func.lower(Tool.name) == "atlassian_rovo",
        func.lower(Tool.name).like(f"{ATLASSIAN_TOOL_PREFIX}%"),
    )


def without_atlassian_secret_fields(config: object) -> dict:
    if not isinstance(config, Mapping):
        return {}
    return {str(key): value for key, value in config.items() if key not in ATLASSIAN_SECRET_FIELDS}


def _normalize_discovered_tools(
    discovered: Sequence[Mapping[str, object]],
) -> list[AtlassianToolDefinition]:
    normalized: list[AtlassianToolDefinition] = []
    for item in discovered:
        raw_name = item.get("name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            continue
        name = raw_name.strip()
        description_value = item.get("description")
        description = description_value[:500] if isinstance(description_value, str) else ""
        schema_value = item.get("inputSchema")
        parameters_schema = (
            dict(schema_value) if isinstance(schema_value, Mapping) else {"type": "object", "properties": {}}
        )
        lowered = name.lower()
        if "jira" in lowered or "issue" in lowered:
            icon = "🔵"
        elif "confluence" in lowered or "page" in lowered:
            icon = "📘"
        elif "compass" in lowered or "component" in lowered:
            icon = "🧭"
        else:
            icon = "🔷"
        normalized.append(
            {
                "name": name,
                "description": description,
                "parameters_schema": parameters_schema,
                "icon": icon,
            }
        )
    return normalized


async def discover_atlassian_tools(api_key: str) -> list[AtlassianToolDefinition]:
    try:
        discovered = await MCPClient(
            ATLASSIAN_MCP_URL,
            api_key=api_key,
        ).list_tools()
    except Exception as exc:
        raise AtlassianSyncError("Could not discover Atlassian tools") from exc
    normalized = _normalize_discovered_tools(discovered)
    if not normalized:
        raise AtlassianSyncError("Atlassian returned no usable tools")
    return normalized


async def upsert_atlassian_shared_tools(
    db: AsyncSession,
    definitions: Sequence[AtlassianToolDefinition],
) -> tuple[list[Tool], int]:
    tools: list[Tool] = []
    created = 0
    for definition in definitions:
        tool_name = f"{ATLASSIAN_TOOL_PREFIX}{definition['name']}"
        result = await query_dao.execute(
            db,
            select(Tool).where(Tool.name == tool_name),
        )
        tool = result.scalar_one_or_none()
        if tool is None:
            tool = Tool(
                name=tool_name,
                display_name=f"Atlassian: {definition['name']}",
                description=definition["description"],
                type="mcp",
                category="atlassian",
                icon=definition["icon"],
                parameters_schema=definition["parameters_schema"],
                mcp_server_url=ATLASSIAN_MCP_URL,
                mcp_server_name=ATLASSIAN_SERVER_NAME,
                mcp_tool_name=definition["name"],
                enabled=True,
                is_default=False,
                config={},
                source="admin",
            )
            query_dao.add(db, tool)
            await query_dao.flush(db)
            created += 1
        else:
            tool.display_name = f"Atlassian: {definition['name']}"
            tool.description = definition["description"]
            tool.type = "mcp"
            tool.category = "atlassian"
            tool.parameters_schema = definition["parameters_schema"]
            tool.icon = definition["icon"]
            tool.mcp_server_url = ATLASSIAN_MCP_URL
            tool.mcp_server_name = ATLASSIAN_SERVER_NAME
            tool.mcp_tool_name = definition["name"]
            tool.enabled = True
            tool.is_default = False
            tool.source = "admin"
            tool.tenant_id = None
            tool.config = without_atlassian_secret_fields(tool.config)
        tools.append(tool)
    return tools, created


async def sync_atlassian_tools_for_agent(
    agent_id: uuid.UUID,
    api_key: str,
    db: AsyncSession,
) -> int:
    definitions = await discover_atlassian_tools(api_key)
    tools, _created = await upsert_atlassian_shared_tools(db, definitions)
    assigned = 0
    for tool in tools:
        result = await query_dao.execute(
            db,
            select(AgentTool).where(
                AgentTool.agent_id == agent_id,
                AgentTool.tool_id == tool.id,
            ),
        )
        assignment = result.scalar_one_or_none()
        if assignment is None:
            assignment = AgentTool(
                agent_id=agent_id,
                tool_id=tool.id,
                enabled=True,
                source="user_installed",
                installed_by_agent_id=agent_id,
                config={},
            )
            query_dao.add(db, assignment)
            assigned += 1
        else:
            assignment.enabled = True
            assignment.config = without_atlassian_secret_fields(assignment.config)
    return assigned


async def remove_atlassian_tool_assignments(
    agent_id: uuid.UUID,
    db: AsyncSession,
) -> int:
    result = await query_dao.execute(
        db,
        select(AgentTool)
        .join(Tool, AgentTool.tool_id == Tool.id)
        .where(
            AgentTool.agent_id == agent_id,
            atlassian_tool_clause(),
        ),
    )
    assignments = list(result.scalars().all())
    for assignment in assignments:
        await query_dao.delete(db, assignment)
    return len(assignments)


async def get_atlassian_configuration(
    agent_id: uuid.UUID,
    db: AsyncSession,
) -> ChannelConfig | None:
    result = await query_dao.execute(
        db,
        select(ChannelConfig).where(
            ChannelConfig.agent_id == agent_id,
            func.lower(func.trim(ChannelConfig.channel_type)) == "atlassian",
        ),
    )
    return result.scalar_one_or_none()


async def configure_atlassian_for_agent(
    agent_id: uuid.UUID,
    api_key: str,
    cloud_id: str,
    db: AsyncSession,
) -> ChannelConfig:
    try:
        encrypted_key = encrypt_data(api_key, get_settings().SECRET_KEY)
    except Exception as exc:
        raise AtlassianSecretError("Atlassian API key encryption failed") from exc

    try:
        config = await get_atlassian_configuration(agent_id, db)
        if config is None:
            config = ChannelConfig(
                agent_id=agent_id,
                channel_type="atlassian",
                app_id="atlassian",
                app_secret=encrypted_key,
                is_configured=True,
                extra_config={"cloud_id": cloud_id},
            )
            query_dao.add(db, config)
        else:
            config.channel_type = "atlassian"
            config.app_id = "atlassian"
            config.app_secret = encrypted_key
            config.is_configured = True
            config.extra_config = {
                **without_atlassian_secret_fields(config.extra_config),
                "cloud_id": cloud_id,
            }
        await query_dao.flush(db)
        await sync_atlassian_tools_for_agent(agent_id, api_key, db)
        await query_dao.commit(db)
    except AtlassianSyncError:
        await db.rollback()
        raise
    except Exception as exc:
        await db.rollback()
        raise AtlassianConfigurationError("Atlassian configuration could not be persisted") from exc
    return config


async def delete_atlassian_for_agent(
    agent_id: uuid.UUID,
    db: AsyncSession,
) -> bool:
    try:
        config = await get_atlassian_configuration(agent_id, db)
        if config is not None:
            await query_dao.delete(db, config)
        await remove_atlassian_tool_assignments(agent_id, db)
        await query_dao.commit(db)
    except Exception as exc:
        await db.rollback()
        raise AtlassianConfigurationError("Atlassian configuration could not be deleted") from exc
    return config is not None


async def test_atlassian_for_agent(
    agent_id: uuid.UUID,
    db: AsyncSession,
) -> list[AtlassianToolDefinition]:
    try:
        api_key = await get_atlassian_api_key_for_agent(agent_id, db)
        if api_key is None:
            raise AtlassianNotConfiguredError("Atlassian is not configured for this Agent")
        return await discover_atlassian_tools(api_key)
    except (
        AtlassianNotConfiguredError,
        AtlassianSecretError,
        AtlassianSyncError,
    ):
        raise
    except Exception as exc:
        raise AtlassianConfigurationError("Atlassian configuration could not be read") from exc


async def get_atlassian_configuration_view(
    agent_id: uuid.UUID,
    db: AsyncSession,
) -> AtlassianConfigurationView:
    config = await get_atlassian_configuration(agent_id, db)
    agent_config = without_atlassian_secret_fields(config.extra_config) if config is not None else {}
    return {
        "id": str(config.id) if config is not None else None,
        "agent_id": str(agent_id),
        "category": "atlassian",
        "is_configured": bool(config is not None and config.is_configured and config.app_secret),
        "config": dict(agent_config),
        "global_config": {},
        "agent_config": agent_config,
    }


async def get_atlassian_api_key_for_agent(
    agent_id: uuid.UUID,
    db: AsyncSession | None = None,
) -> str | None:
    async def read(session: AsyncSession) -> str | None:
        result = await query_dao.execute(
            session,
            select(ChannelConfig).where(
                ChannelConfig.agent_id == agent_id,
                ChannelConfig.channel_type == "atlassian",
                ChannelConfig.is_configured.is_(True),
            ),
        )
        config = result.scalar_one_or_none()
        if config is None or not config.app_secret:
            return None
        try:
            return decrypt_data(config.app_secret, get_settings().SECRET_KEY)
        except Exception as exc:
            raise AtlassianSecretError("Stored Atlassian API key cannot be decrypted") from exc

    if db is not None:
        return await read(db)
    async with query_dao.session() as session:
        return await read(session)
