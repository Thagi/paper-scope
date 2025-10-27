"""FastAPI application entry point for Paper Scope."""

from __future__ import annotations

from fastapi import FastAPI

from .api.router import api_router
from .core.settings import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance.

    Returns:
        FastAPI: A configured FastAPI application.
    """

    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.version)
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
