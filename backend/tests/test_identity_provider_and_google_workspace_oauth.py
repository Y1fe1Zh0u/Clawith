import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.google_workspace_oauth import (
    GOOGLE_SSO_STATE_KIND,
    GOOGLE_SYNC_STATE_KIND,
    parse_google_oauth_state,
    sign_google_oauth_state,
    sign_google_sso_state,
)
from app.services.identity_provider_lookup import get_preferred_identity_provider


class _DummyResult:
    def __init__(self, values):
        self._values = list(values)

    def scalars(self):
        return self

    def all(self):
        return list(self._values)


class _DummyDB:
    def __init__(self, responses):
        self._responses = list(responses)

    async def execute(self, *_args, **_kwargs):
        return _DummyResult(self._responses.pop(0))


@pytest.mark.asyncio
async def test_identity_provider_lookup_tolerates_duplicate_rows():
    older = SimpleNamespace(
        id=uuid.uuid4(),
        provider_type="google_workspace",
        tenant_id=uuid.uuid4(),
        is_active=True,
        config={"client_id": "old"},
        updated_at=datetime(2024, 1, 1, tzinfo=UTC),
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    newer = SimpleNamespace(
        id=uuid.uuid4(),
        provider_type="google_workspace",
        tenant_id=older.tenant_id,
        is_active=True,
        config={"client_id": "new"},
        updated_at=datetime(2025, 1, 1, tzinfo=UTC),
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
    )
    db = _DummyDB([[newer, older]])

    provider = await get_preferred_identity_provider(
        cast(AsyncSession, db),
        "google_workspace",
        str(older.tenant_id),
        is_active=True,
    )

    assert provider is newer


def test_google_workspace_sso_state_includes_provider_id():
    sid = uuid.uuid4()
    provider_id = uuid.uuid4()

    state = sign_google_sso_state(sid, provider_id)
    parsed = parse_google_oauth_state(state)

    assert parsed == (GOOGLE_SSO_STATE_KIND, (sid, provider_id))


def test_google_workspace_sync_state_still_parses_single_uuid():
    provider_id = uuid.uuid4()

    state = sign_google_oauth_state(GOOGLE_SYNC_STATE_KIND, provider_id)
    parsed = parse_google_oauth_state(state)

    assert parsed == (GOOGLE_SYNC_STATE_KIND, (provider_id,))


def test_google_workspace_legacy_sso_state_still_parses():
    sid = uuid.uuid4()

    state = sign_google_oauth_state(GOOGLE_SSO_STATE_KIND, sid)
    parsed = parse_google_oauth_state(state)

    assert parsed == (GOOGLE_SSO_STATE_KIND, (sid,))
