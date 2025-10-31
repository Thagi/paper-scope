"""Knowledge graph rendering utilities."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import networkx as nx
import plotly.graph_objects as go
import streamlit as st

from services.i18n import TranslationManager

AUTO_FOCUS = "__AUTO__"


def render_graph_overview(
    paper_graph: dict[str, Any] | None,
    network_graph: dict[str, Any] | None,
    *,
    papers: list[dict[str, Any]],
    selected_paper_id: str | None,
    focus_selection: str,
    translation: TranslationManager,
) -> tuple[str, str | None]:
    """Render paper-level and cross-paper knowledge graphs.

    Returns a tuple containing the active focus selection and an optional
    paper identifier that should become the newly selected paper when a related
    node is chosen from the focus panel.
    """

    st.subheader(translation.gettext("graph_overview.header"))
    if not paper_graph and not network_graph:
        st.info(translation.gettext("graph_overview.no_data"))
        return focus_selection, None

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
    node_lookup = _collect_focus_nodes(paper_graph, network_graph)
    focus_options = [AUTO_FOCUS]
    focus_options.extend(
        sorted(
            node_lookup,
            key=lambda node_id: node_lookup[node_id]["label"].casefold(),
        )
    )

    if focus_selection not in focus_options:
        focus_selection = AUTO_FOCUS
    default_focus = focus_paper_id if focus_paper_id in node_lookup else None
    selected_option = st.selectbox(
        translation.gettext("graph_overview.focus_selector"),
        focus_options,
        index=focus_options.index(focus_selection),
        format_func=lambda option: _format_focus_option(
            option, node_lookup, translation, default_focus
        ),
    )
    st.caption(translation.gettext("graph_overview.instructions"))

    focus_node_id = default_focus if selected_option == AUTO_FOCUS else selected_option
    requested_paper_id: str | None = None

    selected_tab, network_tab = st.tabs(
        [
            translation.gettext("graph_overview.selected_tab"),
            translation.gettext("graph_overview.network_tab"),
        ]
    )

    with selected_tab:
        if paper_graph and paper_graph.get("nodes"):
            highlight_target = (
                focus_node_id
                if focus_node_id and _node_in_graph(paper_graph, focus_node_id)
                else focus_paper_id
            )
            highlight = {highlight_target} if highlight_target else set()
            st.plotly_chart(
                _graph_to_figure(paper_graph, highlight_nodes=highlight),
                use_container_width=True,
            )
            concept_rows = _extract_concept_rows(paper_graph, focus_paper_id)
            if concept_rows:
                st.markdown(
                    f"##### {translation.gettext('graph_overview.key_concepts')}"
                )
                st.dataframe(concept_rows, hide_index=True, use_container_width=True)
            focus_request = _render_focus_details(
                paper_graph,
                network_graph,
                focus_node_id,
                translation=translation,
            )
            if not requested_paper_id:
                requested_paper_id = focus_request
        else:
            st.info(translation.gettext("graph_overview.select_paper_prompt"))

    with network_tab:
        if network_graph and network_graph.get("nodes"):
            highlight = _derive_network_highlight(network_graph, focus_node_id)
            st.plotly_chart(
                _graph_to_figure(network_graph, highlight_nodes=highlight),
                use_container_width=True,
            )
            related = _extract_related_papers(network_graph, focus_node_id, papers)
            if related:
                related_request = _render_related_papers(
                    related, translation=translation
                )
                if not requested_paper_id:
                    requested_paper_id = related_request
            else:
                st.caption(translation.gettext("graph_overview.no_related"))
        else:
            st.info(translation.gettext("graph_overview.network_wait"))

    return selected_option, requested_paper_id


def _collect_focus_nodes(
    paper_graph: dict[str, Any] | None,
    network_graph: dict[str, Any] | None,
) -> dict[str, dict[str, str]]:
    """Aggregate nodes from available graphs for focus selection."""

    lookup: dict[str, dict[str, str]] = {}
    for graph in (paper_graph, network_graph):
        if not graph:
            continue
        for node in graph.get("nodes", []):
            node_id = node.get("id")
            if not node_id or node_id in lookup:
                continue
            lookup[str(node_id)] = {
                "label": str(node.get("label", node_id)),
                "type": str(node.get("type", "Node")),
            }
    return lookup


def _format_focus_option(
    option: str,
    node_lookup: dict[str, dict[str, str]],
    translation: TranslationManager,
    default_focus: str | None,
) -> str:
    """Format focus options for display inside the selector."""

    if option == AUTO_FOCUS:
        label = translation.gettext("graph_overview.focus_selector_auto")
        if default_focus and default_focus in node_lookup:
            default_label = node_lookup[default_focus]["label"]
            label = f"{label} – {default_label}"
        return label
    entry = node_lookup.get(option)
    if not entry:
        return option
    return f"{entry['label']} ({entry['type']})"


def _node_in_graph(graph: dict[str, Any] | None, node_id: str | None) -> bool:
    """Return whether the node exists in the provided graph payload."""

    if not graph or not node_id:
        return False
    for node in graph.get("nodes", []):
        if node.get("id") == node_id:
            return True
    return False


def _render_focus_details(
    paper_graph: dict[str, Any] | None,
    network_graph: dict[str, Any] | None,
    focus_node_id: str | None,
    *,
    translation: TranslationManager,
) -> str | None:
    """Render contextual details for the currently focused node.

    Returns the identifier of a paper that should be loaded when a related
    paper button is selected, otherwise ``None``.
    """

    st.markdown(f"##### {translation.gettext('graph_overview.focus_details_header')}")
    if not focus_node_id:
        st.caption(translation.gettext("graph_overview.no_focus_details"))
        return None

    node = _find_node(paper_graph, focus_node_id) or _find_node(
        network_graph, focus_node_id
    )
    if not node:
        st.caption(translation.gettext("graph_overview.no_focus_details"))
        return None

    node_label = node.get("label", focus_node_id)
    node_type = node.get("type", "Node")
    metadata = node.get("metadata") or {}
    requested_paper_id: str | None = None

    st.markdown(f"**{node_label}**")
    st.caption(f"{translation.gettext('graph_overview.focus_type_label')}: {node_type}")

    if node_type == "Paper":
        summary = metadata.get("summary")
        st.markdown(f"**{translation.gettext('graph_overview.focus_summary')}**")
        if summary:
            st.write(translation.translate_text(summary))
        else:
            st.caption(translation.gettext("graph_overview.no_description"))

        metadata_payload: dict[str, Any] = {}
        authors = metadata.get("authors")
        if authors:
            metadata_payload[translation.gettext("chapter_viewer.authors")] = ", ".join(
                authors
            )
        landing = metadata.get("landing_url")
        if landing:
            metadata_payload[
                translation.gettext("graph_overview.open_landing_page")
            ] = landing
        published = metadata.get("published_at")
        if published:
            metadata_payload[
                translation.gettext("chapter_viewer.published")
            ] = published
        if metadata_payload:
            st.markdown(f"**{translation.gettext('graph_overview.focus_metadata')}**")
            st.write(metadata_payload)
    else:
        description = metadata.get("description")
        st.markdown(f"**{translation.gettext('graph_overview.focus_summary')}**")
        if description:
            st.write(translation.translate_text(description))
        else:
            st.caption(translation.gettext("graph_overview.no_description"))

    if node_type != "Paper":
        neighbor_papers = _list_neighbors(
            paper_graph, focus_node_id, target_type="Paper"
        )
        if neighbor_papers:
            st.markdown(
                f"**{translation.gettext('graph_overview.focus_related_papers')}**"
            )
            for neighbor in neighbor_papers:
                neighbor_id = neighbor.get("id")
                neighbor_label = neighbor.get("label", neighbor_id)
                cols = st.columns([3, 1])
                with cols[0]:
                    st.write(neighbor_label)
                with cols[1]:
                    if st.button(
                        translation.gettext("graph_overview.focus_in_app"),
                        key=f"focus_neighbor_{focus_node_id}_{neighbor_id}",
                    ):
                        requested_paper_id = neighbor_id
        else:
            st.caption(translation.gettext("graph_overview.no_related"))

    return requested_paper_id


def _find_node(
    graph: dict[str, Any] | None, node_id: str | None
) -> dict[str, Any] | None:
    """Return a node dictionary from the graph by identifier."""

    if not graph or not node_id:
        return None
    for node in graph.get("nodes", []):
        if node.get("id") == node_id:
            return node
    return None


def _list_neighbors(
    graph: dict[str, Any] | None,
    node_id: str | None,
    *,
    target_type: str | None = None,
) -> list[dict[str, Any]]:
    """Return neighbour nodes for the specified node, optionally filtered by type."""

    if not graph or not node_id:
        return []
    nodes = {node.get("id"): node for node in graph.get("nodes", []) if node.get("id")}
    if node_id not in nodes:
        return []

    neighbors: set[str] = set()
    for edge in graph.get("edges", []):
        source = edge.get("source")
        target = edge.get("target")
        if node_id not in (source, target):
            continue
        neighbor_id = target if source == node_id else source
        if not neighbor_id:
            continue
        if target_type and nodes.get(neighbor_id, {}).get("type") != target_type:
            continue
        neighbors.add(neighbor_id)

    return [nodes[neighbor_id] for neighbor_id in neighbors if neighbor_id in nodes]


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
    focus_node_id: str | None,
    papers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return related papers linked through shared concepts."""

    if not network_graph or not focus_node_id:
        return []

    nodes = {node.get("id"): node for node in network_graph.get("nodes", [])}
    focus_node = nodes.get(focus_node_id or "")
    if not focus_node or focus_node.get("type") != "Paper":
        return []
    paper_lookup = {paper.get("paper_id"): paper for paper in papers}

    related: list[dict[str, Any]] = []
    seen: set[str] = set()
    for edge in network_graph.get("edges", []):
        if edge.get("type") != "SHARES_CONCEPT":
            continue
        source = edge.get("source")
        target = edge.get("target")
        if focus_node_id not in (source, target):
            continue
        other_id = target if source == focus_node_id else source
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
) -> str | None:
    """Render a list of related papers with quick actions.

    Returns the identifier of a paper chosen via the "focus in app" button,
    if any were activated during this render pass.
    """

    st.markdown(f"##### {translation.gettext('graph_overview.related_papers')}")
    requested_paper_id: str | None = None
    for entry in related:
        shared_concepts = ", ".join(
            entry.get("shared_concepts") or []
        ) or translation.gettext("paper_browser.no_tags")
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
                    requested_paper_id = entry["paper_id"]

    return requested_paper_id


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
    focus_node_id: str | None,
) -> set[str]:
    """Return nodes to highlight in the network graph."""

    if not network_graph or not focus_node_id:
        return set()
    highlight = {focus_node_id}
    for edge in network_graph.get("edges", []):
        if focus_node_id == edge.get("source"):
            highlight.add(edge.get("target"))
        elif focus_node_id == edge.get("target"):
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
