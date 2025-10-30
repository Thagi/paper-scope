"""Tests for the ingestion service orchestration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.schemas import LLMAnalysis, PaperRecord
from backend.app.services.crawlers.base import TrendingSource
from backend.app.services.ingestion import IngestionService
from backend.app.services.storage import StorageService


class DummyTrendingSource(TrendingSource):
    """Simple trending source returning a fixed set of records."""

    name = "dummy"

    def __init__(self, records: list[PaperRecord]) -> None:
        self._records = records

    async def fetch(self, limit: int) -> list[PaperRecord]:
        return self._records[:limit]


class DummyDownloader:
    """Downloader that writes a placeholder PDF file."""

    def __init__(self) -> None:
        self.downloaded: list[Path] = []

    async def download(self, url: str, destination: Path) -> Path:  # noqa: ARG002 - parity with interface
        destination.write_bytes(b"%PDF-1.4 test content")
        self.downloaded.append(destination)
        return destination


class DummyLLM:
    """LLM client returning deterministic output."""

    async def analyze(self, record: PaperRecord, *, pdf_path: str | None = None) -> LLMAnalysis:  # noqa: ARG002
        return LLMAnalysis(summary=f"Summary for {record.title}", key_points=[record.title])


class InMemoryGraphRepository:
    """Graph repository capturing persisted papers in memory."""

    def __init__(self) -> None:
        self.records: dict[str, tuple[PaperRecord, LLMAnalysis, Path]] = {}

    async def ensure_constraints(self) -> None:  # pragma: no cover - no-op
        return None

    async def paper_exists(self, external_id: str) -> bool:
        return external_id in self.records

    async def upsert_paper(self, record: PaperRecord, analysis: LLMAnalysis, *, storage_path: Path) -> None:
        self.records[record.external_id] = (record, analysis, storage_path)

    async def get_recent_papers(self, limit: int):  # pragma: no cover - not used here
        raise NotImplementedError

    async def get_paper_graph(self, external_id: str):  # pragma: no cover - not used here
        raise NotImplementedError

    async def get_paper_network(self, limit: int):  # pragma: no cover - not used here
        raise NotImplementedError


@pytest.mark.asyncio
async def test_ingestion_service_ingests_new_paper(tmp_path: Path) -> None:
    """Ensure the ingestion service downloads, enriches, and persists papers."""

    record = PaperRecord(
        external_id="1234.5678",
        source="dummy",
        title="Test Paper",
        authors=["Alice", "Bob"],
        abstract="A fascinating test paper.",
        pdf_url="https://example.com/paper.pdf",
        landing_url="https://example.com",
    )
    storage = StorageService(tmp_path)
    downloader = DummyDownloader()
    llm = DummyLLM()
    graph_repository = InMemoryGraphRepository()

    service = IngestionService(
        sources=[DummyTrendingSource([record])],
        downloader=downloader,
        storage=storage,
        llm_client=llm,
        graph_repository=graph_repository,
        limit=10,
    )

    result = await service.run(manual_trigger=True)

    assert result.discovered == 1
    assert result.downloaded == 1
    assert result.enriched == 1
    assert result.persisted == 1
    assert result.manual_trigger is True
    assert graph_repository.records[record.external_id][0].title == "Test Paper"

    metadata_path = storage.metadata_path(record)
    assert metadata_path.exists()
    content = json.loads(metadata_path.read_text())
    assert content["analysis"]["summary"] == "Summary for Test Paper"
