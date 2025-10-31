"""Storage utilities for Paper Scope."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from backend.app.schemas import LLMAnalysis, PaperRecord


class StorageService:
    """Manage persistence of PDFs and metadata on disk."""

    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path
        self._base_path.mkdir(parents=True, exist_ok=True)

    def paper_directory(self, record: PaperRecord) -> Path:
        """Compute the directory where paper assets should be stored."""

        published = record.published_at or datetime.now(timezone.utc)
        year_segment = published.strftime("%Y")
        directory = self._base_path / record.source / year_segment / record.storage_key()
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def pdf_path(self, record: PaperRecord) -> Path:
        """Return the path where the PDF should be stored."""

        return self.paper_directory(record) / "paper.pdf"

    def metadata_path(self, record: PaperRecord) -> Path:
        """Return the path of the JSON metadata manifest."""

        return self.paper_directory(record) / "metadata.json"

    def write_metadata(self, record: PaperRecord, analysis: LLMAnalysis | None) -> Path:
        """Persist metadata and enrichment results alongside the paper."""

        data = {
            "record": record.model_dump(),
            "analysis": analysis.model_dump() if analysis else None,
        }
        path = self.metadata_path(record)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))
        return path

    def read_metadata(self, storage_path: Path | str) -> dict[str, Any] | None:
        """Load the stored metadata manifest for a paper."""

        manifest = Path(storage_path) / "metadata.json"
        if not manifest.exists():
            return None
        try:
            return json.loads(manifest.read_text())
        except json.JSONDecodeError:  # pragma: no cover - defensive path
            return None

    def load_record(self, storage_path: Path | str) -> PaperRecord | None:
        """Reconstruct the original :class:`PaperRecord` from metadata."""

        data = self.read_metadata(storage_path)
        if not data:
            return None
        record_payload = data.get("record")
        if not isinstance(record_payload, dict):
            return None
        try:
            return PaperRecord.model_validate(record_payload)
        except ValidationError:  # pragma: no cover - validation errors are rare but handled
            return None
