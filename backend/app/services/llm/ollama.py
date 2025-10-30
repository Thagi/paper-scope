"""Ollama powered LLM client."""

from __future__ import annotations

import json

import httpx

from backend.app.schemas import LLMAnalysis, LLMConcept, LLMRelationship, PaperRecord

from .base import LLMClient


class OllamaLLMClient(LLMClient):
    """Client that communicates with a locally hosted Ollama server."""

    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def analyze(self, record: PaperRecord, *, pdf_path: str | None = None) -> LLMAnalysis:
        prompt = (
            "Return JSON with fields summary, key_points, concepts, relationships summarizing the following paper.\n"
            f"Title: {record.title}\n"
            f"Authors: {', '.join(record.authors) if record.authors else 'Unknown'}\n"
            f"Abstract: {record.abstract or 'Not provided'}\n"
        )
        payload = {
            "model": self._model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self._base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()

        content = data.get("response") or data.get("message", {}).get("content")
        if not content:
            raise RuntimeError("Ollama response missing content")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:  # pragma: no cover - runtime safeguard
            raise RuntimeError("Ollama response was not valid JSON") from exc
        key_points = [str(item) for item in parsed.get("key_points", [])]
        concepts = [
            LLMConcept(name=item.get("name", ""), description=item.get("description"))
            for item in parsed.get("concepts", [])
            if item.get("name")
        ]
        relationships = [
            LLMRelationship(
                source=item.get("source", record.external_id),
                target=item.get("target", ""),
                relation=item.get("relation", "RELATES_TO"),
            )
            for item in parsed.get("relationships", [])
            if item.get("target")
        ]
        summary = parsed.get("summary") or record.abstract or record.title
        return LLMAnalysis(
            summary=summary,
            key_points=key_points,
            concepts=concepts,
            relationships=relationships,
        )
