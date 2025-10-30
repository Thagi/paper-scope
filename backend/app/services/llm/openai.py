"""OpenAI powered LLM client."""

from __future__ import annotations

import json

import httpx

from backend.app.schemas import LLMAnalysis, LLMConcept, LLMRelationship, PaperRecord

from .base import LLMClient


class OpenAILLMClient(LLMClient):
    """LLM client that communicates with OpenAI's chat completion API."""

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("OpenAI API key must be provided for OpenAI LLM client.")
        self._api_key = api_key
        self._model = model
        self._endpoint = "https://api.openai.com/v1/chat/completions"

    async def analyze(self, record: PaperRecord, *, pdf_path: str | None = None) -> LLMAnalysis:
        system_prompt = (
            "You are a research assistant that writes concise JSON summaries for academic papers. "
            "Always return valid JSON matching the schema {summary: string, key_points: string[], "
            "concepts: {name: string, description: string}[], relationships: {source: string, target: string, relation: string}[]}."
        )
        user_prompt = (
            f"Title: {record.title}\n"
            f"Source: {record.source}\n"
            f"Authors: {', '.join(record.authors) if record.authors else 'Unknown'}\n"
            f"Abstract: {record.abstract or 'Not provided'}\n"
            "Return a structured JSON summary."
        )
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self._endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:  # pragma: no cover - network variability
            raise RuntimeError("OpenAI response was not valid JSON") from exc
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
