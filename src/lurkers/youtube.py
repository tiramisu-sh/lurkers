"""YouTube fetcher: oEmbed for metadata + youtube-transcript-api for transcript."""

from __future__ import annotations

import asyncio
import re
from urllib.parse import parse_qs, urlparse

import httpx

from ._http import build_client
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
        m = re.match(r"^/(?:shorts|embed|v|live)/([^/?]+)", parsed.path)
        if m:
            return m.group(1)
    return None


async def afetch_youtube(url: str, *, client: httpx.AsyncClient | None = None) -> Document:
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"could not extract YouTube video id from {url!r}")

    own_client = client is None
    if own_client:
        client = build_client()
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


class TranscriptUnavailable(Exception):
    """Raised when a YouTube video has no retrievable transcript.

    Surfaced as a real failure rather than buried inside Document.content, so
    callers can distinguish "no transcript" from a genuine summary/transcript.
    """


def _fetch_transcript(video_id: str) -> str:
    """Sync transcript fetch (intended to run in a thread). Raises on failure."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError as e:  # pragma: no cover
        raise TranscriptUnavailable(f"youtube-transcript-api missing: {e}") from e
    try:
        segments = YouTubeTranscriptApi().fetch(video_id, languages=_TRANSCRIPT_LANGS)
    except Exception as e:
        raise TranscriptUnavailable(f"{type(e).__name__}: {e}") from e
    lines: list[str] = []
    for snippet in segments:
        text = getattr(snippet, "text", None) or (snippet.get("text") if isinstance(snippet, dict) else "")
        text = (text or "").strip()
        if text:
            lines.append(text)
    transcript = "\n".join(lines)
    if not transcript.strip():
        raise TranscriptUnavailable("empty transcript")
    return transcript


def fetch_youtube(url: str) -> Document:
    return asyncio.run(afetch_youtube(url))
