"""Helpers for first-party chat session selection and creation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import ChatMessage
from app.models.chat_session import ChatSession


async def get_primary_platform_session(
    db: AsyncSession,
    agent_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ChatSession | None:
    """Return the current primary first-party session for a user+agent pair, if any."""

    result = await db.execute(
        select(ChatSession)
        .where(
            ChatSession.agent_id == agent_id,
            ChatSession.user_id == user_id,
            ChatSession.source_channel == "web",
            ChatSession.is_group.is_(False),
            ChatSession.is_primary.is_(True),
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


async def ensure_primary_platform_session(
    db: AsyncSession,
    agent_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ChatSession:
    """Return a guaranteed primary platform session for a given user+agent pair.

    Primary sessions are explicit fallback destinations for agent-initiated delivery.
    Do not promote existing non-primary web sessions; those are side-topic sessions
    and must remain isolated from fallback routing.
    """

    primary = await get_primary_platform_session(db, agent_id, user_id)
    if primary:
        return primary

    now = datetime.now(timezone.utc)
    session = ChatSession(
        agent_id=agent_id,
        user_id=user_id,
        title=f"Session {now.strftime('%m-%d %H:%M')}",
        source_channel="web",
        is_primary=True,
        created_at=now,
    )
    db.add(session)
    await db.flush()
    return session


async def save_tool_call_log(
    agent_id: uuid.UUID,
    user_id: uuid.UUID,
    conversation_id: str,
    tool_name: str,
    arguments: dict | None,
    result: str,
    status: str = "done",
    tool_call_id: str | None = None,
    reasoning_content: str | None = None,
) -> None:
    """Save a tool call execution log into chat history as a ChatMessage."""
    if not conversation_id:
        return
    import json
    from app.database import async_session
    from loguru import logger

    payload = {
        "name": tool_name,
        "args": arguments or {},
        "status": status,
        "result": str(result) if result is not None else "",
        "tool_call_id": tool_call_id,
        "reasoning_content": reasoning_content,
    }

    try:
        async with async_session() as db:
            db.add(ChatMessage(
                agent_id=agent_id,
                user_id=user_id,
                role="tool_call",
                content=json.dumps(payload, ensure_ascii=False, default=str),
                conversation_id=conversation_id,
            ))
            await db.commit()
    except Exception as e:
        logger.warning(f"Failed to save tool call log: {e}")
