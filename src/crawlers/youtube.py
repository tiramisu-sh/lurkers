"""YouTube fetcher: oEmbed for metadata + youtube-transcript-api for transcript."""

from __future__ import annotations

import asyncio
import re
from urllib.parse import parse_qs, urlparse

import httpx

from .types import Document

_OEMBED_URL = "https://www.youtube.com/oembed"
_TRANSCRIPT_LANGS = ["en", "en-US", "en-GB", "en-CA", "en-AU"]


def extract_video_id(url: str) -> str | None:
    """Extract a YouTube video id from a URL, or return None."""
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.").removeprefix("m.")
    if host == "youtu.be":
        return parsed.path.lstrip("/").split("/")[0] or None
    if host == "youtube.com":
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        m = re.match(r"^/(?:shorts|embed|v)/([^/?]+)", parsed.path)
        if m:
            return m.group(1)
    return None


async def afetch_youtube(url: str, *, client: httpx.AsyncClient | None = None) -> Document:
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"could not extract YouTube video id from {url!r}")

    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)
    try:
        resp = await client.get(
            _OEMBED_URL,
            params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"},
        )
        resp.raise_for_status()
        meta = resp.json()
    finally:
        if own_client:
            await client.aclose()

    transcript_text = await asyncio.to_thread(_fetch_transcript, video_id)

    title = meta.get("title")
    author = meta.get("author_name")
    parts: list[str] = []
    if title:
        parts.append(f"# {title}")
    if author:
        parts.append(f"by {author}")
    parts.append("")
    parts.append(transcript_text)

    return Document(
        source=url,
        source_type="youtube",
        title=title,
        content="\n".join(parts).strip(),
        metadata={
            "video_id": video_id,
            "channel": author,
            "channel_url": meta.get("author_url"),
            "thumbnail_url": meta.get("thumbnail_url"),
        },
    )


def _fetch_transcript(video_id: str) -> str:
    """Sync transcript fetch (intended to run in a thread)."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError as e:
        return f"(transcript unavailable: youtube-transcript-api missing: {e})"
    try:
        segments = YouTubeTranscriptApi().fetch(video_id, languages=_TRANSCRIPT_LANGS)
    except Exception as e:
        return f"(transcript unavailable: {type(e).__name__}: {e})"
    lines: list[str] = []
    for snippet in segments:
        text = getattr(snippet, "text", None) or (snippet.get("text") if isinstance(snippet, dict) else "")
        text = (text or "").strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


def fetch_youtube(url: str) -> Document:
    return asyncio.run(afetch_youtube(url))
