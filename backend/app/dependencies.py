"""Dependency wiring for FastAPI routes."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends
from neo4j import AsyncDriver, AsyncGraphDatabase

from backend.app.core.settings import Settings, get_settings
from backend.app.services.crawlers.huggingface import HuggingFaceTrendingClient
from backend.app.services.downloader import PDFDownloader
from backend.app.services.graph import Neo4jGraphRepository
from backend.app.services.ingestion import IngestionService
from backend.app.services.llm.base import LLMClient
from backend.app.services.llm.factory import build_llm_client
from backend.app.services.storage import StorageService


@lru_cache
def get_cached_settings() -> Settings:
    return get_settings()


@lru_cache
def get_neo4j_driver() -> AsyncDriver:
    settings = get_cached_settings()
    return AsyncGraphDatabase.driver(
        str(settings.neo4j_uri), auth=(settings.neo4j_user, settings.neo4j_password)
    )


def get_graph_repository() -> Neo4jGraphRepository:
    return Neo4jGraphRepository(get_neo4j_driver())


@lru_cache
def get_storage_service() -> StorageService:
    settings = get_cached_settings()
    return StorageService(settings.storage_root)


@lru_cache
def get_pdf_downloader() -> PDFDownloader:
    return PDFDownloader()


@lru_cache
def get_llm_client() -> LLMClient:
    settings = get_cached_settings()
    return build_llm_client(settings)


def get_ingestion_service(
    graph_repository: Neo4jGraphRepository = Depends(get_graph_repository),
) -> IngestionService:
    settings = get_cached_settings()
    sources = [HuggingFaceTrendingClient(str(settings.huggingface_trending_url))]
    return IngestionService(
        sources=sources,
        downloader=get_pdf_downloader(),
        storage=get_storage_service(),
        llm_client=get_llm_client(),
        graph_repository=graph_repository,
        limit=settings.ingestion_limit,
    )
