import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.models.trigger import AgentTrigger
from app.services import chat_session_service
from app.services.trigger_runtime import invoker


class DummyResult:
    def __init__(self, scalar_value=None):
        self._scalar_value = scalar_value

    def scalar_one_or_none(self):
        return self._scalar_value


class RecordingDB:
    def __init__(self, *, get_values=None, execute_results=None):
        self.get_values = dict(get_values or {})
        self.execute_results = list(execute_results or [])
        self.added = []
        self.committed = False
        self.flushed = False

    async def get(self, _model, key):
        return self.get_values.get(key)

    async def execute(self, _statement, _params=None):
        if not self.execute_results:
            raise AssertionError("unexpected execute() call")
        return self.execute_results.pop(0)

    def add(self, value):
        self.added.append(value)

    async def commit(self):
        self.committed = True

    async def flush(self):
        self.flushed = True


class AsyncSessionFactory:
    def __init__(self, db):
        self.db = db

    def __call__(self):
        return self

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, *_exc):
        return False


@pytest.mark.asyncio
async def test_trigger_delivery_prefers_origin_web_session(monkeypatch):
    agent_id = uuid.uuid4()
    user_id = uuid.uuid4()
    origin_session_id = uuid.uuid4()
    primary_session_id = uuid.uuid4()
    origin_session = SimpleNamespace(
        id=origin_session_id,
        user_id=user_id,
        source_channel="web",
        external_conv_id=None,
        is_group=False,
    )
    primary_session = SimpleNamespace(
        id=primary_session_id,
        user_id=user_id,
        source_channel="web",
        external_conv_id=None,
        is_group=False,
    )
    trigger = AgentTrigger(
        agent_id=agent_id,
        name="reminder",
        type="once",
        config={
            "_origin_session_id": str(origin_session_id),
            "_origin_user_id": str(user_id),
            "_origin_source_channel": "web",
        },
    )
    db = RecordingDB(get_values={origin_session_id: origin_session})
    ensure_primary = AsyncMock(return_value=primary_session)

    monkeypatch.setattr(invoker, "async_session", AsyncSessionFactory(db))
    monkeypatch.setattr(chat_session_service, "ensure_primary_platform_session", ensure_primary)

    target = await invoker.resolve_trigger_delivery_target(SimpleNamespace(id=agent_id), [trigger])

    assert target == {
        "kind": "session",
        "session_id": str(origin_session_id),
        "owner_user_id": str(user_id),
        "source_channel": "web",
        "external_conv_id": None,
        "is_group": False,
    }
    ensure_primary.assert_not_called()


@pytest.mark.asyncio
async def test_trigger_delivery_falls_back_to_primary_when_origin_session_missing(monkeypatch):
    agent_id = uuid.uuid4()
    user_id = uuid.uuid4()
    missing_origin_session_id = uuid.uuid4()
    primary_session_id = uuid.uuid4()
    primary_session = SimpleNamespace(
        id=primary_session_id,
        user_id=user_id,
        source_channel="web",
        external_conv_id=None,
        is_group=False,
    )
    trigger = AgentTrigger(
        agent_id=agent_id,
        name="reminder",
        type="once",
        config={
            "_origin_session_id": str(missing_origin_session_id),
            "_origin_user_id": str(user_id),
            "_origin_source_channel": "web",
        },
    )
    db = RecordingDB(get_values={})
    ensure_primary = AsyncMock(return_value=primary_session)

    monkeypatch.setattr(invoker, "async_session", AsyncSessionFactory(db))
    monkeypatch.setattr(chat_session_service, "ensure_primary_platform_session", ensure_primary)

    target = await invoker.resolve_trigger_delivery_target(SimpleNamespace(id=agent_id), [trigger])

    assert target == {
        "kind": "primary_user_session",
        "session_id": str(primary_session_id),
        "owner_user_id": str(user_id),
        "source_channel": "web",
        "external_conv_id": None,
        "is_group": False,
    }
    ensure_primary.assert_awaited_once_with(db, agent_id, user_id)
    assert db.committed is True


@pytest.mark.asyncio
async def test_trigger_delivery_prefers_origin_channel_session(monkeypatch):
    agent_id = uuid.uuid4()
    user_id = uuid.uuid4()
    origin_session_id = uuid.uuid4()
    origin_session = SimpleNamespace(
        id=origin_session_id,
        user_id=user_id,
        source_channel="feishu",
        external_conv_id="feishu_p2p_ou_123",
        is_group=False,
    )
    trigger = AgentTrigger(
        agent_id=agent_id,
        name="webhook",
        type="webhook",
        config={
            "_origin_session_id": str(origin_session_id),
            "_origin_user_id": str(user_id),
            "_origin_source_channel": "feishu",
        },
    )
    db = RecordingDB(get_values={origin_session_id: origin_session})
    ensure_primary = AsyncMock()

    monkeypatch.setattr(invoker, "async_session", AsyncSessionFactory(db))
    monkeypatch.setattr(chat_session_service, "ensure_primary_platform_session", ensure_primary)

    target = await invoker.resolve_trigger_delivery_target(SimpleNamespace(id=agent_id), [trigger])

    assert target == {
        "kind": "session",
        "session_id": str(origin_session_id),
        "owner_user_id": str(user_id),
        "source_channel": "feishu",
        "external_conv_id": "feishu_p2p_ou_123",
        "is_group": False,
    }
    ensure_primary.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_primary_platform_session_does_not_promote_existing_side_session():
    agent_id = uuid.uuid4()
    user_id = uuid.uuid4()
    ordinary_session = SimpleNamespace(
        id=uuid.uuid4(),
        agent_id=agent_id,
        user_id=user_id,
        source_channel="web",
        is_group=False,
        is_primary=False,
    )
    db = RecordingDB(
        execute_results=[
            DummyResult(None),
        ]
    )

    primary = await chat_session_service.ensure_primary_platform_session(db, agent_id, user_id)

    assert primary is not ordinary_session
    assert ordinary_session.is_primary is False
    assert db.added == [primary]
    assert primary.agent_id == agent_id
    assert primary.user_id == user_id
    assert primary.source_channel == "web"
    assert primary.is_primary is True
    assert db.flushed is True
