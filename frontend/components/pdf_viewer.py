"""PDF workspace component."""

from __future__ import annotations

import base64
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from services.i18n import TranslationManager

def render_pdf_viewer(
    paper: dict[str, Any] | None,
    *,
    pdf_url: str | None,
    pdf_bytes: bytes | None,
    translation: TranslationManager,
) -> None:
    """Render the PDF workspace for a selected paper."""

    st.subheader(translation.gettext("pdf_viewer.header"))
    if not paper:
        st.info(translation.gettext("pdf_viewer.no_paper"))
        return

    storage_path_obj = paper.get("storage_path")
    storage_path_str = str(storage_path_obj or "")
    pdf_exists = bool(storage_path_str)
    pdf_available = pdf_bytes is not None
    paper_id = paper.get("paper_id") or paper.get("external_id") or "paper"

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown(f"### {paper.get('title', 'Untitled')}")
        toolbar = st.columns([1, 1, 2])
        with toolbar[0]:
            st.caption(translation.gettext("pdf_viewer.pdf_actions"))
            if pdf_exists and pdf_url:
                st.link_button(
                    translation.gettext("pdf_viewer.download_pdf"),
                    pdf_url,
                    use_container_width=True,
                )
            else:
                st.button(
                    translation.gettext("pdf_viewer.download_pdf"),
                    disabled=True,
                    use_container_width=True,
                )
        with toolbar[1]:
            st.caption(translation.gettext("pdf_viewer.open_in_new_tab"))
            if pdf_exists and pdf_url:
                st.link_button(
                    translation.gettext("pdf_viewer.open_viewer"),
                    pdf_url,
                    use_container_width=True,
                )
            elif pdf_exists:
                st.caption(translation.gettext("pdf_viewer.file_stored"))
            else:
                st.caption(translation.gettext("pdf_viewer.pdf_pending"))
        with toolbar[2]:
            st.caption(translation.gettext("pdf_viewer.storage_path"))
            if storage_path_obj:
                st.code(str(storage_path_obj), line_numbers=False)
            else:
                st.caption(translation.gettext("pdf_viewer.not_persisted"))

        if pdf_available:
            b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
            iframe = f"""
                <iframe src='data:application/pdf;base64,{b64_pdf}' style='border:none;width:100%;height:720px;'></iframe>
            """
            components.html(iframe, height=740)
        else:
            st.warning(translation.gettext("pdf_viewer.pdf_missing"))

    with right:
        summary_tab, key_points_tab, metadata_tab = st.tabs(
            [
                translation.gettext("pdf_viewer.summary_tab"),
                translation.gettext("pdf_viewer.highlights_tab"),
                translation.gettext("pdf_viewer.metadata_tab"),
            ]
        )
        with summary_tab:
            summary_text = translation.translate_text(paper.get("summary"))
            st.write(summary_text or translation.gettext("pdf_viewer.summary_unavailable"))
        with key_points_tab:
            key_points = paper.get("key_points") or []
            if key_points:
                translated_points = translation.translate_list(key_points)
                st.markdown("\n".join(f"- {point}" for point in translated_points))
            else:
                st.caption(translation.gettext("pdf_viewer.no_key_points"))
        with metadata_tab:
            st.write(
                {
                    translation.gettext("pdf_viewer.source"): paper.get("source")
                    or "huggingface",
                    translation.gettext("pdf_viewer.authors"): ", ".join(
                        paper.get("authors", [])
                    )
                    or translation.gettext("paper_browser.unknown_authors"),
                    translation.gettext("pdf_viewer.tags"): ", ".join(
                        paper.get("tags", [])
                    )
                    or translation.gettext("paper_browser.no_tags"),
                    translation.gettext("pdf_viewer.published"): paper.get(
                        "published_at"
                    )
                    or translation.gettext("paper_browser.unknown_published"),
                    translation.gettext("pdf_viewer.paper_id"): paper_id,
                }
            )
