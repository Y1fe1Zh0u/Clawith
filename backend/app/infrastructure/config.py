"""Target application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

BACKEND_ROOT = Path(__file__).resolve().parents[2]
VERSION_PATH = BACKEND_ROOT / "VERSION"
ENV_FILE_PATH = BACKEND_ROOT / ".env"


def _read_version() -> str:
    version = VERSION_PATH.read_text(encoding="utf-8").strip()
    if not version:
        raise ValueError(f"version file is empty: {VERSION_PATH}")
    return version


class Settings(BaseSettings):
    """Configuration owned by the target composition and database infrastructure."""

    APP_NAME: str = Field(default="Clawith", min_length=1)
    APP_VERSION: str = Field(default_factory=_read_version, min_length=1)
    DEBUG: bool = False
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://clawith:clawith@localhost:5432/clawith_target",
    )
    CONTROL_DATABASE_POOL_SIZE: int = Field(default=20, gt=0)
    EXECUTION_DATABASE_POOL_SIZE: int = Field(default=20, gt=0)
    DATABASE_POOL_MAX_OVERFLOW: int = Field(default=0, ge=0)

    @field_validator("DATABASE_URL")
    @classmethod
    def _complete_async_postgres_url(cls, value: str) -> str:
        try:
            url = make_url(value)
        except ArgumentError as exc:
            raise ValueError("DATABASE_URL must be a complete SQLAlchemy URL") from exc

        required_parts = {
            "username": url.username,
            "password": url.password,
            "host": url.host,
            "port": url.port,
            "database": url.database,
        }
        missing = [name for name, part in required_parts.items() if part in (None, "")]
        invalid_port = url.port is not None and not 1 <= url.port <= 65535
        if url.drivername != "postgresql+asyncpg" or missing or invalid_port:
            detail = f"; missing {', '.join(missing)}" if missing else ""
            if invalid_port:
                detail = "; port must be between 1 and 65535"
            raise ValueError(
                "DATABASE_URL must use postgresql+asyncpg and include username, password, "
                f"host, port, and database{detail}"
            )
        return value

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="forbid",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the process configuration snapshot."""
    return Settings()
