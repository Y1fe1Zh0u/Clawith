import contextlib
import uuid
from types import SimpleNamespace
from typing import cast

import pytest
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.notification import BroadcastRequest, broadcast_notification
from app.services import system_email_service


class DummyScalars:
    def __init__(self, values):
        self._values = list(values)

    def all(self):
        return list(self._values)


class DummyResult:
    def __init__(self, value=None, values=None):
        self._value = value
        self._values = list(values or [])

    def scalar_one_or_none(self):
        return self._value

    def scalars(self):
        return DummyScalars(self._values)


class RecordingDB:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.committed = False

    async def execute(self, statement):
        if self.responses:
            return self.responses.pop(0)
        return DummyResult()

    async def commit(self):
        self.committed = True


def make_user(**overrides):
    values = {
        "id": uuid.uuid4(),
        "username": "alice",
        "email": "alice@example.com",
        "password_hash": "old-hash",
        "display_name": "Alice",
        "role": "member",
        "tenant_id": uuid.uuid4(),
        "is_active": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_send_system_email_uses_configured_timeout(monkeypatch):
    captured = {}

    class DummySMTPSSL:
        def __init__(
            self,
            host: str,
            port: int,
            context=None,
            timeout: int | None = None,
        ):
            captured["host"] = host
            captured["port"] = port
            captured["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def login(self, username: str, password: str):
            captured["username"] = username
            captured["password"] = password

        def sendmail(self, from_address: str, to_addresses: list[str], message: str):
            captured["from"] = from_address
            captured["to"] = to_addresses
            captured["has_message"] = bool(message)

    config = system_email_service.SystemEmailConfig(
        from_address="bot@example.com",
        from_name="Clawith",
        smtp_host="smtp.example.com",
        smtp_port=465,
        smtp_username="bot@example.com",
        smtp_password="secret",
        smtp_ssl=True,
        smtp_timeout_seconds=27,
    )
    monkeypatch.setattr(system_email_service.smtplib, "SMTP_SSL", DummySMTPSSL)
    monkeypatch.setattr(
        system_email_service,
        "force_ipv4",
        lambda: contextlib.nullcontext(),
    )

    system_email_service._send_email_with_config_sync(
        config,
        "alice@example.com",
        "subject",
        "body",
    )

    assert captured["timeout"] == 27
    assert captured["to"] == ["alice@example.com"]


@pytest.mark.asyncio
async def test_broadcast_notification_rejects_missing_system_email_config(monkeypatch):
    current_user = make_user(role="org_admin")

    async def fake_resolve_email_config_async(db):
        return None

    monkeypatch.setattr(
        "app.services.system_email_service.resolve_email_config_async",
        fake_resolve_email_config_async,
    )

    with pytest.raises(HTTPException) as excinfo:
        await broadcast_notification(
            BroadcastRequest(title="Maintenance", body="Tonight", send_email=True),
            background_tasks=BackgroundTasks(),
            current_user=current_user,
            db=cast(AsyncSession, RecordingDB()),
        )

    assert excinfo.value.status_code == 400
    assert "System email is not configured" in excinfo.value.detail


@pytest.mark.asyncio
async def test_broadcast_notification_queues_email_delivery(monkeypatch):
    current_user = make_user(role="org_admin")
    target_user = make_user(email="bob@example.com", tenant_id=current_user.tenant_id)
    db = RecordingDB(
        [
            DummyResult(values=[target_user]),
            DummyResult(values=[]),
        ]
    )
    background_tasks = BackgroundTasks()

    async def fake_resolve_email_config_async(db):
        return system_email_service.SystemEmailConfig(
            from_address="bot@example.com",
            from_name="Clawith",
            smtp_host="smtp.example.com",
            smtp_port=465,
            smtp_username="bot@example.com",
            smtp_password="secret",
            smtp_ssl=True,
            smtp_timeout_seconds=15,
        )

    monkeypatch.setattr(
        "app.services.system_email_service.resolve_email_config_async",
        fake_resolve_email_config_async,
    )
    notifications = []

    async def fake_send_notification(*_args, **kwargs):
        notifications.append(kwargs)

    monkeypatch.setattr(
        "app.services.notification_service.send_notification",
        fake_send_notification,
    )

    response = await broadcast_notification(
        BroadcastRequest(title="Maintenance", body="Tonight", send_email=True),
        background_tasks=background_tasks,
        current_user=current_user,
        db=cast(AsyncSession, db),
    )

    assert response["ok"] is True
    assert response["emails_sent"] == 1
    assert db.committed is True
    assert len(notifications) == 1
    assert len(background_tasks.tasks) == 1


@pytest.mark.asyncio
async def test_deliver_broadcast_emails_continues_after_single_failure(monkeypatch):
    from app.services.system_email_service import (
        BroadcastEmailRecipient,
        deliver_broadcast_emails,
    )

    delivered = []

    async def fake_send_system_email(email: str, subject: str, body: str) -> None:
        if email == "bad@example.com":
            raise RuntimeError("smtp down")
        delivered.append((email, subject, body))

    monkeypatch.setattr(
        "app.services.system_email_service.send_system_email",
        fake_send_system_email,
    )

    await deliver_broadcast_emails(
        [
            BroadcastEmailRecipient(email="bad@example.com", subject="s1", body="b1"),
            BroadcastEmailRecipient(email="good@example.com", subject="s2", body="b2"),
        ]
    )

    assert delivered == [("good@example.com", "s2", "b2")]
