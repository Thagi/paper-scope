"""Internationalisation utilities for the Streamlit frontend."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from functools import cache
from typing import Any

import streamlit as st
from deep_translator import GoogleTranslator

SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "ja": "日本語",
}


_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "app.title": "📚 Paper Scope",
        "app.caption": "Monitor trending research, summarize insights, and explore knowledge graphs.",
        "sidebar.language": "Language",
        "sidebar.ingestion_header": "Ingestion Controls",
        "sidebar.trigger_ingestion": "Trigger Ingestion",
        "sidebar.trigger_ingestion_running": "Running ingestion pipeline...",
        "sidebar.trigger_ingestion_success": "Ingestion completed successfully.",
        "sidebar.trigger_ingestion_failure": "Failed to trigger ingestion: {error}",
        "sidebar.last_persisted": "Last Persisted",
        "load_papers_error": "Unable to load papers: {error}",
        "load_paper_graph_warning": "Could not load paper graph: {error}",
        "load_network_graph_warning": "Unable to load network graph: {error}",
        "dashboard.ingestion_overview": "Ingestion Overview",
        "dashboard.tracked_papers": "Tracked Papers",
        "dashboard.sources": "Sources",
        "dashboard.last_run_persisted": "Last Run Persisted",
        "dashboard.last_ingestion_details": "Last Ingestion Details",
        "dashboard.recent_highlights": "Recent Paper Highlights",
        "dashboard.newest_papers": "Newest Papers:",
        "dashboard.no_recent_papers": "None",
        "dashboard.median_publication_year": "Median publication year: {year}",
        "dashboard.no_papers": "No ingested papers yet. Trigger an ingestion run to populate the knowledge graph.",
        "insights.library_insights": "Library Insights",
        "insights.no_papers": "Ingest papers to unlock trend analytics and coverage metrics.",
        "insights.tagged_papers": "Tagged Papers",
        "insights.summaries_available": "Summaries Available",
        "insights.pdfs_stored": "PDFs Stored",
        "insights.coverage_delta": "{percentage:.0f}% coverage",
        "insights.tags_caption": "Tag coverage insights will appear after enrichment tags are populated.",
        "insights.timeline_caption": "Publication timeline will appear when papers include publication dates.",
        "insights.top_tags": "Top Tags",
        "insights.tag_label": "Tag",
        "insights.count_label": "Papers",
        "insights.timeline_title": "Publication Timeline",
        "insights.year_label": "Year",
        "insights.prolific_authors": "Prolific Authors",
        "insights.authors_caption": "Author insights will appear once author metadata is available.",
        "paper_browser.header": "Paper Explorer",
        "paper_browser.no_papers": "No papers available yet. Trigger ingestion to populate the catalog.",
        "paper_browser.search_label": "Search by title, author, or concept",
        "paper_browser.search_placeholder": "Graph neural networks",
        "paper_browser.filter_label": "Filter by tag",
        "paper_browser.filter_placeholder": "Select tags to narrow the list",
        "paper_browser.sort_label": "Sort order",
        "paper_browser.sort_newest": "Newest",
        "paper_browser.sort_oldest": "Oldest",
        "paper_browser.sort_title": "Title",
        "paper_browser.select_label": "Select a paper",
        "paper_browser.no_matches": "No matches",
        "paper_browser.matching_count": "{count} papers match the current filters.",
        "paper_browser.preview_title": "Title",
        "paper_browser.preview_authors": "Authors",
        "paper_browser.preview_published": "Published",
        "paper_browser.preview_tags": "Tags",
        "paper_browser.unknown_authors": "Unknown",
        "paper_browser.unknown_published": "Unknown",
        "paper_browser.no_tags": "—",
        "pdf_viewer.header": "PDF Workspace",
        "pdf_viewer.no_paper": "Select a paper from the list to view its PDF and summary.",
        "pdf_viewer.pdf_actions": "PDF Actions",
        "pdf_viewer.download_pdf": "Download PDF",
        "pdf_viewer.open_in_new_tab": "Open in new tab",
        "pdf_viewer.open_viewer": "Open Viewer",
        "pdf_viewer.file_stored": "File stored inside container",
        "pdf_viewer.pdf_pending": "PDF pending download",
        "pdf_viewer.storage_path": "Storage Path",
        "pdf_viewer.not_persisted": "Not persisted yet",
        "pdf_viewer.pdf_missing": "PDF is not available for this paper yet. Trigger ingestion to download it.",
        "pdf_viewer.summary_tab": "Summary",
        "pdf_viewer.highlights_tab": "Highlights",
        "pdf_viewer.metadata_tab": "Metadata",
        "pdf_viewer.summary_unavailable": "Summary unavailable.",
        "pdf_viewer.no_key_points": "No key points generated yet.",
        "pdf_viewer.source": "Source",
        "pdf_viewer.authors": "Authors",
        "pdf_viewer.tags": "Tags",
        "pdf_viewer.published": "Published",
        "pdf_viewer.paper_id": "Paper ID",
        "graph_overview.header": "Knowledge Graph Explorer",
        "graph_overview.no_data": "Graph data will appear once papers are ingested and enriched.",
        "graph_overview.paper_nodes": "Paper Nodes",
        "graph_overview.concept_nodes": "Concept Nodes",
        "graph_overview.cross_paper_links": "Cross-Paper Links",
        "graph_overview.selected_tab": "Selected Paper Graph",
        "graph_overview.network_tab": "Cross-Paper Network",
        "graph_overview.select_paper_prompt": "Select a paper to visualise its neighbourhood graph.",
        "graph_overview.network_wait": "Network data will appear after multiple papers share concepts.",
        "graph_overview.related_papers": "Related Papers",
        "graph_overview.no_related": "No overlapping concepts with other papers yet.",
        "graph_overview.published_caption": "Published: {published} · Shared concepts ({weight}): {concepts}",
        "graph_overview.open_landing_page": "Open landing page",
        "graph_overview.focus_in_app": "Focus in app",
        "graph_overview.no_network_data": "Network data will appear after multiple papers share concepts.",
        "graph_overview.key_concepts": "Key Concepts",
    },
    "ja": {
        "app.title": "📚 Paper Scope",
        "app.caption": "最新の研究動向を追跡し、洞察を要約し、ナレッジグラフを探索しましょう。",
        "sidebar.language": "言語",
        "sidebar.ingestion_header": "インジェスト管理",
        "sidebar.trigger_ingestion": "インジェストを実行",
        "sidebar.trigger_ingestion_running": "インジェストパイプラインを実行中...",
        "sidebar.trigger_ingestion_success": "インジェストが正常に完了しました。",
        "sidebar.trigger_ingestion_failure": "インジェストの起動に失敗しました: {error}",
        "sidebar.last_persisted": "前回の保存件数",
        "load_papers_error": "論文を読み込めませんでした: {error}",
        "load_paper_graph_warning": "論文グラフを読み込めませんでした: {error}",
        "load_network_graph_warning": "ネットワークグラフを読み込めませんでした: {error}",
        "dashboard.ingestion_overview": "インジェスト概要",
        "dashboard.tracked_papers": "追跡中の論文",
        "dashboard.sources": "ソース",
        "dashboard.last_run_persisted": "直近の保存数",
        "dashboard.last_ingestion_details": "直近のインジェスト詳細",
        "dashboard.recent_highlights": "最新のハイライト",
        "dashboard.newest_papers": "最新の論文:",
        "dashboard.no_recent_papers": "なし",
        "dashboard.median_publication_year": "中央値の発行年: {year}",
        "dashboard.no_papers": "まだ論文がインジェストされていません。インジェストを実行してナレッジグラフを構築しましょう。",
        "insights.library_insights": "ライブラリ分析",
        "insights.no_papers": "インジェストを行うとトレンド分析とカバレッジ指標が表示されます。",
        "insights.tagged_papers": "タグ付き論文",
        "insights.summaries_available": "要約が利用可能",
        "insights.pdfs_stored": "保存済みPDF",
        "insights.coverage_delta": "カバレッジ {percentage:.0f}%",
        "insights.tags_caption": "タグが作成されるとカバレッジ分析が表示されます。",
        "insights.timeline_caption": "論文に発行日が含まれると年次推移が表示されます。",
        "insights.top_tags": "人気タグ",
        "insights.tag_label": "タグ",
        "insights.count_label": "論文数",
        "insights.timeline_title": "発行年の推移",
        "insights.year_label": "年",
        "insights.prolific_authors": "主要著者",
        "insights.authors_caption": "著者メタデータが利用可能になると表示されます。",
        "paper_browser.header": "論文ブラウザー",
        "paper_browser.no_papers": "まだ論文がありません。インジェストを実行してカタログを作成してください。",
        "paper_browser.search_label": "タイトル・著者・概念で検索",
        "paper_browser.search_placeholder": "Graph neural networks",
        "paper_browser.filter_label": "タグで絞り込む",
        "paper_browser.filter_placeholder": "タグを選択してリストを絞り込む",
        "paper_browser.sort_label": "並び替え",
        "paper_browser.sort_newest": "新しい順",
        "paper_browser.sort_oldest": "古い順",
        "paper_browser.sort_title": "タイトル",
        "paper_browser.select_label": "論文を選択",
        "paper_browser.no_matches": "該当なし",
        "paper_browser.matching_count": "現在の条件に一致する論文は {count} 件です。",
        "paper_browser.preview_title": "タイトル",
        "paper_browser.preview_authors": "著者",
        "paper_browser.preview_published": "発行日",
        "paper_browser.preview_tags": "タグ",
        "paper_browser.unknown_authors": "不明",
        "paper_browser.unknown_published": "不明",
        "paper_browser.no_tags": "―",
        "pdf_viewer.header": "PDFワークスペース",
        "pdf_viewer.no_paper": "PDFと要約を見るには論文を選択してください。",
        "pdf_viewer.pdf_actions": "PDFアクション",
        "pdf_viewer.download_pdf": "PDFをダウンロード",
        "pdf_viewer.open_in_new_tab": "新しいタブで開く",
        "pdf_viewer.open_viewer": "ビューアを開く",
        "pdf_viewer.file_stored": "ファイルはコンテナ内に保存されています",
        "pdf_viewer.pdf_pending": "PDFはダウンロード待ちです",
        "pdf_viewer.storage_path": "保存パス",
        "pdf_viewer.not_persisted": "まだ保存されていません",
        "pdf_viewer.pdf_missing": "この論文のPDFはまだ利用できません。インジェストを実行してください。",
        "pdf_viewer.summary_tab": "要約",
        "pdf_viewer.highlights_tab": "ハイライト",
        "pdf_viewer.metadata_tab": "メタデータ",
        "pdf_viewer.summary_unavailable": "要約は利用できません。",
        "pdf_viewer.no_key_points": "キーポイントはまだ生成されていません。",
        "pdf_viewer.source": "ソース",
        "pdf_viewer.authors": "著者",
        "pdf_viewer.tags": "タグ",
        "pdf_viewer.published": "発行日",
        "pdf_viewer.paper_id": "論文ID",
        "graph_overview.header": "ナレッジグラフビューア",
        "graph_overview.no_data": "論文がインジェストされるとグラフデータが表示されます。",
        "graph_overview.paper_nodes": "論文ノード",
        "graph_overview.concept_nodes": "概念ノード",
        "graph_overview.cross_paper_links": "論文間リンク",
        "graph_overview.selected_tab": "選択中の論文グラフ",
        "graph_overview.network_tab": "論文ネットワーク",
        "graph_overview.select_paper_prompt": "論文を選択すると近傍グラフを表示します。",
        "graph_overview.network_wait": "複数の論文で概念が共有されるとネットワークが表示されます。",
        "graph_overview.related_papers": "関連論文",
        "graph_overview.no_related": "他の論文と共通する概念はまだありません。",
        "graph_overview.published_caption": "発行日: {published} · 共有概念 ({weight}): {concepts}",
        "graph_overview.open_landing_page": "ランディングページを開く",
        "graph_overview.focus_in_app": "アプリでフォーカス",
        "graph_overview.no_network_data": "ネットワークグラフはまだ利用できません。",
        "graph_overview.key_concepts": "主要概念",
    },
}


@dataclass(frozen=True)
class TranslationManager:
    """Helper to manage UI text and dynamic translations."""

    language: str

    def gettext(self, key: str, **kwargs: Any) -> str:
        """Return the translated value for a given key."""

        translations = _TRANSLATIONS.get(self.language, {})
        template = translations.get(key) or _TRANSLATIONS["en"].get(key) or key
        return template.format(**kwargs)

    def translate_text(self, text: str | None) -> str | None:
        """Translate arbitrary text into the active language if needed."""

        if not text or self.language == "en":
            return text
        try:
            return _translate_text_cached(text, self.language)
        except Exception:
            # Fall back to the original text if translation fails.
            return text

    def translate_list(self, values: Iterable[str]) -> list[str]:
        """Translate an iterable of strings into the active language."""

        return [self.translate_text(value) or "" for value in values]


@cache
def _translator_for(language: str) -> GoogleTranslator:
    return GoogleTranslator(source="auto", target=language)


@st.cache_data(show_spinner=False)
def _translate_text_cached(text: str, language: str) -> str:
    translator = _translator_for(language)
    return translator.translate(text)


def get_translation_manager() -> TranslationManager:
    """Return a translation manager bound to the current session language."""

    language = st.session_state.get("language", "en")
    if language not in SUPPORTED_LANGUAGES:
        language = "en"
    return TranslationManager(language=language)


def set_language(language: str) -> None:
    """Update the active UI language."""

    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")
    st.session_state["language"] = language
