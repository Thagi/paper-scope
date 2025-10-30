"""Ingestion endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from backend.app.dependencies import get_ingestion_service
from backend.app.schemas import PaperIngestionResult, PaperRecord
from backend.app.services.ingestion import IngestionService

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/run", response_model=PaperIngestionResult, status_code=status.HTTP_202_ACCEPTED)
async def trigger_ingestion(service: IngestionService = Depends(get_ingestion_service)) -> PaperIngestionResult:
    """Execute the ingestion pipeline on demand."""

    return await service.run(manual_trigger=True)


@router.get("/preview", response_model=list[PaperRecord])
async def preview_ingestion(service: IngestionService = Depends(get_ingestion_service)) -> list[PaperRecord]:
    """Return a preview of papers that would be ingested."""

    return await service.dry_run()
