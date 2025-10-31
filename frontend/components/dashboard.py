"""Dashboard components for Paper Scope."""

from __future__ import annotations

import statistics
from typing import Any

import streamlit as st

from services.i18n import TranslationManager

def render_dashboard(
    papers: list[dict[str, Any]],
    *,
    last_ingestion: dict[str, Any] | None = None,
    translation: TranslationManager,
) -> None:
    """Render the high-level ingestion and trend dashboard widgets."""

    st.subheader(translation.gettext("dashboard.ingestion_overview"))
    cols = st.columns(3)
    total_sources = sorted({paper.get("source", "unknown") for paper in papers}) or [
        "N/A"
    ]
    last_status = last_ingestion.get("persisted") if last_ingestion else 0
    stats = [
        (translation.gettext("dashboard.tracked_papers"), str(len(papers))),
        (translation.gettext("dashboard.sources"), ", ".join(total_sources)),
        (translation.gettext("dashboard.last_run_persisted"), str(last_status)),
    ]
    for col, (label, value) in zip(cols, stats, strict=False):
        col.metric(label, value)

    if last_ingestion and last_ingestion.get("details"):
        with st.expander(
            translation.gettext("dashboard.last_ingestion_details"), expanded=False
        ):
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
        with st.expander(
            translation.gettext("dashboard.recent_highlights"), expanded=True
        ):
            st.write(
                translation.gettext("dashboard.newest_papers"),
                ", ".join(paper.get("title", "") for paper in papers[:3])
                if papers
                else translation.gettext("dashboard.no_recent_papers"),
            )
            if years:
                st.caption(
                    translation.gettext(
                        "dashboard.median_publication_year",
                        year=f"{statistics.median(years):.0f}",
                    )
                )
    else:
        st.info(translation.gettext("dashboard.no_papers"))
