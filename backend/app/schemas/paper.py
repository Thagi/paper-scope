"""Schemas describing papers and enrichment payloads."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class PaperRecord(BaseModel):
    """Metadata describing a paper discovered during ingestion."""

    external_id: str = Field(..., description="Canonical identifier (e.g., arXiv ID).")
    source: str = Field(..., description="Ingestion source identifier (huggingface, arxiv, etc.).")
    title: str = Field(..., description="Title of the paper.")
    abstract: str | None = Field(default=None, description="Abstract or summary text.")
    authors: list[str] = Field(default_factory=list, description="List of author names.")
    pdf_url: HttpUrl = Field(..., description="URL to download the paper PDF.")
    landing_url: HttpUrl | None = Field(default=None, description="Human-friendly landing page for the paper.")
    published_at: datetime | None = Field(default=None, description="Publication timestamp when available.")
    tags: list[str] = Field(default_factory=list, description="Categorical tags for the paper.")

    def storage_key(self) -> str:
        """Generate a filesystem-friendly key for storage paths."""

        return self.external_id.replace("/", "-")


class LLMConcept(BaseModel):
    """Concept extracted from the paper."""

    name: str
    description: str | None = None


class LLMRelationship(BaseModel):
    """Relationship triple derived from the paper."""

    source: str
    target: str
    relation: str


class LLMAnalysis(BaseModel):
    """LLM generated insights for a paper."""

    summary: str = Field(..., description="High-level summary text.")
    key_points: list[str] = Field(default_factory=list, description="Key bullet point highlights.")
    concepts: list[LLMConcept] = Field(default_factory=list, description="Extracted concepts.")
    relationships: list[LLMRelationship] = Field(default_factory=list, description="Graph relationships.")


class PaperIngestionResult(BaseModel):
    """Result payload returned after an ingestion run."""

    discovered: int = Field(..., description="Total papers discovered from sources.")
    downloaded: int = Field(..., description="Number of PDFs downloaded in this run.")
    enriched: int = Field(..., description="Number of papers enriched via LLM.")
    persisted: int = Field(..., description="Number of papers persisted to the graph database.")
    manual_trigger: bool = Field(default=False, description="Whether the run was manually triggered.")
    details: list[dict[str, Any]] = Field(default_factory=list, description="Per-paper diagnostic details.")


class StoredPaper(BaseModel):
    """Representation of a paper stored in the graph for frontend consumption."""

    paper_id: str = Field(..., description="Graph identifier for the paper.")
    title: str
    source: str | None = None
    summary: str | None = None
    landing_url: HttpUrl | None = None
    tags: list[str] = Field(default_factory=list)
    authors: list[str] = Field(default_factory=list)
    published_at: datetime | None = None
    storage_path: Path | None = None
    key_points: list[str] = Field(default_factory=list)


class GraphNode(BaseModel):
    """Node representation for knowledge graph visualizations."""

    id: str
    label: str
    type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Edge representation for knowledge graph visualizations."""

    id: str
    source: str
    target: str
    type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class PaperGraph(BaseModel):
    """Full graph payload for a specific paper."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
