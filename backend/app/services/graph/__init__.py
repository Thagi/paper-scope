"""Graph service exports."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from backend.app.schemas import LLMAnalysis, PaperGraph, PaperRecord, StoredPaper


class GraphRepository(Protocol):
    """Protocol describing the graph repository contract."""

    async def ensure_constraints(self) -> None:  # pragma: no cover - interface definition
        """Ensure required database constraints exist."""

    async def paper_exists(self, external_id: str) -> bool:
        """Return whether the paper already exists in storage."""

    async def upsert_paper(self, record: PaperRecord, analysis: LLMAnalysis, *, storage_path: str | Path) -> None:
        """Persist a paper and its analysis."""

    async def get_recent_papers(self, limit: int) -> list[StoredPaper]:
        """Fetch recent papers from the graph."""

    async def get_paper_graph(self, external_id: str) -> PaperGraph:
        """Retrieve the graph around a paper."""

    async def get_paper_network(self, limit: int) -> PaperGraph:
        """Retrieve a cross-paper knowledge graph."""

    async def get_paper(self, external_id: str) -> StoredPaper | None:
        """Fetch a single paper by identifier."""


from .repository import Neo4jGraphRepository

__all__ = ["GraphRepository", "Neo4jGraphRepository"]
