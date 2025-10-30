"""Trending paper crawler for Hugging Face Papers."""

from __future__ import annotations

from datetime import datetime
import json
from html import unescape
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from backend.app.schemas import PaperRecord

from .base import TrendingSource


class HuggingFaceTrendingClient(TrendingSource):
    """Scrape the Hugging Face trending page for recent papers."""

    name = "huggingface"
    _BASE_URL = "https://huggingface.co"

    def __init__(self, endpoint: str, *, http_client: httpx.AsyncClient | None = None, timeout: float = 30.0) -> None:
        self._endpoint = endpoint
        self._client = http_client
        self._timeout = timeout

    async def fetch(self, limit: int) -> list[PaperRecord]:
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        owns_client = self._client is None
        try:
            response = await client.get(
                self._endpoint,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; PaperScopeBot/1.0; +https://paperscope.ai)"
                    )
                },
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
        finally:
            if owns_client:
                await client.aclose()

        records = self._extract_from_data_props(soup, limit)
        if len(records) < limit:
            for article in self._iter_articles(soup):
                if len(records) >= limit:
                    break
                try:
                    record = self._parse_article(article)
                except Exception as exc:  # pragma: no cover - defensive logging handled by caller
                    print(f"Failed to parse Hugging Face entry: {exc!r}")
                    continue
                if record.external_id not in {r.external_id for r in records}:
                    records.append(record)
        return records

    def _extract_from_data_props(self, soup: BeautifulSoup, limit: int) -> list[PaperRecord]:
        records: list[PaperRecord] = []
        seen_ids: set[str] = set()
        for container in soup.select("div[data-target='DailyPapers'][data-props]"):
            payload_raw = container.get("data-props")
            if not payload_raw:
                continue
            try:
                payload = json.loads(unescape(payload_raw))
            except json.JSONDecodeError:
                continue
            for entry in payload.get("dailyPapers", []):
                paper_data = entry.get("paper") or entry
                if not isinstance(paper_data, dict):
                    continue
                try:
                    record = self._parse_from_payload(paper_data)
                except Exception as exc:  # pragma: no cover - defensive logging handled by caller
                    print(f"Failed to parse Hugging Face JSON entry: {exc!r}")
                    continue
                if record.external_id in seen_ids:
                    continue
                records.append(record)
                seen_ids.add(record.external_id)
                if len(records) >= limit:
                    return records
        return records

    def _iter_articles(self, soup: BeautifulSoup) -> Iterable[Tag]:
        main = soup.select_one("main")
        if not main:
            return []
        return main.select("article")

    def _parse_article(self, article: Tag) -> PaperRecord:
        title_link = article.select_one("h3 a[href]")
        if not title_link:
            raise ValueError("Missing title link")
        title = title_link.get_text(strip=True) or "Untitled"
        landing_url = urljoin(self._BASE_URL, title_link["href"])
        external_id = self._extract_external_id(landing_url)

        abstract = self._extract_abstract(article)
        authors = self._extract_authors(article)
        tags = self._extract_tags(article)
        published_at = self._extract_published_at(article)
        arxiv_url = self._extract_arxiv_url(article)
        pdf_url = self._resolve_pdf_url(arxiv_url, external_id)

        return PaperRecord(
            external_id=external_id,
            source=self.name,
            title=title,
            abstract=abstract,
            authors=authors,
            pdf_url=pdf_url,
            landing_url=landing_url,
            published_at=published_at,
            tags=tags,
        )

    def _parse_from_payload(self, data: dict[str, Any]) -> PaperRecord:
        external_id = (
            data.get("id")
            or data.get("paperId")
            or data.get("arxivId")
            or data.get("slug")
        )
        if not external_id:
            raise ValueError("JSON entry missing external identifier")

        landing_url = data.get("url") or data.get("paperUrl")
        if not landing_url:
            landing_url = f"{self._BASE_URL}/papers/{external_id}"

        pdf_url = data.get("pdfUrl") or data.get("pdf_url")
        if not pdf_url and data.get("arxivUrl"):
            pdf_url = data["arxivUrl"].replace("/abs/", "/pdf/") + ".pdf"
        if not pdf_url:
            pdf_url = self._resolve_pdf_url(data.get("arxivUrl") or data.get("arxiv_id"), external_id)

        summary = data.get("summary") or data.get("ai_summary")
        authors = []
        for author in data.get("authors", []):
            if isinstance(author, dict):
                name = author.get("name") or author.get("fullname") or author.get("fullName")
                if name:
                    authors.append(name)
            elif isinstance(author, str):
                authors.append(author)

        tags = data.get("ai_keywords") or data.get("tags") or []
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

        published_at = self._parse_datetime(data.get("publishedAt") or data.get("published_at"))

        return PaperRecord(
            external_id=external_id,
            source=self.name,
            title=data.get("title") or data.get("paperTitle") or "Untitled",
            abstract=summary,
            authors=authors,
            pdf_url=pdf_url,
            landing_url=landing_url,
            published_at=published_at,
            tags=tags if isinstance(tags, list) else [],
        )

    def _extract_abstract(self, article: Tag) -> str | None:
        abstract_el = article.select_one("p")
        if abstract_el:
            text = abstract_el.get_text(strip=True)
            return text or None
        return None

    def _extract_authors(self, article: Tag) -> list[str]:
        authors: list[str] = []
        for item in article.select("li[title]"):
            title = item.get("title")
            if title:
                authors.append(title.strip())
        if authors:
            return authors

        author_spans = article.select("div span")
        for span in author_spans:
            text = span.get_text(strip=True)
            if text and text.lower().startswith("by "):
                authors.extend(author.strip() for author in text[3:].split(",") if author.strip())
        return authors

    def _extract_tags(self, article: Tag) -> list[str]:
        tags: list[str] = []
        for tag_link in article.select("a[href*='/papers?tag=']"):
            label = tag_link.get_text(strip=True)
            if label:
                tags.append(label)
        return tags

    def _extract_published_at(self, article: Tag) -> datetime | None:
        for span in article.find_all("span"):
            text = span.get_text(strip=True)
            if not text:
                continue
            if "Published on" in text:
                return self._parse_datetime(text.replace("Published on", "").strip())
        return None

    def _extract_arxiv_url(self, article: Tag) -> str | None:
        for link in article.select("a[href]"):
            href = link.get("href", "")
            if "arxiv.org" in href:
                return urljoin(self._BASE_URL, href)
        return None

    def _resolve_pdf_url(self, arxiv_url: str | None, external_id: str) -> str:
        if arxiv_url:
            if "/pdf/" in arxiv_url:
                return arxiv_url if arxiv_url.endswith(".pdf") else f"{arxiv_url}.pdf"
            if "/abs/" in arxiv_url:
                return arxiv_url.replace("/abs/", "/pdf/") + ".pdf"
        return f"https://arxiv.org/pdf/{external_id}.pdf"

    def _extract_external_id(self, landing_url: str) -> str:
        path = urlparse(landing_url).path
        external_id = path.rstrip("/").split("/")[-1]
        if not external_id:
            raise ValueError("Unable to derive external id")
        return external_id

    def _parse_datetime(self, value: str) -> datetime | None:
        value = value.strip()
        if not value:
            return None
        try:
            # Attempt ISO parsing first.
            normalized = value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized)
        except ValueError:
            pass
        try:
            return datetime.strptime(value, "%b %d, %Y")
        except ValueError:
            return None
