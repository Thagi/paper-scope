"""Knowledge graph endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from backend.app.dependencies import get_graph_repository
from backend.app.schemas import PaperGraph
from backend.app.services.graph import Neo4jGraphRepository

router = APIRouter(prefix="/graphs", tags=["graphs"])


@router.get("/network", response_model=PaperGraph)
async def get_paper_network(
    limit: int = Query(50, ge=1, le=200),
    repository: Neo4jGraphRepository = Depends(get_graph_repository),
) -> PaperGraph:
    """Return a cross-paper knowledge graph."""

    return await repository.get_paper_network(limit)
