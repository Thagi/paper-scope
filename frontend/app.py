"""Streamlit entrypoint for the Paper Scope frontend."""

from __future__ import annotations

import streamlit as st

import httpx

from components.chapter_viewer import render_chapter_viewer
from components.dashboard import render_dashboard
from components.graphs import AUTO_FOCUS, render_graph_overview
from components.insights import render_insights
from components.paper_browser import render_paper_browser
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
if "graph_focus_selection" not in st.session_state:
    st.session_state["graph_focus_selection"] = AUTO_FOCUS
if "graph_focus_anchor" not in st.session_state:
    st.session_state["graph_focus_anchor"] = None


@st.cache_data(ttl=60)
def load_papers(limit: int = 25) -> list[dict]:
    return client.fetch_papers(limit=limit)


@st.cache_data(ttl=60)
def load_paper_graph(paper_id: str) -> dict:
    return client.fetch_paper_graph(paper_id)


@st.cache_data(ttl=300)
def load_network_graph(limit: int = 50) -> dict:
    return client.fetch_network(limit=limit)


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
if selected_id:
    try:
        paper_graph = load_paper_graph(selected_id)
    except httpx.HTTPError as exc:
        st.warning(i18n.gettext("load_paper_graph_warning", error=exc))

    current_anchor = st.session_state.get("graph_focus_anchor")
    if current_anchor != selected_id:
        st.session_state["graph_focus_selection"] = AUTO_FOCUS
        st.session_state["graph_focus_anchor"] = selected_id
else:
    st.session_state["graph_focus_selection"] = AUTO_FOCUS
    st.session_state["graph_focus_anchor"] = None

render_chapter_viewer(
    selected_paper,
    paper_graph=paper_graph,
    translation=i18n,
)

try:
    network_graph = load_network_graph()
except httpx.HTTPError as exc:
    st.warning(i18n.gettext("load_network_graph_warning", error=exc))
    network_graph = None

focus_selection = st.session_state.get("graph_focus_selection", AUTO_FOCUS)
updated_focus = render_graph_overview(
    paper_graph,
    network_graph,
    papers=papers,
    selected_paper_id=st.session_state.get("selected_paper_id"),
    focus_selection=focus_selection,
    translation=i18n,
)
if updated_focus != focus_selection:
    st.session_state["graph_focus_selection"] = updated_focus
