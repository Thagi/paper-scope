"""Knowledge graph rendering utilities."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import networkx as nx
import plotly.graph_objects as go
import streamlit as st

from services.i18n import TranslationManager

def render_graph_overview(
    paper_graph: dict[str, Any] | None,
    network_graph: dict[str, Any] | None,
    *,
    papers: list[dict[str, Any]],
    selected_paper_id: str | None,
    translation: TranslationManager,
) -> None:
    """Render paper-level and cross-paper knowledge graphs."""

    st.subheader(translation.gettext("graph_overview.header"))
    if not paper_graph and not network_graph:
        st.info(translation.gettext("graph_overview.no_data"))
        return

    metrics = st.columns(3)
    metrics[0].metric(
        translation.gettext("graph_overview.paper_nodes"),
        _count_nodes(paper_graph, "Paper"),
    )
    metrics[1].metric(
        translation.gettext("graph_overview.concept_nodes"),
        _count_nodes(paper_graph, "Concept"),
    )
    metrics[2].metric(
        translation.gettext("graph_overview.cross_paper_links"),
        _count_edges(network_graph, "SHARES_CONCEPT"),
    )

    focus_paper_id = selected_paper_id or _find_primary_paper_id(paper_graph)
    selected_tab, network_tab = st.tabs(
        [
            translation.gettext("graph_overview.selected_tab"),
            translation.gettext("graph_overview.network_tab"),
        ]
    )

    with selected_tab:
        if paper_graph and paper_graph.get("nodes"):
            highlight = {focus_paper_id} if focus_paper_id else set()
            st.plotly_chart(
                _graph_to_figure(paper_graph, highlight_nodes=highlight),
                use_container_width=True,
            )
            concept_rows = _extract_concept_rows(paper_graph, focus_paper_id)
            if concept_rows:
                st.markdown(f"##### {translation.gettext('graph_overview.key_concepts')}")
                st.dataframe(concept_rows, hide_index=True, use_container_width=True)
        else:
            st.info(translation.gettext("graph_overview.select_paper_prompt"))

    with network_tab:
        if network_graph and network_graph.get("nodes"):
            highlight = _derive_network_highlight(network_graph, focus_paper_id)
            st.plotly_chart(
                _graph_to_figure(network_graph, highlight_nodes=highlight),
                use_container_width=True,
            )
            related = _extract_related_papers(network_graph, focus_paper_id, papers)
            if related:
                _render_related_papers(related, translation=translation)
            else:
                st.caption(translation.gettext("graph_overview.no_related"))
        else:
            st.info(translation.gettext("graph_overview.network_wait"))


def _graph_to_figure(
    graph: dict[str, Any],
    *,
    highlight_nodes: set[str] | None = None,
) -> go.Figure:
    """Convert a graph payload into a Plotly scatter network."""

    G = nx.Graph()
    for node in graph.get("nodes", []):
        node_id = node.get("id")
        if not node_id:
            continue
        G.add_node(node_id, **node)
    for edge in graph.get("edges", []):
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            continue
        G.add_edge(source, target, **edge)

    if not G.nodes:
        return go.Figure()

    pos = nx.spring_layout(G, seed=42, k=0.6 / max(len(G.nodes), 1))
    graph_nodes = set(G.nodes)
    highlight_nodes = (highlight_nodes or set()) & graph_nodes
    neighbor_nodes: set[str] = set()
    for node_id in highlight_nodes:
        neighbor_nodes.update(G.neighbors(node_id))

    edges_by_type: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for source, target, data in G.edges(data=True):
        edge_type = data.get("type", "RELATED")
        edges_by_type[edge_type].append((source, target))

    edge_style = {
        "RELATES_TO": {"color": "#2ca02c", "width": 1.0, "dash": None},
        "AUTHORED_BY": {"color": "#17becf", "width": 0.8, "dash": "dot"},
        "SHARES_CONCEPT": {"color": "#d62728", "width": 2.2, "dash": None},
    }

    edge_traces = []
    for edge_type, connections in edges_by_type.items():
        xs: list[float] = []
        ys: list[float] = []
        for source, target in connections:
            x0, y0 = pos[source]
            x1, y1 = pos[target]
            xs.extend([x0, x1, None])
            ys.extend([y0, y1, None])
        style = edge_style.get(edge_type, {"color": "#888", "width": 0.8, "dash": None})
        edge_traces.append(
            go.Scatter(
                x=xs,
                y=ys,
                line=dict(
                    width=style["width"], color=style["color"], dash=style["dash"]
                ),
                mode="lines",
                hoverinfo="none",
                name=edge_type.replace("_", " ").title(),
            )
        )

    node_x: list[float] = []
    node_y: list[float] = []
    hover_text: list[str] = []
    colors: list[str] = []
    sizes: list[float] = []

    base_colors = {"Paper": "#1f77b4", "Concept": "#ff7f0e", "Author": "#9467bd"}
    highlight_colors = {"Paper": "#d62728", "Concept": "#ff9896", "Author": "#c5b0d5"}
    neighbor_colors = {"Paper": "#9edae5", "Concept": "#c49c94", "Author": "#d7b5d8"}

    for node_id, data in G.nodes(data=True):
        x, y = pos[node_id]
        node_x.append(x)
        node_y.append(y)
        label = data.get("label", node_id)
        metadata = data.get("metadata") or {}
        meta_lines = [
            f"{key}: {value}"
            for key, value in metadata.items()
            if value not in (None, "", [])
        ]
        hover_text.append("<br>".join([label] + meta_lines))

        node_type = data.get("type")
        base_color = base_colors.get(node_type, "#7f7f7f")
        color = base_color
        size = 12.0
        if node_id in highlight_nodes:
            color = highlight_colors.get(node_type, "#ff9896")
            size = 16.0
        elif node_id in neighbor_nodes:
            color = neighbor_colors.get(node_type, base_color)
            size = 13.0
        colors.append(color)
        sizes.append(size)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        marker=dict(size=sizes, color=colors, line=dict(width=2, color="#FFFFFF")),
        hoverinfo="text",
        hovertext=hover_text,
        showlegend=False,
    )

    fig = go.Figure(data=[*edge_traces, node_trace])
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="#f8f9fa",
    )
    return fig


def _extract_concept_rows(
    paper_graph: dict[str, Any] | None,
    focus_paper_id: str | None,
) -> list[dict[str, Any]]:
    """Build a table summarising key concepts for the selected paper."""

    if not paper_graph:
        return []

    nodes = {node.get("id"): node for node in paper_graph.get("nodes", [])}
    if not nodes:
        return []

    paper_id = focus_paper_id or _find_primary_paper_id(paper_graph)
    if not paper_id:
        return []

    concept_rows: dict[str, dict[str, Any]] = {}
    for edge in paper_graph.get("edges", []):
        if edge.get("source") != paper_id:
            continue
        target_id = edge.get("target")
        target_node = nodes.get(target_id)
        if not target_node or target_node.get("type") != "Concept":
            continue

        relations = edge.get("metadata", {}).get("relations")
        if not relations:
            relation_value = edge.get("metadata", {}).get("relation") or edge.get(
                "type"
            )
            relations = [relation_value] if relation_value else []

        entry = concept_rows.setdefault(
            target_id,
            {
                "Concept": target_node.get("label"),
                "Relations": set(),
                "Description": (target_node.get("metadata") or {}).get(
                    "description", ""
                ),
            },
        )
        entry["Relations"].update(relations)

    result: list[dict[str, Any]] = []
    for row in concept_rows.values():
        relations = (
            ", ".join(sorted(rel for rel in row["Relations"] if rel)) or "Related"
        )
        result.append(
            {
                "Concept": row["Concept"],
                "Relation": relations,
                "Description": row["Description"],
            }
        )
    return result


def _extract_related_papers(
    network_graph: dict[str, Any] | None,
    focus_paper_id: str | None,
    papers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return related papers linked through shared concepts."""

    if not network_graph or not focus_paper_id:
        return []

    nodes = {node.get("id"): node for node in network_graph.get("nodes", [])}
    paper_lookup = {paper.get("paper_id"): paper for paper in papers}

    related: list[dict[str, Any]] = []
    seen: set[str] = set()
    for edge in network_graph.get("edges", []):
        if edge.get("type") != "SHARES_CONCEPT":
            continue
        source = edge.get("source")
        target = edge.get("target")
        if focus_paper_id not in (source, target):
            continue
        other_id = target if source == focus_paper_id else source
        if not other_id or other_id in seen:
            continue
        seen.add(other_id)

        node_payload = nodes.get(other_id, {})
        paper_payload = paper_lookup.get(other_id, {})
        metadata = edge.get("metadata", {})
        shared_concepts = metadata.get("shared_concepts") or []
        weight = metadata.get("weight") or len(shared_concepts)

        related.append(
            {
                "paper_id": other_id,
                "title": paper_payload.get("title")
                or node_payload.get("label")
                or other_id,
                "summary": paper_payload.get("summary")
                or (node_payload.get("metadata") or {}).get("summary"),
                "shared_concepts": shared_concepts,
                "weight": weight,
                "published_at": paper_payload.get("published_at")
                or (node_payload.get("metadata") or {}).get("published_at"),
                "landing_url": paper_payload.get("landing_url")
                or (node_payload.get("metadata") or {}).get("landing_url"),
            }
        )

    related.sort(key=lambda item: item["weight"], reverse=True)
    return related[:8]


