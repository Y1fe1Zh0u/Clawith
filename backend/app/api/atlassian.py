"""Atlassian Rovo MCP Channel API routes.

Provides per-agent Atlassian integration configuration.
Unlike Slack/Discord (messaging channels), Atlassian is a tool-access channel:
the agent uses Jira, Confluence, and Compass via the Atlassian Rovo MCP server.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import check_agent_access, is_agent_creator
from app.core.security import get_current_user
from app.dao import query_dao
from app.database import get_db
from app.models.channel_config import ChannelConfig
from app.models.user import User

router = APIRouter(tags=["atlassian"])

ATLASSIAN_MCP_URL = "https://mcp.atlassian.com/v1/mcp"


class AtlassianSecretError(RuntimeError):
    """Stored Atlassian credentials cannot be decrypted safely."""


class AtlassianSyncError(RuntimeError):
    """Atlassian tools could not be discovered for assignment."""


# ─── Config CRUD ────────────────────────────────────────

@router.post("/agents/{agent_id}/atlassian-channel", status_code=201)
async def configure_atlassian_channel(
    agent_id: uuid.UUID,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Configure Atlassian Rovo MCP for an agent.

    Required field: api_key (Bearer token starting with ATSTT, or Basic base64(email:token)).
    Optional: cloud_id (Atlassian cloud site ID for multi-site setups).
    """
    agent, _ = await check_agent_access(db, current_user, agent_id)
    if not is_agent_creator(current_user, agent):
        raise HTTPException(status_code=403, detail="Only creator can configure channel")

    api_key = (data.get("api_key") or "").strip()
    if not api_key:
        raise HTTPException(status_code=422, detail="api_key is required")

    cloud_id = (data.get("cloud_id") or "").strip()

    from app.config import get_settings
    from app.core.security import encrypt_data
    encrypted_key = encrypt_data(api_key, get_settings().SECRET_KEY)

    result = await query_dao.execute(db, 
        select(ChannelConfig).where(
            ChannelConfig.agent_id == agent_id,
            ChannelConfig.channel_type == "atlassian",
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.app_secret = encrypted_key
        existing.is_configured = True
        existing.extra_config = {**(existing.extra_config or {}), "cloud_id": cloud_id}
        config = existing
    else:
        config = ChannelConfig(
            agent_id=agent_id,
            channel_type="atlassian",
            app_id="atlassian",
            app_secret=encrypted_key,
            is_configured=True,
            extra_config={"cloud_id": cloud_id},
        )
        query_dao.add(db, config)

    try:
        await _sync_atlassian_tools_for_agent(agent_id, api_key, db)
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=502,
            detail="Atlassian tool synchronization failed",
        ) from exc

    await query_dao.commit(db)
    if not existing:
        await query_dao.refresh(db, config)
    return _serialize(config)


@router.get("/agents/{agent_id}/atlassian-channel")
async def get_atlassian_channel(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await check_agent_access(db, current_user, agent_id)
    result = await query_dao.execute(db, 
        select(ChannelConfig).where(
            ChannelConfig.agent_id == agent_id,
            ChannelConfig.channel_type == "atlassian",
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Atlassian not configured")
    return _serialize(config)


@router.delete("/agents/{agent_id}/atlassian-channel", status_code=204)
async def delete_atlassian_channel(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent, _ = await check_agent_access(db, current_user, agent_id)
    if not is_agent_creator(current_user, agent):
        raise HTTPException(status_code=403, detail="Only creator can remove channel")
    result = await query_dao.execute(db, 
        select(ChannelConfig).where(
            ChannelConfig.agent_id == agent_id,
            ChannelConfig.channel_type == "atlassian",
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Atlassian not configured")
    try:
        await query_dao.delete(db, config)
        await _remove_atlassian_tool_assignments(agent_id, db)
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Atlassian configuration cleanup failed",
        ) from exc
    await query_dao.commit(db)


@router.post("/agents/{agent_id}/atlassian-channel/test")
async def test_atlassian_channel(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Test connectivity to Atlassian Rovo MCP and list available tools."""
    await check_agent_access(db, current_user, agent_id)
    result = await query_dao.execute(db, 
        select(ChannelConfig).where(
            ChannelConfig.agent_id == agent_id,
            ChannelConfig.channel_type == "atlassian",
        )
    )
    config = result.scalar_one_or_none()
    if not config or not config.app_secret:
        raise HTTPException(status_code=400, detail="Atlassian not configured")

    try:
        api_key = await get_atlassian_api_key_for_agent(agent_id, db)
    except AtlassianSecretError as exc:
        raise HTTPException(
            status_code=500,
            detail="Stored Atlassian API key is invalid",
        ) from exc
    if api_key is None:
        raise HTTPException(status_code=400, detail="Atlassian not configured")

    from app.services.mcp_client import MCPClient
    try:
        client = MCPClient(ATLASSIAN_MCP_URL, api_key=api_key)
        tools = await client.list_tools()
        return {
            "ok": True,
            "tool_count": len(tools),
            "tools": [{"name": t["name"], "description": t.get("description", "")[:100]} for t in tools[:10]],
            "message": f"✅ Connected to Atlassian Rovo MCP — {len(tools)} tools available",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}


# ─── Internal helper ────────────────────────────────────

def _serialize(config: ChannelConfig) -> dict:
    return {
        "id": str(config.id),
        "agent_id": str(config.agent_id),
        "channel_type": config.channel_type,
        "is_configured": config.is_configured,
        "is_connected": config.is_connected,
        "cloud_id": (config.extra_config or {}).get("cloud_id", ""),
        "extra_config": config.extra_config or {},
        "created_at": config.created_at.isoformat() if config.created_at else None,
    }


# ─── Utility for internal use ──────────────────────────

async def _sync_atlassian_tools_for_agent(
    agent_id: uuid.UUID,
    api_key: str,
    db: AsyncSession,
) -> None:
    """Connect to Atlassian Rovo MCP and ensure all tools are seeded + assigned to this agent.

    Discovers tools from the MCP server, creates Tool records if needed,
    and creates AgentTool assignments for this specific agent.
    """
    from sqlalchemy import select as sa_select

    from app.config import get_settings
    from app.core.security import encrypt_data
    from app.models.tool import AgentTool, Tool
    from app.services.mcp_client import MCPClient

    logger.info(f"[AtlassianChannel] Syncing tools for agent {agent_id} ...")
    try:
        client = MCPClient(ATLASSIAN_MCP_URL, api_key=api_key)
        tools_discovered = await client.list_tools()
    except Exception as e:
        logger.error(f"[AtlassianChannel] Could not list tools: {e}")
        raise AtlassianSyncError("Could not discover Atlassian tools") from e

    if not tools_discovered:
        logger.warning("[AtlassianChannel] No tools returned from Atlassian MCP")
        raise AtlassianSyncError("Atlassian returned no tools")

    try:
        encrypted_api_key = encrypt_data(api_key, get_settings().SECRET_KEY)
    except Exception as exc:
        raise AtlassianSyncError("Could not encrypt Atlassian API key") from exc

    logger.info(f"[AtlassianChannel] Found {len(tools_discovered)} tools, assigning to agent {agent_id}")

    assigned = 0
    for mcp_tool in tools_discovered:
        raw_name = mcp_tool.get("name", "")
        if not raw_name:
            continue

        tool_name = f"atlassian_rovo_{raw_name}"
        tool_desc = mcp_tool.get("description", "")[:500]
        tool_schema = mcp_tool.get("inputSchema", {"type": "object", "properties": {}})

        if "jira" in raw_name.lower() or "issue" in raw_name.lower():
            icon = "🔵"
        elif "confluence" in raw_name.lower() or "page" in raw_name.lower():
            icon = "📘"
        elif "compass" in raw_name.lower() or "component" in raw_name.lower():
            icon = "🧭"
        else:
            icon = "🔷"

        tool_r = await query_dao.execute(db, sa_select(Tool).where(Tool.name == tool_name))
        tool = tool_r.scalar_one_or_none()
        if not tool:
            tool = Tool(
                name=tool_name,
                display_name=f"Atlassian: {raw_name}",
                description=tool_desc,
                type="mcp",
                category="atlassian",
                icon=icon,
                parameters_schema=tool_schema,
                mcp_server_url=ATLASSIAN_MCP_URL,
                mcp_server_name="Atlassian Rovo",
                mcp_tool_name=raw_name,
                enabled=True,
                is_default=False,
                source="admin",
            )
            query_dao.add(db, tool)
            await query_dao.flush(db)
        else:
            tool.description = tool_desc
            tool.parameters_schema = tool_schema

        at_r = await query_dao.execute(
            db,
            sa_select(AgentTool).where(
                AgentTool.agent_id == agent_id,
                AgentTool.tool_id == tool.id,
            )
        )
        at = at_r.scalar_one_or_none()
        if at:
            at.enabled = True
            at.config = {"api_key": encrypted_api_key}
        else:
            query_dao.add(
                db,
                AgentTool(
                    agent_id=agent_id,
                    tool_id=tool.id,
                    enabled=True,
                    source="user_installed",
                    installed_by_agent_id=agent_id,
                    config={"api_key": encrypted_api_key},
                ),
            )
            assigned += 1

    logger.info(f"[AtlassianChannel] {assigned} new tool assignments for agent {agent_id}")


async def _remove_atlassian_tool_assignments(
    agent_id: uuid.UUID,
    db: AsyncSession,
) -> int:
    """Remove one Agent's Atlassian assignments without deleting shared Tools."""
    from app.models.tool import AgentTool, Tool

    result = await query_dao.execute(
        db,
        select(AgentTool)
        .join(Tool, AgentTool.tool_id == Tool.id)
        .where(
            AgentTool.agent_id == agent_id,
            Tool.category == "atlassian",
        ),
    )
    assignments = list(result.scalars().all())
    for assignment in assignments:
        await query_dao.delete(db, assignment)
    return len(assignments)


async def get_atlassian_api_key_for_agent(agent_id: uuid.UUID, db=None) -> str | None:
    """Return the configured Atlassian API key for the given agent, or None."""

    async def _fetch(session):
        from app.config import get_settings
        from app.core.security import decrypt_data
        result = await query_dao.execute(session, 
            select(ChannelConfig).where(
                ChannelConfig.agent_id == agent_id,
                ChannelConfig.channel_type == "atlassian",
                ChannelConfig.is_configured == True,
            )
        )
        config = result.scalar_one_or_none()
        if not config or not config.app_secret:
            return None
        
        try:
            return decrypt_data(config.app_secret, get_settings().SECRET_KEY)
        except Exception as exc:
            raise AtlassianSecretError(
                "Stored Atlassian API key cannot be decrypted"
            ) from exc

    if db is not None:
        return await _fetch(db)
    async with query_dao.session() as session:
        return await _fetch(session)
