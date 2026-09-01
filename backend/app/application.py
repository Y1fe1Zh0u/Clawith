"""Final application composition root."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure import database
from app.infrastructure.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Compose the target application without legacy routes or lifecycle work."""
    application_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        resources = await database.create_database_resources(application_settings)
        application.state.database = resources
        try:
            yield
        finally:
            try:
                await resources.aclose()
            finally:
                del application.state.database

    application = FastAPI(
        title=application_settings.APP_NAME,
        version=application_settings.APP_VERSION,
        debug=application_settings.DEBUG,
        lifespan=lifespan,
    )

    @application.get("/api/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "version": application_settings.APP_VERSION}

    return application
