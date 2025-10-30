"""PDF workspace component."""

from __future__ import annotations

import base64
from typing import Any

import streamlit as st
import streamlit.components.v1 as components


def render_pdf_viewer(
    paper: dict[str, Any] | None,
    *,
    pdf_url: str | None,
    pdf_bytes: bytes | None,
) -> None:
    """Render the PDF workspace for a selected paper."""

    st.subheader("PDF Workspace")
    if not paper:
        st.info("Select a paper from the list to view its PDF and summary.")
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
            st.caption("PDF Actions")
            if pdf_exists and pdf_url:
                st.link_button(
                    "Download PDF",
                    pdf_url,
                    use_container_width=True,
                )
            else:
                st.button("Download PDF", disabled=True, use_container_width=True)
        with toolbar[1]:
            st.caption("Open in new tab")
            if pdf_exists and pdf_url:
                st.link_button("Open Viewer", pdf_url, use_container_width=True)
            elif pdf_exists:
                st.caption("File stored inside container")
            else:
                st.caption("PDF pending download")
        with toolbar[2]:
            st.caption("Storage Path")
            if storage_path_obj:
                st.code(str(storage_path_obj), line_numbers=False)
            else:
                st.caption("Not persisted yet")

        if pdf_available:
            b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
            iframe = f"""
                <iframe src='data:application/pdf;base64,{b64_pdf}' style='border:none;width:100%;height:720px;'></iframe>
            """
            components.html(iframe, height=740)
        else:
            st.warning("PDF is not available for this paper yet. Trigger ingestion to download it.")

    with right:
        summary_tab, key_points_tab, metadata_tab = st.tabs(["Summary", "Highlights", "Metadata"])
        with summary_tab:
            st.write(paper.get("summary") or "Summary unavailable.")
        with key_points_tab:
            key_points = paper.get("key_points") or []
            if key_points:
                st.markdown("\n".join(f"- {point}" for point in key_points))
            else:
                st.caption("No key points generated yet.")
        with metadata_tab:
            st.write(
                {
                    "Source": paper.get("source") or "huggingface",
                    "Authors": ", ".join(paper.get("authors", [])) or "Unknown",
                    "Tags": ", ".join(paper.get("tags", [])) or "None",
                    "Published": paper.get("published_at") or "Unknown",
                    "Paper ID": paper_id,
                }
            )
