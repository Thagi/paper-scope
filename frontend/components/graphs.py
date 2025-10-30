"""Graph visualization placeholder component."""

from __future__ import annotations

from typing import Any

import networkx as nx
import plotly.graph_objects as go
import streamlit as st


def render_graph_overview(
    paper_graph: dict[str, Any] | None,
    network_graph: dict[str, Any] | None,
) -> None:
    """Render paper-level and cross-paper knowledge graphs."""

    st.subheader("Knowledge Graph")
    cols = st.columns(2)
    with cols[0]:
        st.markdown("#### Selected Paper Graph")
        if paper_graph and paper_graph.get("nodes"):
            st.plotly_chart(_graph_to_figure(paper_graph), use_container_width=True)
        else:
            st.info("Select a paper to view its concept graph.")

    with cols[1]:
        st.markdown("#### Cross-Paper Network")
        if network_graph and network_graph.get("nodes"):
            st.plotly_chart(_graph_to_figure(network_graph), use_container_width=True)
        else:
            st.info("Network data will appear after multiple papers share concepts.")


def _graph_to_figure(graph: dict[str, Any]) -> go.Figure:
    """Convert a graph payload into a Plotly scatter network."""

    G = nx.Graph()
    for node in graph.get("nodes", []):
        G.add_node(node["id"], label=node.get("label"), type=node.get("type"))
    for edge in graph.get("edges", []):
        G.add_edge(edge["source"], edge["target"], relation=edge.get("type"))

    if not G.nodes:
        return go.Figure()

    pos = nx.spring_layout(G, seed=42)
    edge_x = []
    edge_y = []
    for source, target in G.edges():
        x0, y0 = pos[source]
        x1, y1 = pos[target]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5, color="#888"), mode="lines")

    node_x = []
    node_y = []
    text = []
    colors = []
    color_map = {"Paper": "#1f77b4", "Concept": "#ff7f0e", "Author": "#2ca02c"}
    for node_id, data in G.nodes(data=True):
        x, y = pos[node_id]
        node_x.append(x)
        node_y.append(y)
        text.append(data.get("label", node_id))
        colors.append(color_map.get(data.get("type"), "#7f7f7f"))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        marker=dict(size=12, color=colors, line=dict(width=2, color="#FFFFFF")),
        text=text,
        hoverinfo="text",
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
    return fig
