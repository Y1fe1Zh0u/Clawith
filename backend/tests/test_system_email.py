import contextlib

import pytest

from app.services import system_email_service


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
async def test_deliver_broadcast_emails_continues_after_single_failure(monkeypatch):
    delivered = []

    async def fake_send_system_email(email: str, subject: str, body: str) -> None:
        if email == "bad@example.com":
            raise RuntimeError("smtp down")
        delivered.append((email, subject, body))

    monkeypatch.setattr(
        system_email_service,
        "send_system_email",
        fake_send_system_email,
    )

    await system_email_service.deliver_broadcast_emails(
        [
            system_email_service.BroadcastEmailRecipient(
                email="bad@example.com",
                subject="s1",
                body="b1",
            ),
            system_email_service.BroadcastEmailRecipient(
                email="good@example.com",
                subject="s2",
                body="b2",
            ),
        ]
    )

    assert delivered == [("good@example.com", "s2", "b2")]
