"""Client utilities for interacting with the FastAPI backend."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import httpx

DEFAULT_API_BASE = os.getenv("PAPER_SCOPE_BACKEND_URL", "http://localhost:8000/api")


class BackendClient:
    """Simple synchronous client for backend API operations."""

    def __init__(self, base_url: str | None = None, *, timeout: float = 10.0) -> None:
        self._base_url = (base_url or DEFAULT_API_BASE).rstrip("/")
        public_override = os.getenv("PAPER_SCOPE_BACKEND_PUBLIC_URL")
        if public_override:
            self._public_base_url = public_override.rstrip("/")
        else:
            # Default to the nginx-routed path so browsers resolve correctly.
            self._public_base_url = "/api"
        self._timeout = timeout

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self._base_url}{path}"
        with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
            response = client.request(method, url, **kwargs)
            response.raise_for_status()
            if "application/json" in response.headers.get("Content-Type", ""):
                return response.json()
            return response.content

    def trigger_ingestion(self) -> dict[str, Any]:
        return self._request("POST", "/ingest/run")

    def fetch_papers(self, *, limit: int = 25) -> list[dict[str, Any]]:
        return self._request("GET", "/papers/", params={"limit": limit})

    def fetch_paper_graph(self, external_id: str) -> dict[str, Any]:
        return self._request("GET", f"/papers/{external_id}/graph")

    def fetch_network(self, *, limit: int = 50) -> dict[str, Any]:
        return self._request("GET", "/graphs/network", params={"limit": limit})

    def fetch_pdf(self, external_id: str) -> bytes:
        return self._request("GET", f"/papers/{external_id}/pdf")

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def public_base_url(self) -> str:
        return self._public_base_url


@lru_cache
def get_backend_client() -> BackendClient:
    """Return a cached backend client instance."""

    return BackendClient()
