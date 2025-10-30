"""API router composition for Paper Scope."""

from __future__ import annotations

from fastapi import APIRouter

from . import graphs, health, ingest, papers

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(ingest.router)
api_router.include_router(papers.router)
api_router.include_router(graphs.router)
