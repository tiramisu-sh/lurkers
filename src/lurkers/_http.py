"""Shared HTTP client configuration for the fetchers.

Every fetcher builds its client via `build_client()` so they share one
User-Agent and timeout policy. This matters: several sites — and Cloudflare-
fronted APIs like fxtwitter — reject the default library User-Agent with a 403
("Just a moment..." challenge page). A non-default UA gets through.
"""

from __future__ import annotations

import httpx

# A real browser User-Agent. Many sites (Medium, Substack, openai.com, news
# paywalls, Cloudflare-fronted APIs) return 403 to non-browser UAs, so we
# present as a current Chrome to maximize what we can actually fetch.
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
DEFAULT_TIMEOUT = 30.0


def build_client() -> httpx.AsyncClient:
    """An httpx.AsyncClient with lurkers' default headers, timeout, and redirects."""
    return httpx.AsyncClient(
        headers=DEFAULT_HEADERS,
        timeout=DEFAULT_TIMEOUT,
        follow_redirects=True,
    )
