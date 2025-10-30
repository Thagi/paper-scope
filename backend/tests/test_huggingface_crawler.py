"""Tests for the Hugging Face trending crawler."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
import pytest

from backend.app.services.crawlers.huggingface import HuggingFaceTrendingClient


class DummyAsyncClient:
    """Async client stub returning a preconfigured response."""

    def __init__(self, response: httpx.Response) -> None:
        self._response = response
        self.closed = False

    async def get(self, *args: Any, **kwargs: Any) -> httpx.Response:  # noqa: ANN401
        return self._response

    async def aclose(self) -> None:
        self.closed = True


DATA_PROPS_HTML = """
<html>
  <body>
    <div data-target="DailyPapers" data-props="{&quot;dailyPapers&quot;:[{&quot;paper&quot;:{&quot;id&quot;:&quot;2401.00099&quot;,&quot;title&quot;:&quot;Data Props Paper&quot;,&quot;summary&quot;:&quot;JSON provided summary.&quot;,&quot;authors&quot;:[{&quot;name&quot;:&quot;Dana&quot;},{&quot;name&quot;:&quot;Eli&quot;}],&quot;ai_keywords&quot;:[&quot;json&quot;,&quot;parsing&quot;],&quot;publishedAt&quot;:&quot;2024-03-01T00:00:00Z&quot;}}]}">
    </div>
  </body>
</html>
"""


TRENDING_HTML = """
<html>
  <body>
    <main>
      <section>
        <article>
          <div>
            <h3><a href="/papers/2401.00001">First Paper</a></h3>
            <div><p>This is a test abstract.</p></div>
            <div>
              <ul>
                <li title="Alice"></li>
                <li title="Bob"></li>
              </ul>
              <span>Published on Jan 5, 2024</span>
            </div>
          </div>
          <div>
            <a href="https://github.com/test/repo">GitHub</a>
            <a href="https://arxiv.org/abs/2401.00001">arXiv</a>
          </div>
          <div>
            <a href="/papers?tag=nlp">NLP</a>
            <a href="/papers?tag=transformers">Transformers</a>
          </div>
        </article>
        <article>
          <div>
            <h3><a href="/papers/2401.00002">Second Paper</a></h3>
            <div><p>Another abstract.</p></div>
            <div><span>Published on Feb 10, 2024</span></div>
          </div>
          <div>
            <a href="https://arxiv.org/pdf/2401.00002.pdf">arXiv PDF</a>
          </div>
        </article>
      </section>
    </main>
  </body>
</html>
"""


@pytest.mark.asyncio
async def test_fetch_prefers_data_props_payload() -> None:
    """Ensure JSON payload takes precedence over article scraping."""

    response = httpx.Response(200, headers={"Content-Type": "text/html"}, text=DATA_PROPS_HTML)
    client = HuggingFaceTrendingClient("https://huggingface.co/papers/trending", http_client=DummyAsyncClient(response))

    records = await client.fetch(limit=5)

    assert len(records) == 1
    record = records[0]
    assert record.external_id == "2401.00099"
    assert record.title == "Data Props Paper"
    assert record.abstract == "JSON provided summary."
    assert record.authors == ["Dana", "Eli"]
    assert record.tags == ["json", "parsing"]
    assert record.published_at == datetime(2024, 3, 1)
    assert record.pdf_url.endswith("2401.00099.pdf")


@pytest.mark.asyncio
async def test_fetch_parses_articles_when_no_json_payload() -> None:
    """Ensure HTML articles are converted when JSON payload is missing."""

    response = httpx.Response(200, headers={"Content-Type": "text/html"}, text=TRENDING_HTML)
    client = HuggingFaceTrendingClient("https://huggingface.co/papers/trending", http_client=DummyAsyncClient(response))

    records = await client.fetch(limit=5)

    assert len(records) == 2

    first = records[0]
    assert first.external_id == "2401.00001"
    assert first.title == "First Paper"
    assert first.abstract == "This is a test abstract."
    assert first.authors == ["Alice", "Bob"]
    assert first.tags == ["NLP", "Transformers"]
    assert first.pdf_url == "https://arxiv.org/pdf/2401.00001.pdf"
    assert first.published_at == datetime(2024, 1, 5)

    second = records[1]
    assert second.external_id == "2401.00002"
    assert second.pdf_url == "https://arxiv.org/pdf/2401.00002.pdf"
    assert second.tags == []
    assert second.authors == []


@pytest.mark.asyncio
async def test_fetch_handles_empty_markup() -> None:
    """Return an empty list when the trending markup is missing."""

    response = httpx.Response(200, headers={"Content-Type": "text/html"}, text="<html><body></body></html>")
    client = HuggingFaceTrendingClient("https://huggingface.co/papers/trending", http_client=DummyAsyncClient(response))

    records = await client.fetch(limit=10)

    assert records == []
