import contextlib

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