def _render_related_papers(
    related: list[dict[str, Any]], *, translation: TranslationManager
) -> None:
    """Render a list of related papers with quick actions."""

    st.markdown(f"##### {translation.gettext('graph_overview.related_papers')}")
    for entry in related:
        shared_concepts = ", ".join(entry.get("shared_concepts") or []) or translation.gettext(
            "paper_browser.no_tags"
        )
        published = entry.get("published_at") or translation.gettext(
            "paper_browser.unknown_published"
        )
        if published == "Unknown":
            published = translation.gettext("paper_browser.unknown_published")
        with st.container():
            st.markdown(f"**{entry['title']}**")
            st.caption(
                translation.gettext(
                    "graph_overview.published_caption",
                    published=published,
                    weight=entry["weight"],
                    concepts=shared_concepts,
                )
            )
            if entry.get("summary"):
                st.write(translation.translate_text(entry["summary"]))
            cols = st.columns([3, 1])
            with cols[0]:
                if entry.get("landing_url"):
                    st.link_button(
                        translation.gettext("graph_overview.open_landing_page"),
                        entry["landing_url"],
                        key=f"landing_{entry['paper_id']}",
                    )
            with cols[1]:
                if st.button(
                    translation.gettext("graph_overview.focus_in_app"),
                    key=f"focus_{entry['paper_id']}",
                ):
                    st.session_state["selected_paper_id"] = entry["paper_id"]
                    st.experimental_rerun()


