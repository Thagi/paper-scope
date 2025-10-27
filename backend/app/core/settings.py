"""Application configuration for Paper Scope."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration for the FastAPI backend."""

    app_name: str = Field(default="Paper Scope API", description="Human readable application name.")
    version: str = Field(default="0.1.0", description="Semantic version of the API.")
    scheduler_timezone: str = Field(default="UTC", description="Timezone used by the scheduler.")

    model_config = {
        "env_file": ".env",
        "env_prefix": "PAPER_SCOPE_",
    }


@lru_cache
def get_settings() -> Settings:
    """Retrieve a cached settings instance.

    Returns:
        Settings: The cached application settings.
    """

    return Settings()
