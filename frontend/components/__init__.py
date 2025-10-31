"""Reusable Streamlit components for Paper Scope."""

from __future__ import annotations

from .dashboard import render_dashboard
from .graphs import render_graph_overview
from .insights import render_insights
from .paper_browser import render_paper_browser
from .pdf_viewer import render_pdf_viewer

__all__ = [
    "render_dashboard",
    "render_graph_overview",
    "render_insights",
    "render_paper_browser",
    "render_pdf_viewer",
]
