"""Application configuration for Paper Scope."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration for the FastAPI backend."""

    app_name: str = Field(default="Paper Scope API", description="Human readable application name.")
    version: str = Field(default="0.1.0", description="Semantic version of the API.")
    scheduler_timezone: str = Field(default="UTC", description="Timezone used by the scheduler.")
    ingestion_limit: int = Field(default=10, description="Maximum number of papers to ingest per source run.")

    storage_root: Path = Field(default=Path("/data/papers"), description="Base directory for downloaded PDFs and metadata.")
    huggingface_trending_url: AnyHttpUrl = Field(
        default="https://huggingface.co/papers/trending",
        description="Trending papers page scraped for ingestion.",
    )

    llm_provider: Literal["openai", "ollama", "mock"] = Field(
        default="mock",
        description="LLM provider used for enrichment. 'mock' is suitable for development/testing.",
    )
    openai_api_key: str | None = Field(default=None, description="API key for OpenAI completion APIs.")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model used for enrichment.")
    ollama_base_url: AnyHttpUrl = Field(
        default="http://host.containers.internal:11434",
        description=(
            "Base URL for the Ollama server. Defaults to the host bridge address when running "
            "in containers."
        ),
    )
    ollama_model: str = Field(default="mistral", description="Ollama model used for enrichment.")

    neo4j_uri: AnyUrl = Field(default="bolt://neo4j:7687", description="Neo4j Bolt connection URI.")
    neo4j_user: str = Field(default="neo4j", description="Neo4j authentication user name.")
    neo4j_password: str = Field(
        default="changeme123", description="Neo4j authentication password (minimum 8 characters)."
    )

    model_config = {
        "env_file": ".env",
        "env_prefix": "PAPER_SCOPE_",
    }

    @field_validator("storage_root", mode="before")
    @classmethod
    def _coerce_storage_root(cls, value: str | Path) -> Path:
        """Ensure the storage root is stored as an absolute Path."""

        return Path(value).expanduser().resolve()


@lru_cache
def get_settings() -> Settings:
    """Retrieve a cached settings instance.

    Returns:
        Settings: The cached application settings.
    """

    return Settings()
