"""Paper retrieval endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from backend.app.dependencies import get_graph_repository
from backend.app.schemas import PaperGraph, StoredPaper
from backend.app.services.graph import Neo4jGraphRepository

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
