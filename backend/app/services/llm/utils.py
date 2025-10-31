"""Utility helpers shared across LLM clients."""

from __future__ import annotations

from pathlib import Path

from backend.app.schemas import PaperRecord

try:  # pragma: no cover - optional dependency guard during import time
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - handled gracefully when dependency missing
    PdfReader = None  # type: ignore[assignment]


def extract_pdf_excerpt(
    pdf_path: str | Path,
    *,
    max_pages: int = 12,
    max_characters: int = 20000,
) -> str:
    """Return a text excerpt from the provided PDF path.

    The function reads up to ``max_pages`` pages from the PDF and truncates the
    aggregated text to ``max_characters`` to keep prompts within model limits.
    If ``pypdf`` is not available or the PDF cannot be read, an empty string is
    returned so callers can degrade gracefully.
    """

    if PdfReader is None:
        return ""

    path = Path(pdf_path)
    if not path.exists():
        return ""

    try:
        reader = PdfReader(str(path))
    except Exception:  # pragma: no cover - defensive path for malformed PDFs
        return ""

    collected: list[str] = []
    total_chars = 0
    for index, page in enumerate(reader.pages):  # type: ignore[attr-defined]
        if index >= max_pages:
            break
        try:
            text = page.extract_text() or ""
        except Exception:  # pragma: no cover - defensive path per page
            continue
        if not text.strip():
            continue
        text = text.strip()
        collected.append(text)
        total_chars += len(text)
        if total_chars >= max_characters:
            break

    excerpt = "\n\n".join(collected)
    if len(excerpt) > max_characters:
        excerpt = excerpt[:max_characters]
    return excerpt


def build_structured_user_prompt(
    record: PaperRecord,
    *,
    pdf_excerpt: str | None = None,
) -> str:
    """Compose the user prompt shared by LLM clients.

    The prompt includes bibliographic metadata, the abstract (when available),
    and a trimmed excerpt of the PDF to encourage chapter-level fidelity.
    """

    metadata_lines: list[str] = [
        f"Title: {record.title}",
        f"Source: {record.source}",
        f"External ID: {record.external_id}",
    ]
    if record.authors:
        metadata_lines.append(f"Authors: {', '.join(record.authors)}")
    if record.published_at:
        metadata_lines.append(f"Published at: {record.published_at.isoformat()}")
    if record.tags:
        metadata_lines.append(f"Tags: {', '.join(record.tags)}")

    abstract = record.abstract or "Not provided"
    sections: list[str] = [
        "Paper metadata:\n" + "\n".join(metadata_lines),
        f"Abstract:\n{abstract}",
    ]
    if pdf_excerpt:
        sections.append("PDF excerpt (trimmed):\n" + pdf_excerpt.strip())

    guidance = (
        "Construct a meticulous chapter-by-chapter explanation of the paper. "
        "Organise the response into 4-7 sections that mirror the logical flow "
        "(problem framing, methodology, experiments, results, implications). "
        "Each chapter explanation must contain at least four sentences split "
        "across coherent paragraphs: begin by summarising the section's goal, "
        "then dive into concrete mechanisms (models, algorithms, datasets, "
        "training signals, evaluation setups), and conclude with the impact or "
        "design trade-offs. Explicitly mention terminology that should map to "
        "knowledge-graph concepts so downstream tooling can anchor nodes. "
        "When the excerpt lacks details, acknowledge the gap explicitly instead "
        "of fabricating content."
    )

    sections.append(guidance)
    sections.append(
        "Return a JSON object with fields summary (string), key_points (string[]), "
        "concepts ({name: string, description: string}[]), relationships ({source: "
        "string, target: string, relation: string}[]), and chapters ({title: "
        "string, explanation: string, related_concepts: (string | {label: string, "
        "node_type?: string, normalized?: string})[]}[])."
    )
    return "\n\n".join(sections)
