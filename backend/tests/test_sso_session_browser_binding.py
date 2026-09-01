import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import cast

import pytest
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import sso as sso_api
from app.services.sso_session_security import (
    sign_sso_browser_binding,
    sso_browser_cookie_name,
)


class DummyResult:
    def __init__(self, scalar_value=None):
        self._scalar_value = scalar_value

    def scalar_one_or_none(self):
        return self._scalar_value


class RecordingDB:
    def __init__(self, responses=None):
        self.responses = list(responses or [])

    async def execute(self, _statement, _params=None):
        if not self.responses:
            return DummyResult()
        return self.responses.pop(0)


@pytest.mark.asyncio
async def test_sso_session_status_rejects_a_browser_without_its_binding_cookie():
    session_id = uuid.uuid4()
    request = Request({"type": "http", "headers": []})

    with pytest.raises(HTTPException, match="not bound to this browser") as exc_info:
        await sso_api.get_sso_session_status(
            session_id,
            request,
            cast(AsyncSession, RecordingDB()),
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_sso_session_status_accepts_the_initiating_browser_cookie():
    session_id = uuid.uuid4()
    cookie_name = sso_browser_cookie_name(session_id)
    cookie_value = sign_sso_browser_binding(session_id)
    request = Request(
        {
            "type": "http",
            "headers": [(b"cookie", f"{cookie_name}={cookie_value}".encode())],
        }
    )
    session = SimpleNamespace(
        expires_at=datetime.now(UTC) + timedelta(minutes=1),
        status="pending",
        provider_type=None,
        error_msg=None,
    )

    result = await sso_api.get_sso_session_status(
        session_id,
        request,
        cast(AsyncSession, RecordingDB([DummyResult(scalar_value=session)])),
    )

    assert result == {
        "status": "pending",
        "provider_type": None,
        "error_msg": None,
    }
