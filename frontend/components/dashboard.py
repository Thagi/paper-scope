"""Dashboard components for Paper Scope."""

from __future__ import annotations

import streamlit as st


def render_dashboard() -> None:
    """Render the high-level ingestion and trend dashboard widgets."""

    st.subheader("Ingestion Overview")
    cols = st.columns(3)
    stats = [
        ("Papers Ingested", "0"),
        ("Sources", "Hugging Face, arXiv"),
        ("Last Updated", "Not yet run"),
    ]
    for col, (label, value) in zip(cols, stats, strict=False):
        col.metric(label, value)

    st.info(
        "This dashboard will display ingestion status, trends, and recent enrichments as the backend evolves."
    )
