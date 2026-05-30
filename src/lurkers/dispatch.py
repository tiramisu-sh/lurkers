"""URL → source-type routing and unified fetch entry point."""

from __future__ import annotations

import asyncio
from urllib.parse import urlparse

import httpx

from .types import Document

_YOUTUBE_HOSTS = {"youtube.com", "youtu.be", "m.youtube.com"}
_TWITTER_HOSTS = {
    "twitter.com", "x.com", "mobile.twitter.com",
    # Embed-friendly mirrors people paste instead of the originals; all are
    # resolvable through the fxtwitter API the twitter fetcher already uses.
    "fxtwitter.com", "fixupx.com", "vxtwitter.com", "fixvx.com", "twittpr.com",
}


def _looks_like_pdf(url: str) -> bool:
    """URL-level PDF hint. Content-type sniffing in the html fetcher catches
    the rest (e.g. PDFs served from extensionless URLs)."""
    path = urlparse(url).path.lower()
    return path.endswith(".pdf") or path == "/pdf" or "/pdf/" in path


def detect_source_type(url: str) -> str:
    """Return one of: 'youtube', 'twitter', 'pdf', or 'html' (fallback)."""
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if host in _YOUTUBE_HOSTS:
        return "youtube"
    if host in _TWITTER_HOSTS:
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
