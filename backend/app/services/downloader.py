"""Utility for downloading PDF assets."""

from __future__ import annotations

from pathlib import Path

import httpx


class PDFDownloader:
    """Download PDF files with retry-aware semantics."""

    def __init__(self, *, timeout: float = 60.0) -> None:
        self._timeout = timeout

    async def download(self, url: str, destination: Path) -> Path:
        """Download a PDF file to the destination path.

        Args:
            url: The remote PDF URL.
            destination: Path where the PDF will be stored.

        Returns:
            Path: The destination path for the downloaded file.
        """

        destination.parent.mkdir(parents=True, exist_ok=True)
        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            destination.write_bytes(response.content)
        return destination
