"""Remove legacy Atlassian secrets duplicated in AgentTool.config.

Usage from ``backend/``::

    uv run python scripts/remove_legacy_atlassian_agent_tool_secrets.py
    uv run python scripts/remove_legacy_atlassian_agent_tool_secrets.py --apply

Alembic migrations are DDL-only, so this data cleanup runs out of band. The
default is a read-only preview. ``--apply`` irreversibly removes only the
``api_key`` and ``atlassian_api_key`` fields from Atlassian AgentTool rows;
unrelated assignment config and shared Tool rows are preserved. A downgrade is
intentionally unavailable because removed legacy values may be plaintext or
corrupt ciphertext and cannot be restored safely. ChannelConfig remains the
authoritative encrypted credential source.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from app.database import async_session
from app.models.tool import AgentTool, Tool

SessionFactory = Callable[[], AbstractAsyncContextManager[AsyncSession]]
_LEGACY_SECRET_KEYS = frozenset({"api_key", "atlassian_api_key"})


def _without_legacy_secret_fields(config: object) -> tuple[dict, bool]:
    if not isinstance(config, dict):
        return {}, False
    cleaned = {
        key: value
        for key, value in config.items()
        if key not in _LEGACY_SECRET_KEYS
    }
    return cleaned, cleaned != config


async def process_data(
    batch_size: int,
    apply: bool,
    *,
    session_factory: SessionFactory = async_session,
) -> int:
    mode = "APPLY" if apply else "DRY-RUN"
    scanned = 0
    matched = 0
    updated = 0
    last_id: uuid.UUID | None = None

    while True:
        async with session_factory() as db:
            statement = (
                select(AgentTool)
                .join(Tool, AgentTool.tool_id == Tool.id)
                .where(Tool.category == "atlassian")
                .order_by(AgentTool.id)
                .limit(batch_size)
            )
            if last_id is not None:
                statement = statement.where(AgentTool.id > last_id)

            assignments = list((await db.execute(statement)).scalars().all())
            if not assignments:
                break

            batch_updated = 0
            for assignment in assignments:
                scanned += 1
                cleaned, changed = _without_legacy_secret_fields(
                    assignment.config
                )
                if not changed:
                    continue
                matched += 1
                if apply:
                    assignment.config = cleaned
                    batch_updated += 1

            if apply and batch_updated:
                try:
                    await db.commit()
                except Exception:
                    await db.rollback()
                    raise
                updated += batch_updated

            last_id = assignments[-1].id

    print(
        f"mode={mode} scanned={scanned} matched={matched} updated={updated}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Irreversibly remove duplicate Atlassian AgentTool secret fields",
    )
    args = parser.parse_args()
    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")
    return asyncio.run(process_data(args.batch_size, args.apply))


if __name__ == "__main__":
    raise SystemExit(main())
