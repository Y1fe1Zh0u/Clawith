"""Remove legacy Atlassian secret copies outside ChannelConfig.app_secret.

Usage from ``backend/``::

    uv run python scripts/remove_legacy_atlassian_agent_tool_secrets.py
    uv run python scripts/remove_legacy_atlassian_agent_tool_secrets.py --apply

Alembic migrations are DDL-only, so this data cleanup runs out of band. The
default is a read-only preview. ``--apply`` irreversibly removes supported
credential aliases from Atlassian Tool config, AgentTool config, and
ChannelConfig.extra_config. Unrelated config and rows are preserved. A downgrade
is intentionally unavailable because removed values cannot be restored safely.
ChannelConfig.app_secret remains the authoritative credential source.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from app.database import async_session
from app.models.channel_config import ChannelConfig
from app.models.tool import AgentTool, Tool
from app.services.atlassian_tool_service import (
    atlassian_tool_clause,
    without_atlassian_secret_fields,
)

SessionFactory = Callable[[], AbstractAsyncContextManager[AsyncSession]]


async def _process_batches(
    model: type[Tool | AgentTool | ChannelConfig],
    statement,
    config_field: str,
    batch_size: int,
    apply: bool,
    session_factory: SessionFactory,
) -> tuple[int, int, int]:
    scanned = matched = updated = 0
    last_id: uuid.UUID | None = None
    while True:
        async with session_factory() as db:
            query = statement.order_by(model.id).limit(batch_size)
            if last_id is not None:
                query = query.where(model.id > last_id)
            rows = list((await db.execute(query)).scalars().all())
            if not rows:
                break
            batch_updated = 0
            for row in rows:
                scanned += 1
                current = getattr(row, config_field)
                cleaned = without_atlassian_secret_fields(current)
                if cleaned == (current or {}):
                    continue
                matched += 1
                if apply:
                    setattr(row, config_field, cleaned)
                    batch_updated += 1
            if apply and batch_updated:
                try:
                    await db.commit()
                except Exception:
                    await db.rollback()
                    raise
                updated += batch_updated
            last_id = rows[-1].id
    return scanned, matched, updated


async def process_data(
    batch_size: int,
    apply: bool,
    *,
    session_factory: SessionFactory = async_session,
) -> int:
    mode = "APPLY" if apply else "DRY-RUN"
    tool_counts = await _process_batches(
        Tool,
        select(Tool).where(atlassian_tool_clause()),
        "config",
        batch_size,
        apply,
        session_factory,
    )
    assignment_counts = await _process_batches(
        AgentTool,
        select(AgentTool).join(Tool, AgentTool.tool_id == Tool.id).where(atlassian_tool_clause()),
        "config",
        batch_size,
        apply,
        session_factory,
    )
    channel_counts = await _process_batches(
        ChannelConfig,
        select(ChannelConfig).where(func.lower(func.trim(ChannelConfig.channel_type)) == "atlassian"),
        "extra_config",
        batch_size,
        apply,
        session_factory,
    )

    print(
        f"mode={mode} tools_scanned={tool_counts[0]} "
        f"tools_matched={tool_counts[1]} tools_updated={tool_counts[2]} "
        f"assignments_scanned={assignment_counts[0]} "
        f"assignments_matched={assignment_counts[1]} "
        f"assignments_updated={assignment_counts[2]} "
        f"channels_scanned={channel_counts[0]} "
        f"channels_matched={channel_counts[1]} "
        f"channels_updated={channel_counts[2]}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Irreversibly remove duplicate Atlassian secret fields",
    )
    args = parser.parse_args()
    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")
    return asyncio.run(process_data(args.batch_size, args.apply))


if __name__ == "__main__":
    raise SystemExit(main())
