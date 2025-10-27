"""Graph visualization placeholder component."""

from __future__ import annotations

import streamlit as st


def render_graph_overview() -> None:
    """Render the knowledge graph overview placeholder."""

    st.subheader("Knowledge Graph")
    st.write(
        "Interactive graph visualizations will appear here to illustrate relationships between papers, authors, and concepts."
    )
    st.info("Graph rendering integrations (pyvis/plotly) will be added in later phases.")
