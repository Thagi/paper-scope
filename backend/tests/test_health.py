"""Tests for the health endpoint."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from backend.app.main import app  # noqa: E402  pylint: disable=wrong-import-position


def test_health_endpoint_returns_ok() -> None:
    """Ensure the health endpoint responds with an OK status payload."""

    client = TestClient(app)
    response = client.get("/api/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
