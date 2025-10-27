"""CLI entrypoint for manual ingestion triggers."""

from __future__ import annotations

import typer

app = typer.Typer(help="Utilities for managing Paper Scope ingestion workflows.")


@app.command()
def once() -> None:
    """Trigger a single ingestion cycle (placeholder)."""

    typer.echo("Ingestion run would be triggered here once the pipeline is implemented.")


if __name__ == "__main__":
    app()
