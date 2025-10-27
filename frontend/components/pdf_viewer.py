"""PDF viewer placeholder component."""

from __future__ import annotations

import streamlit as st


def render_pdf_viewer() -> None:
    """Render the PDF workspace placeholder."""

    st.subheader("PDF Workspace")
    st.write(
        "Select a paper to view its PDF and metadata. This section will embed a PDF viewer and LLM-generated summaries."
    )
    st.empty()