def _count_nodes(graph: dict[str, Any] | None, node_type: str) -> int:
    """Count nodes of a given type inside a graph payload."""

    if not graph:
        return 0
    return sum(1 for node in graph.get("nodes", []) if node.get("type") == node_type)


def _count_edges(graph: dict[str, Any] | None, edge_type: str) -> int:
    """Count edges of a given type inside a graph payload."""

    if not graph:
        return 0
    return sum(1 for edge in graph.get("edges", []) if edge.get("type") == edge_type)


def _derive_network_highlight(
    network_graph: dict[str, Any] | None,
    focus_paper_id: str | None,
) -> set[str]:
    """Return nodes to highlight in the network graph."""

    if not network_graph or not focus_paper_id:
        return set()
    highlight = {focus_paper_id}
    for edge in network_graph.get("edges", []):
        if focus_paper_id == edge.get("source"):
            highlight.add(edge.get("target"))
        elif focus_paper_id == edge.get("target"):
            highlight.add(edge.get("source"))
    return {node_id for node_id in highlight if node_id}


def _find_primary_paper_id(graph: dict[str, Any] | None) -> str | None:
    """Return the identifier of the first paper node inside the graph."""

    if not graph:
        return None
    for node in graph.get("nodes", []):
        if node.get("type") == "Paper":
            return node.get("id")
    return None
