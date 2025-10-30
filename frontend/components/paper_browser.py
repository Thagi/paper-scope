"""Paper explorer and selection utilities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st


def render_paper_browser(
    papers: list[dict[str, Any]],
    *,
    selected_id: str | None,
) -> str | None:
    """Render a searchable browser to pick a paper."""

    st.subheader("Paper Explorer")
    if not papers:
        st.info("No papers available yet. Trigger ingestion to populate the catalog.")
        return None

    search = st.text_input(
        "Search by title, author, or concept",
        key="paper_search",
        placeholder="Graph neural networks",
    ).strip()
    available_tags = sorted(
        {tag for paper in papers for tag in paper.get("tags", []) if tag}
    )
    tag_filter = st.multiselect(
        "Filter by tag",
        available_tags,
        key="paper_tag_filter",
        placeholder="Select tags to narrow the list",
    )

    filtered = _filter_papers(papers, query=search, tags=set(tag_filter))
    sorted_papers = _sort_papers(
        filtered,
        key=st.selectbox(
            "Sort order",
            ("Newest", "Oldest", "Title"),
            key="paper_sort_order",
        ),
    )

    options = {_format_option(paper): paper["paper_id"] for paper in sorted_papers} or {
        "No matches": None
    }

    default_index = 0
    if selected_id and selected_id in options.values():
        default_index = list(options.values()).index(selected_id)

    selected_label = st.selectbox(
        "Select a paper",
        list(options.keys()),
        index=default_index,
        key="paper_selector",
    )
    st.caption(f"{len(filtered)} papers match the current filters.")

    preview_rows = [
        {
            "Title": paper.get("title", "Untitled"),
            "Authors": ", ".join(paper.get("authors", [])) or "Unknown",
            "Published": _format_datetime(paper.get("published_at")),
            "Tags": ", ".join(paper.get("tags", [])) or "—",
        }
        for paper in sorted_papers[:15]
    ]
    if preview_rows:
        st.dataframe(preview_rows, use_container_width=True, hide_index=True)

    return options.get(selected_label)


def _filter_papers(
    papers: list[dict[str, Any]],
    *,
    query: str,
    tags: set[str],
) -> list[dict[str, Any]]:
    """Return papers matching the provided search criteria."""

    if not query and not tags:
        return list(papers)

    lowered_query = query.lower()
    filtered: list[dict[str, Any]] = []
    for paper in papers:
        if tags and not tags.issubset(set(paper.get("tags", []))):
            continue
        if not query:
            filtered.append(paper)
            continue
        haystack = " ".join(
            [
                paper.get("title", ""),
                " ".join(paper.get("authors", [])),
                " ".join(paper.get("tags", [])),
            ]
        ).lower()
        if lowered_query in haystack:
            filtered.append(paper)
    return filtered


def _sort_papers(
    papers: list[dict[str, Any]],
    key: str,
) -> list[dict[str, Any]]:
    """Sort papers using the requested key."""

    if key == "Title":
        return sorted(papers, key=lambda item: item.get("title", "").lower())
    reverse = key == "Newest"
    return sorted(
        papers,
        key=lambda item: (
            _parse_datetime(item.get("published_at")) or datetime.min,
            item.get("title", "").lower(),
        ),
        reverse=reverse,
    )


def _format_option(paper: dict[str, Any]) -> str:
    """Return a human-readable label for the select box option."""

    title = paper.get("title", "Untitled")
    source = paper.get("source") or "unknown"
    published = _format_datetime(paper.get("published_at"))
    return f"{title} — {source} ({published})"


def _parse_datetime(value: Any) -> datetime | None:
    """Parse datetime-like values from Neo4j payloads."""

    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _format_datetime(value: Any) -> str:
    """Render a compact date string for UI consumption."""

    parsed = _parse_datetime(value)
    if not parsed:
        return "Unknown"
    return parsed.strftime("%Y-%m-%d")
