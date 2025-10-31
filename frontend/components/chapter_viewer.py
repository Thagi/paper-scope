"""LLM chapter explanation component."""

from __future__ import annotations

from typing import Any

import streamlit as st

from services.i18n import TranslationManager


def render_chapter_viewer(
    paper: dict[str, Any] | None,
    *,
    paper_graph: dict[str, Any] | None,
    translation: TranslationManager,
) -> None:
    """Render a narrative-first view of the selected paper."""

    st.subheader(translation.gettext("chapter_viewer.header"))
    if not paper:
        st.info(translation.gettext("chapter_viewer.no_paper"))
        return

    nodes = (paper_graph or {}).get("nodes", [])
    node_by_id = {str(node.get("id")): node for node in nodes if node.get("id")}
    label_lookup = {
        str(node.get("label")).casefold(): str(node.get("id"))
        for node in nodes
        if node.get("label")
    }

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown(f"### {paper.get('title', 'Untitled')}")
        st.markdown(f"#### {translation.gettext('chapter_viewer.summary')}")
        summary_text = translation.translate_text(paper.get("summary"))
        if summary_text:
            st.write(summary_text)
        else:
            st.caption(translation.gettext("chapter_viewer.summary_unavailable"))

        st.markdown(f"#### {translation.gettext('chapter_viewer.key_points')}")
        key_points = paper.get("key_points") or []
        if key_points:
            translated_points = translation.translate_list(key_points)
            st.markdown("\n".join(f"- {point}" for point in translated_points))
        else:
            st.caption(translation.gettext("chapter_viewer.no_key_points"))

    with right:
        st.markdown(f"#### {translation.gettext('chapter_viewer.metadata')}")
        metadata = {
            translation.gettext("chapter_viewer.source"): paper.get("source") or "—",
            translation.gettext("chapter_viewer.authors"): ", ".join(
                paper.get("authors", [])
            )
            or translation.gettext("paper_browser.unknown_authors"),
            translation.gettext("chapter_viewer.tags"): ", ".join(paper.get("tags", []))
            or translation.gettext("paper_browser.no_tags"),
            translation.gettext("chapter_viewer.published"): paper.get("published_at")
            or translation.gettext("paper_browser.unknown_published"),
            translation.gettext("chapter_viewer.paper_id"): paper.get("paper_id")
            or paper.get("external_id")
            or "",
        }
        st.write(metadata)

    st.divider()
    chapters = paper.get("chapters") or []
    if not chapters:
        st.info(translation.gettext("chapter_viewer.no_chapters"))
        return

    for index, chapter in enumerate(chapters, start=1):
        chapter_title = chapter.get("title") or translation.gettext(
            "chapter_viewer.summary"
        )
        display_title = translation.gettext(
            "chapter_viewer.chapter_title", index=index, title=chapter_title
        )
        with st.expander(display_title, expanded=index == 1):
            explanation = translation.translate_text(chapter.get("explanation"))
            st.write(
                explanation or translation.gettext("chapter_viewer.summary_unavailable")
            )

            related_concepts = chapter.get("related_concepts") or []
            concept_buttons: list[tuple[str, str | None]] = []
            for concept in related_concepts:
                label, node_id = _extract_concept_anchor(
                    concept, node_by_id, label_lookup
                )
                if not label:
                    continue
                concept_buttons.append((label, node_id))

            if concept_buttons:
                st.markdown(
                    f"**{translation.gettext('chapter_viewer.chapter_concepts')}**"
                )
                st.caption(translation.gettext("chapter_viewer.click_to_focus"))
                columns = st.columns(min(len(concept_buttons), 3) or 1)
                for idx, (label, node_id) in enumerate(concept_buttons):
                    column = columns[idx % len(columns)]
                    with column:
                        disabled = node_id is None
                        button_label = label if not disabled else f"{label}"
                        if st.button(
                            button_label,
                            key=f"chapter_{index}_concept_{idx}_{label}",
                            disabled=disabled,
                        ):
                            if node_id:
                                st.session_state["graph_focus_selection"] = node_id
                                st.experimental_rerun()
            else:
                st.caption(translation.gettext("chapter_viewer.no_concepts"))


def _extract_concept_anchor(
    concept: Any, node_by_id: dict[str, dict[str, Any]], label_lookup: dict[str, str]
) -> tuple[str | None, str | None]:
    """Return the display label and node identifier for a chapter concept."""

    if isinstance(concept, dict):
        label = concept.get("label") or concept.get("name")
        normalized = concept.get("normalized")
    else:
        label = str(concept)
        normalized = None

    if not label:
        return None, None

    node_id: str | None = None
    if normalized:
        candidate = str(normalized)
        if candidate in node_by_id:
            node_id = candidate
    if not node_id:
        key = label.casefold()
        node_id = label_lookup.get(key)
    return label, node_id
