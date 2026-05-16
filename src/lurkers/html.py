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
        html = resp.text
    finally:
        if own_client:
            await client.aclose()

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
