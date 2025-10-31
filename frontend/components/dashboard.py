"""Dashboard components for Paper Scope."""

from __future__ import annotations

import statistics
from typing import Any

import streamlit as st


def render_dashboard(
    papers: list[dict[str, Any]],
    *,
    last_ingestion: dict[str, Any] | None = None,
) -> None:
    """Render the high-level ingestion and trend dashboard widgets."""

    st.subheader("Ingestion Overview")
    cols = st.columns(3)
    total_sources = sorted({paper.get("source", "unknown") for paper in papers}) or [
        "N/A"
    ]
    last_status = last_ingestion.get("persisted") if last_ingestion else 0
    stats = [
        ("Tracked Papers", str(len(papers))),
        ("Sources", ", ".join(total_sources)),
        ("Last Run Persisted", str(last_status)),
    ]
    for col, (label, value) in zip(cols, stats, strict=False):
        col.metric(label, value)

    if last_ingestion and last_ingestion.get("details"):
        with st.expander("Last Ingestion Details", expanded=False):
            st.write(last_ingestion["details"])

    if papers:
        years: list[int] = []
        for paper in papers:
            published = paper.get("published_at")
            if not published:
                continue
            if isinstance(published, str):
                years.append(int(published[:4]))
            else:
                years.append(int(str(published)[:4]))
        with st.expander("Recent Paper Highlights", expanded=True):
            st.write(
                "Newest Papers:",
                ", ".join(paper.get("title", "") for paper in papers[:3])
                if papers
                else "None",
            )
            if years:
                st.caption(f"Median publication year: {statistics.median(years):.0f}")
    else:
        st.info(
            "No ingested papers yet. Trigger an ingestion run to populate the knowledge graph."
        )
