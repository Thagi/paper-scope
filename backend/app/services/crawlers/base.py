"""Base classes for ingestion crawlers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.app.schemas import PaperRecord


class TrendingSource(ABC):
    """Abstract base class for trending paper sources."""

    name: str

    @abstractmethod
    async def fetch(self, limit: int) -> list[PaperRecord]:
        """Fetch a list of trending papers.

        Args:
            limit: Maximum number of papers to return.

        Returns:
            List of paper records discovered from the source.
        """


class MetadataEnricher(ABC):
    """Optional component to augment records with additional metadata."""

    @abstractmethod
    async def enrich(self, record: PaperRecord) -> PaperRecord:
        """Return an enriched copy of the paper record."""
