"""Paper ingestion orchestration service."""

from __future__ import annotations

from collections.abc import Sequence

from backend.app.schemas import PaperIngestionResult, PaperRecord

from .crawlers.base import TrendingSource
from .downloader import PDFDownloader
from .graph import GraphRepository
from .llm.base import LLMClient
from .storage import StorageService


class IngestionService:
    """Coordinate the end-to-end ingestion workflow."""

    def __init__(
        self,
        *,
        sources: Sequence[TrendingSource],
        downloader: PDFDownloader,
        storage: StorageService,
        llm_client: LLMClient,
        graph_repository: GraphRepository,
        limit: int,
    ) -> None:
        self._sources = list(sources)
        self._downloader = downloader
        self._storage = storage
        self._llm_client = llm_client
        self._graph_repository = graph_repository
        self._limit = limit

    async def run(self, *, manual_trigger: bool = False) -> PaperIngestionResult:
        discovered = 0
        downloaded = 0
        enriched = 0
        persisted = 0
        details: list[dict[str, str]] = []

        for source in self._sources:
            try:
                records = await source.fetch(self._limit)
            except Exception as exc:  # pragma: no cover - defensive path
                details.append(
                    {
                        "source": source.name,
                        "status": "failed",
                        "error": str(exc),
                    }
                )
                continue

            if not records:
                details.append(
                    {
                        "source": source.name,
                        "status": "skipped",
                        "reason": "no_records",
                    }
                )
                continue

            discovered += len(records)
            for record in records:
                detail = {"source": source.name, "external_id": record.external_id}
                exists = await self._graph_repository.paper_exists(record.external_id)
                try:
                    pdf_path = self._storage.pdf_path(record)
                    await self._downloader.download(str(record.pdf_url), pdf_path)
                    downloaded += 1

                    analysis = await self._llm_client.analyze(record, pdf_path=str(pdf_path))
                    enriched += 1
                    self._storage.write_metadata(record, analysis)

                    await self._graph_repository.upsert_paper(
                        record,
                        analysis,
                        storage_path=self._storage.paper_directory(record),
                    )
                    persisted += 1
                    detail["status"] = "updated" if exists else "ingested"
                except Exception as exc:  # pragma: no cover - defensive path
                    detail["status"] = "failed"
                    detail["error"] = str(exc)
                details.append(detail)

        return PaperIngestionResult(
            discovered=discovered,
            downloaded=downloaded,
            enriched=enriched,
            persisted=persisted,
            manual_trigger=manual_trigger,
            details=details,
        )

    async def dry_run(self) -> list[PaperRecord]:
        """Fetch papers without mutating state (useful for previews)."""

        records: list[PaperRecord] = []
        for source in self._sources:
            records.extend(await source.fetch(self._limit))
        return records
