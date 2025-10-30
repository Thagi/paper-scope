"""LLM abstraction layer."""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.app.schemas import LLMAnalysis, PaperRecord


class LLMClient(ABC):
    """Interface for enrichment language models."""

    @abstractmethod
    async def analyze(self, record: PaperRecord, *, pdf_path: str | None = None) -> LLMAnalysis:
        """Generate an enrichment payload for the paper."""
