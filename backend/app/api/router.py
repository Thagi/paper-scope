"""API router composition for Paper Scope."""

from __future__ import annotations

from fastapi import APIRouter

from . import health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
