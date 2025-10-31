"""Pydantic schemas for Paper Scope."""

from __future__ import annotations

from .paper import (
    ChapterConcept,
    GraphEdge,
    GraphNode,
    LLMAnalysis,
    LLMChapter,
    LLMConcept,
    LLMRelationship,
    PaperGraph,
    PaperIngestionResult,
    PaperRecord,
    StoredPaper,
)

__all__ = [
    "ChapterConcept",
    "GraphEdge",
    "GraphNode",
    "LLMAnalysis",
    "LLMChapter",
    "LLMConcept",
    "LLMRelationship",
    "PaperGraph",
    "PaperIngestionResult",
    "PaperRecord",
    "StoredPaper",
]
