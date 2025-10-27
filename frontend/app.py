"""Streamlit entrypoint for the Paper Scope frontend."""

from __future__ import annotations

import streamlit as st

from components.dashboard import render_dashboard
from components.pdf_viewer import render_pdf_viewer
from components.graphs import render_graph_overview


st.set_page_config(page_title="Paper Scope", layout="wide")

st.title("📚 Paper Scope")
st.caption("Monitor trending research, summarize insights, and explore knowledge graphs.")

with st.sidebar:
    st.header("Ingestion Controls")
    if st.button("Trigger Ingestion"):
        st.info("Ingestion trigger sent (placeholder).")
    st.divider()
    st.metric("Last Run", "Not yet scheduled")
    st.metric("Queued Jobs", "0")

render_dashboard()
st.divider()
render_pdf_viewer()
st.divider()
render_graph_overview()
