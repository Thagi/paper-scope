"""CLI entrypoint for manual ingestion triggers."""

from __future__ import annotations

import os
from typing import Annotated

import httpx
import typer

DEFAULT_API_BASE = os.getenv("PAPER_SCOPE_BACKEND_URL", "http://localhost:8000/api")

app = typer.Typer(help="Utilities for managing Paper Scope ingestion workflows.")


def _trigger_ingestion(api_base: str) -> dict:
    with httpx.Client(timeout=30.0) as client:
        response = client.post(f"{api_base.rstrip('/')}/ingest/run")
        response.raise_for_status()
        return response.json()


@app.command()
def once(
    api_base: Annotated[str, typer.Option(help="Base URL of the Paper Scope backend API.")] = DEFAULT_API_BASE,
) -> None:
    """Trigger a single ingestion cycle via the FastAPI backend."""

    typer.echo(f"Triggering ingestion using backend at {api_base} ...")
    try:
        result = _trigger_ingestion(api_base)
    except httpx.HTTPError as exc:  # pragma: no cover - network interactions
        typer.secho(f"Failed to trigger ingestion: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho("Ingestion completed.", fg=typer.colors.GREEN)
    typer.echo(result)


if __name__ == "__main__":
    app()
