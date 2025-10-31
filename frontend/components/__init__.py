"""Reusable Streamlit components for Paper Scope."""

from __future__ import annotations

from .chapter_viewer import render_chapter_viewer
from .dashboard import render_dashboard
from .graphs import AUTO_FOCUS, render_graph_overview
from .insights import render_insights
from .paper_browser import render_paper_browser

__all__ = [
    "AUTO_FOCUS",
    "render_chapter_viewer",
    "render_dashboard",
    "render_graph_overview",
    "render_insights",
    "render_paper_browser",
]
