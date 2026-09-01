from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import admin as admin_api
from app.api import tenants as tenants_api  # pyright: ignore[reportAttributeAccessIssue]
from app.services.platform_service import platform_service


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

    async def execute(self, _statement):
        if self.responses:
            return self.responses.pop(0)
        return DummyResult()


@pytest.mark.asyncio
async def test_get_platform_settings_sso_toggle_default():
    """Verify that get_platform_settings returns sso_custom_domain_redirect_enabled by default."""
    db = RecordingDB(responses=[
        DummyResult(),  # allow_self_create_company lookup -> None (default True)
        DummyResult(),  # invitation_code_enabled lookup -> None (default False)
        DummyResult(),  # sso_custom_domain_redirect_enabled lookup -> None (default True)
    ])
    
    current_user = MagicMock()
    settings = await admin_api.get_platform_settings(
        current_user=current_user,
        db=cast(AsyncSession, db),
    )
    
    assert settings.sso_custom_domain_redirect_enabled is True
    assert settings.allow_self_create_company is True
    assert settings.invitation_code_enabled is False


@pytest.mark.asyncio
async def test_get_platform_settings_sso_toggle_disabled():
    """Verify that get_platform_settings returns sso_custom_domain_redirect_enabled False if set."""
    setting_record = SimpleNamespace(key="sso_custom_domain_redirect_enabled", value={"enabled": False})
    db = RecordingDB(responses=[
        DummyResult(),  # allow_self_create_company -> None
        DummyResult(),  # invitation_code_enabled -> None
        DummyResult(values=[setting_record]),  # sso_custom_domain_redirect_enabled -> disabled
    ])
    
    current_user = MagicMock()
    settings = await admin_api.get_platform_settings(
        current_user=current_user,
        db=cast(AsyncSession, db),
    )
    assert settings.sso_custom_domain_redirect_enabled is False


@pytest.mark.asyncio
async def test_resolve_tenant_by_domain_sso_toggle():
    """Verify that resolve_tenant_by_domain respects the sso_custom_domain_redirect_enabled toggle."""
    # When enabled, custom domain lookup should match the tenant by domain
    active_tenant = SimpleNamespace(id="tenant-id", name="Acme", slug="acme", sso_enabled=True, sso_domain="https://acme.com", is_active=True)
    
    # Check 1: SSO toggle enabled, matches tenant
    db_enabled = RecordingDB(responses=[
        DummyResult(),  # sso_custom_domain_redirect_enabled -> None (default True)
        DummyResult(values=[active_tenant]),  # Match for https://acme.com
    ])
    res = await tenants_api.resolve_tenant_by_domain(
        domain="acme.com",
        db=cast(AsyncSession, db_enabled),
    )
    assert res["id"] == "tenant-id"
    assert res["sso_domain"] == "https://acme.com"

    # Check 2: SSO toggle disabled, does not match tenant by domain, falls back or fails
    setting_disabled = SimpleNamespace(key="sso_custom_domain_redirect_enabled", value={"enabled": False})
    db_disabled = RecordingDB(responses=[
        DummyResult(values=[setting_disabled]),  # sso_custom_domain_redirect_enabled -> False
        DummyResult(),  # Fallback search slug (which fails)
    ])
    with pytest.raises(HTTPException) as exc:
        await tenants_api.resolve_tenant_by_domain(
            domain="acme.com",
            db=cast(AsyncSession, db_disabled),
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_tenant_sso_base_url_toggle():
    """Verify that get_tenant_sso_base_url respects the sso_redirect_enabled kwarg."""
    tenant = SimpleNamespace(slug="acme", sso_domain="https://acme.com")

    # 1. Enabled: returns the custom sso_domain
    url = await platform_service.get_tenant_sso_base_url(
        db=cast(AsyncSession, None), tenant=tenant, sso_redirect_enabled=True
    )
    assert url == "https://acme.com"

    # 2. Disabled: falls back to public base URL
    with patch.object(platform_service, "get_public_base_url", return_value="https://try.clawith.ai"):
        url = await platform_service.get_tenant_sso_base_url(
            db=cast(AsyncSession, None), tenant=tenant, sso_redirect_enabled=False
        )
        assert url == "https://try.clawith.ai"
