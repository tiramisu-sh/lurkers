"""Shared HTTP client configuration for the fetchers.

Every fetcher builds its client via `build_client()` so they share one
User-Agent and timeout policy. This matters: several sites — and Cloudflare-
fronted APIs like fxtwitter — reject the default library User-Agent with a 403
("Just a moment..." challenge page). A non-default UA gets through.
"""

from __future__ import annotations

import httpx

USER_AGENT = "Mozilla/5.0 (compatible; lurkers/0.1; +https://github.com/tiramisu-sh/lurkers)"
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml,*/*",
}
DEFAULT_TIMEOUT = 30.0


def build_client() -> httpx.AsyncClient:
    """An httpx.AsyncClient with lurkers' default headers, timeout, and redirects."""
    return httpx.AsyncClient(
        headers=DEFAULT_HEADERS,
        timeout=DEFAULT_TIMEOUT,
        follow_redirects=True,
    )
