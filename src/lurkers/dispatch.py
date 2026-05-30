"""URL → source-type routing and unified fetch entry point."""

from __future__ import annotations

import asyncio
from urllib.parse import urlparse

import httpx

from .twitter import TWEET_HOSTS
from .types import Document

_YOUTUBE_HOSTS = {"youtube.com", "youtu.be", "m.youtube.com"}


def _looks_like_pdf(url: str) -> bool:
    """Conservative URL-level PDF hint: only obvious PDF URLs. Pages that merely
    contain '/pdf/' somewhere in the path (e.g. /pdf/viewer/<article>) are left
    to the html fetcher, whose content-type sniff still catches real PDFs served
    from extensionless URLs like arxiv.org/pdf/<id>."""
    path = urlparse(url).path.lower()
    return path.endswith(".pdf") or path.rstrip("/") == "/pdf"


def detect_source_type(url: str) -> str:
    """Return one of: 'youtube', 'twitter', 'pdf', or 'html' (fallback)."""
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if host in _YOUTUBE_HOSTS:
        return "youtube"
    if host in TWEET_HOSTS:
        return "twitter"
    if _looks_like_pdf(url):
        return "pdf"
    return "html"


async def afetch(url: str, *, client: httpx.AsyncClient | None = None) -> Document:
    """Async unified fetch. Auto-dispatches by URL pattern."""
    source_type = detect_source_type(url)
    if source_type == "youtube":
        from .youtube import afetch_youtube

        return await afetch_youtube(url, client=client)
    if source_type == "twitter":
        from .twitter import afetch_twitter

        return await afetch_twitter(url, client=client)
    if source_type == "pdf":
        from .pdf import afetch_pdf

        return await afetch_pdf(url, client=client)
    from .html import afetch_html

    return await afetch_html(url, client=client)


def fetch(url: str) -> Document:
    """Sync unified fetch. Wraps afetch via asyncio.run."""
    return asyncio.run(afetch(url))
