"""RSS/Atom feed: parse → fetch each entry's URL through the unified dispatch."""

from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET

import httpx

from .types import Document

_ATOM_NS = "{http://www.w3.org/2005/Atom}"


def parse_feed_urls(xml_text: str) -> list[str]:
    """Extract entry URLs from RSS 2.0 or Atom feed XML, in order."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise ValueError(f"invalid feed XML: {e}") from e

    urls: list[str] = []
    for item in root.iter("item"):
        link_el = item.find("link")
        if link_el is not None and link_el.text:
            urls.append(link_el.text.strip())

    for entry in root.iter(f"{_ATOM_NS}entry"):
        link_el = entry.find(f"{_ATOM_NS}link")
        if link_el is not None and "href" in link_el.attrib:
            urls.append(link_el.attrib["href"])

    return urls


async def afeed(
    feed_url: str,
    *,
    limit: int | None = None,
    skip_errors: bool = True,
    client: httpx.AsyncClient | None = None,
) -> list[Document]:
    """Fetch and parse a feed, then fetch each entry URL via the unified dispatch.

    Failed per-entry fetches are skipped silently when skip_errors=True (default).
    """
    from .dispatch import afetch

    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; lurkers/0.1)"},
        )
    try:
        resp = await client.get(feed_url)
        resp.raise_for_status()
        urls = parse_feed_urls(resp.text)
        if limit is not None:
            urls = urls[:limit]

        async def safe_fetch(u: str) -> Document | None:
            try:
                return await afetch(u, client=client)
            except Exception:
                if skip_errors:
                    return None
                raise

        results = await asyncio.gather(*[safe_fetch(u) for u in urls])
        return [d for d in results if d is not None]
    finally:
        if own_client:
            await client.aclose()


def feed(feed_url: str, *, limit: int | None = None, skip_errors: bool = True) -> list[Document]:
    return asyncio.run(afeed(feed_url, limit=limit, skip_errors=skip_errors))
