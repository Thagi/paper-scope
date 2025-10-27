"""Health check endpoints for Paper Scope."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="API health check")
def get_health() -> dict[str, str]:
    """Return the operational status of the API.

    Returns:
        dict[str, str]: A simple health status payload.
    """

    return {"status": "ok"}
