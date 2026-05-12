"""URL → source-type routing tests."""

from __future__ import annotations

import crawlers


def test_detect_youtube():
    assert crawlers.detect_source_type("https://www.youtube.com/watch?v=abc") == "youtube"
    assert crawlers.detect_source_type("https://youtu.be/abc") == "youtube"
    assert crawlers.detect_source_type("https://m.youtube.com/watch?v=xyz") == "youtube"
    assert crawlers.detect_source_type("https://www.youtube.com/shorts/xyz") == "youtube"


def test_detect_twitter():
    assert crawlers.detect_source_type("https://twitter.com/user/status/123") == "twitter"
    assert crawlers.detect_source_type("https://x.com/user/status/123") == "twitter"
    assert crawlers.detect_source_type("https://mobile.twitter.com/u/status/1") == "twitter"


def test_detect_html_fallback():
    assert crawlers.detect_source_type("https://example.com/article") == "html"
    assert crawlers.detect_source_type("https://news.ycombinator.com/item?id=1") == "html"
    assert crawlers.detect_source_type("https://www.bbc.co.uk/news/123") == "html"
