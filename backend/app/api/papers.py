"""Paper retrieval endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from backend.app.dependencies import (
    get_graph_repository,
    get_llm_client,
    get_storage_service,
)
from backend.app.schemas import PaperGraph, StoredPaper
from backend.app.services.graph import Neo4jGraphRepository
from backend.app.services.llm.base import LLMClient
from backend.app.services.storage import StorageService

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("/", response_model=list[StoredPaper])
async def list_papers(
    limit: int = Query(25, ge=1, le=100),
    repository: Neo4jGraphRepository = Depends(get_graph_repository),
) -> list[StoredPaper]:
    """Return a paginated list of recently ingested papers."""

    return await repository.get_recent_papers(limit)


@router.get("/{external_id}/graph", response_model=PaperGraph)
async def get_paper_graph(
    external_id: str,
    repository: Neo4jGraphRepository = Depends(get_graph_repository),
) -> PaperGraph:
    """Return the knowledge graph neighborhood for a paper."""

    return await repository.get_paper_graph(external_id)


@router.get("/{external_id}/pdf")
async def get_paper_pdf(
    external_id: str,
    repository: Neo4jGraphRepository = Depends(get_graph_repository),
) -> FileResponse:
    """Stream the PDF associated with a paper."""

    paper = await repository.get_paper(external_id)
    if not paper or not paper.storage_path:
        raise HTTPException(status_code=404, detail="Paper not found")
    pdf_path = Path(paper.storage_path) / "paper.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not available")
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"{external_id}.pdf")


@router.post("/{external_id}/chapters/regenerate", response_model=StoredPaper)
async def regenerate_chapters(
    external_id: str,
    repository: Neo4jGraphRepository = Depends(get_graph_repository),
    storage: StorageService = Depends(get_storage_service),
    llm_client: LLMClient = Depends(get_llm_client),
) -> StoredPaper:
    """Re-run LLM analysis to regenerate chapter explanations for a paper."""

    paper = await repository.get_paper(external_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    if not paper.storage_path:
        raise HTTPException(
            status_code=400, detail="Paper storage path not available for regeneration"
        )

    record = storage.load_record(paper.storage_path)
    if not record:
        raise HTTPException(
            status_code=400, detail="Stored paper metadata is missing or invalid"
        )

    pdf_path = paper.storage_path / "paper.pdf"
    pdf_arg = str(pdf_path) if pdf_path.exists() else None

    analysis = await llm_client.analyze(record, pdf_path=pdf_arg)
    storage.write_metadata(record, analysis)
    await repository.upsert_paper(record, analysis, storage_path=paper.storage_path)

    refreshed = await repository.get_paper(external_id)
    if not refreshed:
        raise HTTPException(status_code=500, detail="Failed to load regenerated paper")
    return refreshed
