"""Factory helpers for instantiating LLM clients."""

from __future__ import annotations

from backend.app.core.settings import Settings

from .base import LLMClient
from .mock import MockLLMClient
from .ollama import OllamaLLMClient
from .openai import OpenAILLMClient


def build_llm_client(settings: Settings) -> LLMClient:
    """Create an LLM client based on application settings."""

    if settings.llm_provider == "mock":
        return MockLLMClient()
    if settings.llm_provider == "ollama":
        return OllamaLLMClient(base_url=str(settings.ollama_base_url), model=settings.ollama_model)
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OpenAI provider selected but PAPER_SCOPE_OPENAI_API_KEY is missing")
        return OpenAILLMClient(api_key=settings.openai_api_key, model=settings.openai_model)
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
