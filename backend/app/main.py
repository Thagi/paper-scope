"""FastAPI application entry point for Paper Scope."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.router import api_router
from .core.settings import get_settings
from .dependencies import get_neo4j_driver
from .services.graph import Neo4jGraphRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown tasks."""

    driver = get_neo4j_driver()
    repository = Neo4jGraphRepository(driver)
    await repository.ensure_constraints()
    try:
        yield
    finally:
        await driver.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance.

    Returns:
        FastAPI: A configured FastAPI application.
    """

    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
