"""Streamlit entrypoint for the Paper Scope frontend."""

from __future__ import annotations

import httpx
import streamlit as st

from components.dashboard import render_dashboard
from components.graphs import render_graph_overview
from components.insights import render_insights
from components.paper_browser import render_paper_browser
from components.pdf_viewer import render_pdf_viewer
from services.backend import get_backend_client
from services.i18n import (
    SUPPORTED_LANGUAGES,
    get_translation_manager,
    set_language,
)


st.set_page_config(page_title="Paper Scope", layout="wide")
client = get_backend_client()

if "selected_paper" not in st.session_state:
    st.session_state["selected_paper"] = None
if "selected_paper_id" not in st.session_state:
    st.session_state["selected_paper_id"] = None
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


if "language" not in st.session_state:
    st.session_state["language"] = "ja"

i18n = get_translation_manager()

st.title(i18n.gettext("app.title"))
st.caption(i18n.gettext("app.caption"))

with st.sidebar:
    language_codes = list(SUPPORTED_LANGUAGES)
    selected_language = st.selectbox(
        i18n.gettext("sidebar.language"),
        language_codes,
        index=language_codes.index(i18n.language),
        format_func=lambda code: SUPPORTED_LANGUAGES[code],
    )
    if selected_language != i18n.language:
        set_language(selected_language)
        st.experimental_rerun()

    st.header(i18n.gettext("sidebar.ingestion_header"))
    if st.button(i18n.gettext("sidebar.trigger_ingestion")):
        with st.spinner(i18n.gettext("sidebar.trigger_ingestion_running")):
            try:
                result = client.trigger_ingestion()
                st.session_state["last_ingestion"] = result
                st.success(i18n.gettext("sidebar.trigger_ingestion_success"))
                load_papers.clear()
                load_network_graph.clear()
                load_paper_graph.clear()
                load_pdf_bytes.clear()
            except httpx.HTTPError as exc:
                st.error(i18n.gettext("sidebar.trigger_ingestion_failure", error=exc))
    st.divider()
    last_run = st.session_state.get("last_ingestion")
    metric_label = i18n.gettext("sidebar.last_persisted")
    if last_run:
        st.metric(metric_label, last_run.get("persisted", 0))
    else:
        st.metric(metric_label, "—")

try:
    papers = load_papers()
except httpx.HTTPError as exc:
    st.error(i18n.gettext("load_papers_error", error=exc))
    papers = []

render_dashboard(
    papers,
    last_ingestion=st.session_state.get("last_ingestion"),
    translation=i18n,
)
render_insights(papers, translation=i18n)

selected_id = render_paper_browser(
    papers,
    selected_id=st.session_state.get("selected_paper_id"),
    translation=i18n,
)
st.session_state["selected_paper_id"] = selected_id
selected_paper = next(
    (paper for paper in papers if paper.get("paper_id") == selected_id), None
)
st.session_state["selected_paper"] = selected_paper

paper_graph = None
pdf_url = None
pdf_bytes = None
if selected_id:
    try:
        paper_graph = load_paper_graph(selected_id)
    except httpx.HTTPError as exc:
        st.warning(i18n.gettext("load_paper_graph_warning", error=exc))
    pdf_url = f"{client.public_base_url}/papers/{selected_id}/pdf"
    pdf_bytes = load_pdf_bytes(selected_id)

render_pdf_viewer(
    selected_paper,
    pdf_url=pdf_url,
    pdf_bytes=pdf_bytes,
    translation=i18n,
)

try:
    network_graph = load_network_graph()
except httpx.HTTPError as exc:
        st.warning(i18n.gettext("load_network_graph_warning", error=exc))
        network_graph = None

render_graph_overview(
    paper_graph,
    network_graph,
    papers=papers,
    selected_paper_id=st.session_state.get("selected_paper_id"),
    translation=i18n,
)
