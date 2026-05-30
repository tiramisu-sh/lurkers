"""Twitter/X fetcher via the fxtwitter public API (no auth)."""

from __future__ import annotations

import asyncio
import re

import httpx

from ._http import build_client
from .types import Document

# Single source of truth for tweet hosts: the originals plus embed-friendly
# mirrors people paste instead of them. Both the routing host-set (dispatch)
# and the parse regex are derived from this, so they can't drift apart.
_TWEET_HOST_BASES = ("twitter", "x", "fxtwitter", "fixupx", "vxtwitter", "fixvx", "twittpr")
TWEET_HOSTS = frozenset(f"{base}.com" for base in _TWEET_HOST_BASES) | {"mobile.twitter.com"}
_TWEET_RE = re.compile(
    r"^https?://(?:www\.|mobile\.)?(?:" + "|".join(_TWEET_HOST_BASES) + r")\.com"
    r"/([^/]+)/status/(\d+)",
    re.IGNORECASE,
)
_FXTWITTER_API = "https://api.fxtwitter.com"


def parse_tweet_url(url: str) -> tuple[str, str] | None:
    """Return (username, tweet_id) or None if URL is not a tweet."""
    m = _TWEET_RE.match(url)
    if not m:
        return None
    return m.group(1), m.group(2)


async def afetch_twitter(url: str, *, client: httpx.AsyncClient | None = None) -> Document:
    parsed = parse_tweet_url(url)
    if not parsed:
        raise ValueError(f"could not parse tweet URL: {url!r}")
    username, tweet_id = parsed
    api_url = f"{_FXTWITTER_API}/{username}/status/{tweet_id}"

    own_client = client is None
    if own_client:
        client = build_client()
    try:
        resp = await client.get(api_url)
        resp.raise_for_status()
        data = resp.json()
    finally:
        if own_client:
            await client.aclose()

    tweet = data.get("tweet") or {}
    text = tweet.get("text") or ""
    author = tweet.get("author") or {}
    handle = author.get("screen_name") or username
    name = author.get("name", "")
    snippet = text.replace("\n", " ")[:80]
    title = f"@{handle}: {snippet}{'...' if len(text) > 80 else ''}"

    return Document(
        source=url,
        source_type="twitter",
        title=title,
        content=text,
        metadata={
            "tweet_id": tweet_id,
            "author_handle": handle,
            "author_name": name,
            "likes": tweet.get("likes"),
            "retweets": tweet.get("retweets"),
            "replies": tweet.get("replies"),
            "views": tweet.get("views"),
            "created_at": tweet.get("created_at"),
        },
    )


def fetch_twitter(url: str) -> Document:
    return asyncio.run(afetch_twitter(url))
