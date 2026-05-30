"""HTML page fetcher via httpx + trafilatura."""

from __future__ import annotations

import asyncio

import httpx
import trafilatura

from ._http import build_client
from .types import Document


async def afetch_html(url: str, *, client: httpx.AsyncClient | None = None) -> Document:
    own_client = client is None
    if own_client:
        client = build_client()
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "").lower()
        raw = resp.content
        html = resp.text
    finally:
        if own_client:
            await client.aclose()

    # A URL that looked like a web page can still serve a PDF — hand it off.
    if "application/pdf" in content_type or raw[:5] == b"%PDF-":
        from .pdf import afetch_pdf

        return await afetch_pdf(url, _content=raw)

    content = trafilatura.extract(html, output_format="markdown", with_metadata=False) or ""
    meta = trafilatura.extract_metadata(html)

    title: str | None = None
    extra: dict = {}
    if meta is not None:
        title = meta.title
        if meta.author:
            extra["author"] = meta.author
        if meta.date:
            extra["published_date"] = meta.date
        if meta.sitename:
            extra["sitename"] = meta.sitename
        if meta.url and meta.url != url:
            extra["canonical_url"] = meta.url

    return Document(
        source=url,
        source_type="html",
        title=title,
        content=content,
        metadata=extra,
    )


def fetch_html(url: str) -> Document:
    return asyncio.run(afetch_html(url))
