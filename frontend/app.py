"""Streamlit entrypoint for the Paper Scope frontend."""

from __future__ import annotations

import httpx
import streamlit as st

from components.dashboard import render_dashboard
from components.pdf_viewer import render_pdf_viewer
from components.graphs import render_graph_overview
from services.backend import get_backend_client


st.set_page_config(page_title="Paper Scope", layout="wide")
client = get_backend_client()

if "selected_paper" not in st.session_state:
    st.session_state["selected_paper"] = None
if "last_ingestion" not in st.session_state:
    st.session_state["last_ingestion"] = None


@st.cache_data(ttl=60)
def load_papers(limit: int = 25) -> list[dict]:
    return client.fetch_papers(limit=limit)


@st.cache_data(ttl=60)
def load_paper_graph(paper_id: str) -> dict:
    return client.fetch_paper_graph(paper_id)


@st.cache_data(ttl=300)
def load_network_graph(limit: int = 50) -> dict:
    return client.fetch_network(limit=limit)


@st.cache_data(ttl=600)
def load_pdf_bytes(paper_id: str) -> bytes | None:
    try:
        return client.fetch_pdf(paper_id)
    except httpx.HTTPError:
        return None


st.title("📚 Paper Scope")
st.caption("Monitor trending research, summarize insights, and explore knowledge graphs.")

with st.sidebar:
    st.header("Ingestion Controls")
    if st.button("Trigger Ingestion"):
        with st.spinner("Running ingestion pipeline..."):
            try:
                result = client.trigger_ingestion()
                st.session_state["last_ingestion"] = result
                st.success("Ingestion completed successfully.")
                load_papers.clear()
                load_network_graph.clear()
                load_paper_graph.clear()
                load_pdf_bytes.clear()
            except httpx.HTTPError as exc:
                st.error(f"Failed to trigger ingestion: {exc}")
    st.divider()
    last_run = st.session_state.get("last_ingestion")
    if last_run:
        st.metric("Last Persisted", last_run.get("persisted", 0))
    else:
        st.metric("Last Persisted", "—")

try:
    papers = load_papers()
except httpx.HTTPError as exc:
    st.error(f"Unable to load papers: {exc}")
    papers = []

render_dashboard(papers, last_ingestion=st.session_state.get("last_ingestion"))

paper_options = {paper["title"]: paper["paper_id"] for paper in papers}
selected_label = st.selectbox("Select a paper", list(paper_options.keys()) or ["None"], index=0)
selected_id = paper_options.get(selected_label)
selected_paper = next((paper for paper in papers if paper["paper_id"] == selected_id), None)
st.session_state["selected_paper"] = selected_paper

paper_graph = None
pdf_url = None
pdf_bytes = None
if selected_id:
    try:
        paper_graph = load_paper_graph(selected_id)
    except httpx.HTTPError as exc:
        st.warning(f"Could not load paper graph: {exc}")
    pdf_url = f"{client.public_base_url}/papers/{selected_id}/pdf"
    pdf_bytes = load_pdf_bytes(selected_id)

render_pdf_viewer(selected_paper, pdf_url=pdf_url, pdf_bytes=pdf_bytes)

try:
    network_graph = load_network_graph()
except httpx.HTTPError as exc:
    st.warning(f"Unable to load network graph: {exc}")
    network_graph = None

render_graph_overview(paper_graph, network_graph)
