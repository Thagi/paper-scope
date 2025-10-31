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
        "chapter_viewer.header": "Narrative Explorer",
        "chapter_viewer.no_paper": "Select a paper to read its guided explanation.",
        "chapter_viewer.no_chapters": "No chapter-level explanation is available yet.",
        "chapter_viewer.summary": "Global Summary",
        "chapter_viewer.key_points": "Highlights",
        "chapter_viewer.metadata": "Metadata",
        "chapter_viewer.chapter_concepts": "Concept anchors",
        "chapter_viewer.click_to_focus": "Click a concept to focus the knowledge graph.",
        "chapter_viewer.summary_unavailable": "Summary unavailable.",
        "chapter_viewer.no_key_points": "No highlights yet.",
        "chapter_viewer.no_concepts": "No linked nodes for this section yet.",
        "chapter_viewer.chapter_title": "Chapter {index}: {title}",
        "chapter_viewer.source": "Source",
        "chapter_viewer.authors": "Authors",
        "chapter_viewer.tags": "Tags",
        "chapter_viewer.published": "Published",
        "chapter_viewer.paper_id": "Paper ID",
        "chapter_viewer.focus_graph_action": "Focus in graph",
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
        "graph_overview.instructions": "Use the selector or chapter highlights to focus nodes in the knowledge graph.",
        "graph_overview.focus_selector": "Focus node",
        "graph_overview.focus_selector_auto": "Auto (selected paper)",
        "graph_overview.focus_details_header": "Focused node details",
        "graph_overview.no_focus_details": "Select a node to inspect its context.",
        "graph_overview.focus_summary": "Summary",
        "graph_overview.focus_metadata": "Metadata",
        "graph_overview.focus_related_concepts": "Connected concepts",
        "graph_overview.focus_related_papers": "Linked papers",
        "graph_overview.no_description": "No description available.",
        "graph_overview.focus_type_label": "Type",
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
        "chapter_viewer.header": "ナレッジガイド",
        "chapter_viewer.no_paper": "ガイド付きの説明を見るには論文を選択してください。",
        "chapter_viewer.no_chapters": "章ごとの説明はまだ生成されていません。",
        "chapter_viewer.summary": "全体要約",
        "chapter_viewer.key_points": "ハイライト",
        "chapter_viewer.metadata": "メタデータ",
        "chapter_viewer.chapter_concepts": "関連ノード",
        "chapter_viewer.click_to_focus": "概念をクリックするとナレッジグラフがフォーカスします。",
        "chapter_viewer.summary_unavailable": "要約は利用できません。",
        "chapter_viewer.no_key_points": "ハイライトはまだありません。",
        "chapter_viewer.no_concepts": "このセクションに紐づくノードはまだありません。",
        "chapter_viewer.chapter_title": "第{index}章: {title}",
        "chapter_viewer.source": "ソース",
        "chapter_viewer.authors": "著者",
        "chapter_viewer.tags": "タグ",
        "chapter_viewer.published": "発行日",
        "chapter_viewer.paper_id": "論文ID",
        "chapter_viewer.focus_graph_action": "グラフでフォーカス",
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
        "graph_overview.instructions": "セレクターまたは章のハイライトからノードを選んでグラフをフォーカスしましょう。",
        "graph_overview.focus_selector": "フォーカスするノード",
        "graph_overview.focus_selector_auto": "自動（選択中の論文）",
        "graph_overview.focus_details_header": "フォーカス中のノード詳細",
        "graph_overview.no_focus_details": "ノードを選択してコンテキストを確認してください。",
        "graph_overview.focus_summary": "概要",
        "graph_overview.focus_metadata": "メタデータ",
        "graph_overview.focus_related_concepts": "関連する概念",
        "graph_overview.focus_related_papers": "関連論文",
        "graph_overview.no_description": "説明はありません。",
        "graph_overview.focus_type_label": "タイプ",
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
