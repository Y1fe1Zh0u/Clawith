"""Atlassian Rovo configuration transport routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import check_agent_access, is_agent_creator
from app.core.security import get_current_user
from app.database import get_db
from app.models.channel_config import ChannelConfig
from app.models.user import User
from app.services.atlassian_tool_service import (
    AtlassianConfigurationError,
    AtlassianNotConfiguredError,
    AtlassianSecretError,
    AtlassianSyncError,
    configure_atlassian_for_agent,
    delete_atlassian_for_agent,
    get_atlassian_configuration,
    test_atlassian_for_agent,
    without_atlassian_secret_fields,
)

router = APIRouter(tags=["atlassian"])


def _serialize(config: ChannelConfig) -> dict:
    extra_config = without_atlassian_secret_fields(config.extra_config)
    return {
        "id": str(config.id),
        "agent_id": str(config.agent_id),
        "channel_type": config.channel_type,
        "is_configured": config.is_configured,
        "is_connected": config.is_connected,
        "cloud_id": extra_config.get("cloud_id", ""),
        "extra_config": extra_config,
        "created_at": config.created_at.isoformat() if config.created_at else None,
    }


@router.post("/agents/{agent_id}/atlassian-channel", status_code=201)
async def configure_atlassian_channel(
    agent_id: uuid.UUID,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent, _ = await check_agent_access(db, current_user, agent_id)
    if not is_agent_creator(current_user, agent):
        raise HTTPException(status_code=403, detail="Only creator can configure channel")

    api_key = str(data.get("api_key") or "").strip()
    if not api_key:
        raise HTTPException(status_code=422, detail="api_key is required")
    cloud_id = str(data.get("cloud_id") or "").strip()
    try:
        config = await configure_atlassian_for_agent(
            agent_id,
            api_key,
            cloud_id,
            db,
        )
    except AtlassianSecretError as exc:
        raise HTTPException(
            status_code=500,
            detail="Atlassian API key encryption failed",
        ) from exc
    except AtlassianSyncError as exc:
        raise HTTPException(
            status_code=502,
            detail="Atlassian tool synchronization failed",
        ) from exc
    except AtlassianConfigurationError as exc:
        raise HTTPException(
            status_code=500,
            detail="Atlassian configuration could not be saved",
        ) from exc
    return _serialize(config)


@router.get("/agents/{agent_id}/atlassian-channel")
async def get_atlassian_channel(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await check_agent_access(db, current_user, agent_id)
    config = await get_atlassian_configuration(agent_id, db)
    if config is None:
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
    try:
        deleted = await delete_atlassian_for_agent(agent_id, db)
    except AtlassianConfigurationError as exc:
        raise HTTPException(
            status_code=500,
            detail="Atlassian configuration cleanup failed",
        ) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Atlassian not configured")


@router.post("/agents/{agent_id}/atlassian-channel/test")
async def test_atlassian_channel(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await check_agent_access(db, current_user, agent_id)
    try:
        tools = await test_atlassian_for_agent(agent_id, db)
    except AtlassianSecretError as exc:
        raise HTTPException(
            status_code=500,
            detail="Stored Atlassian API key is invalid",
        ) from exc
    except AtlassianNotConfiguredError as exc:
        raise HTTPException(
            status_code=400,
            detail="Atlassian not configured",
        ) from exc
    except AtlassianConfigurationError as exc:
        raise HTTPException(
            status_code=500,
            detail="Atlassian configuration could not be read",
        ) from exc
    except AtlassianSyncError as exc:
        return {"ok": False, "error": str(exc)[:300]}
    return {
        "ok": True,
        "tool_count": len(tools),
        "tools": [
            {
                "name": tool["name"],
                "description": tool.get("description", "")[:100],
            }
            for tool in tools[:10]
        ],
        "message": (
            f"✅ Connected to Atlassian Rovo MCP — {len(tools)} tools available"
        ),
    }
