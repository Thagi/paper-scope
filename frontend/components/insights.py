"""Insight widgets for Paper Scope library data."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from services.i18n import TranslationManager

def render_insights(papers: list[dict[str, Any]], *, translation: TranslationManager) -> None:
    """Render analytics about the currently ingested papers."""

    st.subheader(translation.gettext("insights.library_insights"))
    if not papers:
        st.info(translation.gettext("insights.no_papers"))
        return

    total = len(papers)
    with_tags = sum(1 for paper in papers if paper.get("tags"))
    with_summaries = sum(1 for paper in papers if paper.get("summary"))
    with_pdfs = sum(1 for paper in papers if paper.get("storage_path"))

    coverage_cols = st.columns(3)
    coverage_cols[0].metric(
        translation.gettext("insights.tagged_papers"),
        f"{with_tags}/{total}",
        delta=
        translation.gettext(
            "insights.coverage_delta", percentage=(with_tags / total * 100)
        )
        if total
        else None,
    )
    coverage_cols[1].metric(
        translation.gettext("insights.summaries_available"),
        f"{with_summaries}/{total}",
        delta=
        translation.gettext(
            "insights.coverage_delta", percentage=(with_summaries / total * 100)
        )
        if total
        else None,
    )
    coverage_cols[2].metric(
        translation.gettext("insights.pdfs_stored"),
        f"{with_pdfs}/{total}",
        delta=
        translation.gettext(
            "insights.coverage_delta", percentage=(with_pdfs / total * 100)
        )
        if total
        else None,
    )

    top_tags = _build_top_tags(papers)
    top_authors = _build_top_authors(papers)
    timeline = _build_publication_timeline(papers)

    charts = st.columns(2)
    with charts[0]:
        if top_tags.empty:
            st.caption(translation.gettext("insights.tags_caption"))
        else:
            fig = px.bar(
                top_tags,
                x="count",
                y="tag",
                orientation="h",
                labels={
                    "tag": translation.gettext("insights.tag_label"),
                    "count": translation.gettext("insights.count_label"),
                },
                title=translation.gettext("insights.top_tags"),
            )
            fig.update_layout(margin=dict(l=0, r=10, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with charts[1]:
        if timeline.empty:
            st.caption(translation.gettext("insights.timeline_caption"))
        else:
            fig = px.line(
                timeline,
                x="year",
                y="count",
                markers=True,
                labels={
                    "year": translation.gettext("insights.year_label"),
                    "count": translation.gettext("insights.count_label"),
                },
                title=translation.gettext("insights.timeline_title"),
            )
            fig.update_layout(margin=dict(l=10, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)

    if not top_authors.empty:
        st.markdown(f"##### {translation.gettext('insights.prolific_authors')}")
        st.dataframe(top_authors, hide_index=True, use_container_width=True)
    else:
        st.caption(translation.gettext("insights.authors_caption"))


def _build_top_tags(papers: list[dict[str, Any]]) -> pd.DataFrame:
    """Return the top tags ranked by paper count."""

    tag_counts: Counter[str] = Counter()
    for paper in papers:
        tag_counts.update(tag for tag in paper.get("tags", []) if tag)
    if not tag_counts:
        return pd.DataFrame(columns=["tag", "count"])
    most_common = tag_counts.most_common(10)
    df = pd.DataFrame(most_common, columns=["tag", "count"])
    return df.sort_values("count", ascending=True)


def _build_top_authors(papers: list[dict[str, Any]]) -> pd.DataFrame:
    """Return the top authors ranked by paper count."""

    author_counts: Counter[str] = Counter()
    for paper in papers:
        author_counts.update(author for author in paper.get("authors", []) if author)
    if not author_counts:
        return pd.DataFrame(columns=["Author", "Papers"])
    most_common = author_counts.most_common(8)
    df = pd.DataFrame(most_common, columns=["Author", "Papers"])
    return df


def _build_publication_timeline(papers: list[dict[str, Any]]) -> pd.DataFrame:
    """Return a time series of paper counts per publication year."""

    year_counts: Counter[int] = Counter()
    for paper in papers:
        year = _extract_year(paper.get("published_at"))
        if year:
            year_counts.update([year])
    if not year_counts:
        return pd.DataFrame(columns=["year", "count"])
    data = sorted(year_counts.items())
    return pd.DataFrame(data, columns=["year", "count"])


def _extract_year(value: Any) -> int | None:
    """Attempt to extract a publication year from a metadata value."""

    if value is None:
        return None
    if isinstance(value, datetime):
        return value.year
    if isinstance(value, str):
        try:
            if len(value) >= 4:
                return int(value[:4])
        except ValueError:
            return None
    return None
