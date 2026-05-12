"""HTML extraction tests (httpx mocked via respx)."""

from __future__ import annotations

import httpx
import respx

import crawlers

ARTICLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<title>The Cat Article</title>
<meta name="author" content="Jane Doe">
<meta name="description" content="An article about cats.">
</head>
<body>
<article>
<h1>The Cat Article</h1>
<p>Cats are wonderful creatures with whiskers and tails. They like to sleep all day
   and hunt at night. Domestic cats have been companions to humans for thousands of years.</p>
<p>The earliest domestication of cats dates back to ancient Egypt, where they were
   revered as sacred animals and even mummified alongside their owners.</p>
<p>Modern cat breeds include Persians, Siamese, Maine Coons, and many others. Each
   breed has distinct physical and behavioral traits that have been refined over generations.</p>
</article>
</body>
</html>
"""


def test_html_extraction_via_dispatch():
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://example.com/cats").mock(return_value=httpx.Response(200, text=ARTICLE_HTML))
        doc = crawlers.fetch("https://example.com/cats")

    assert doc.source == "https://example.com/cats"
    assert doc.source_type == "html"
    assert doc.title and "Cat" in doc.title
    assert "Cats are wonderful" in doc.content
    assert doc.metadata.get("author") == "Jane Doe"


def test_html_handles_empty_extraction():
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://example.com/empty").mock(return_value=httpx.Response(200, text="<html><body></body></html>"))
        doc = crawlers.fetch("https://example.com/empty")
    assert doc.source_type == "html"
    assert isinstance(doc.content, str)
