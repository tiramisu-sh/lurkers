"""RSS feed tests (httpx mocked)."""

from __future__ import annotations

import httpx
import respx

import lurkers
from lurkers.rss import parse_feed_urls

RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>Example Feed</title>
<link>https://example.com/</link>
<item><title>First</title><link>https://example.com/a1</link></item>
<item><title>Second</title><link>https://example.com/a2</link></item>
</channel>
</rss>
"""

ATOM_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<title>Atom Feed</title>
<entry><title>One</title><link href="https://example.com/atom-1"/></entry>
<entry><title>Two</title><link href="https://example.com/atom-2"/></entry>
</feed>
"""

ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html><head><title>{title}</title></head>
<body><article><h1>{title}</h1>
<p>{title} body. This is a long enough paragraph for trafilatura to actually
extract it. Repeat repeat repeat repeat repeat repeat repeat repeat repeat
repeat repeat repeat repeat repeat repeat repeat repeat repeat repeat.</p>
</article></body></html>
"""


def test_parse_rss_urls():
    urls = parse_feed_urls(RSS_XML)
    assert urls == ["https://example.com/a1", "https://example.com/a2"]


def test_parse_atom_urls():
    urls = parse_feed_urls(ATOM_XML)
    assert urls == ["https://example.com/atom-1", "https://example.com/atom-2"]


def test_feed_fetches_each_entry():
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://example.com/rss.xml").mock(return_value=httpx.Response(200, text=RSS_XML))
        mock.get("https://example.com/a1").mock(
            return_value=httpx.Response(200, text=ARTICLE_TEMPLATE.format(title="First"))
        )
        mock.get("https://example.com/a2").mock(
            return_value=httpx.Response(200, text=ARTICLE_TEMPLATE.format(title="Second"))
        )
        docs = lurkers.feed("https://example.com/rss.xml")

    assert len(docs) == 2
    assert {d.source for d in docs} == {"https://example.com/a1", "https://example.com/a2"}
    assert all(d.source_type == "html" for d in docs)


def test_feed_with_limit():
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://example.com/rss.xml").mock(return_value=httpx.Response(200, text=RSS_XML))
        mock.get("https://example.com/a1").mock(
            return_value=httpx.Response(200, text=ARTICLE_TEMPLATE.format(title="First"))
        )
        docs = lurkers.feed("https://example.com/rss.xml", limit=1)
    assert len(docs) == 1
    assert docs[0].source == "https://example.com/a1"
