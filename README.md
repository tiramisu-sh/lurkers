# lurkers

[![PyPI](https://img.shields.io/pypi/v/lurkers.svg)](https://pypi.org/project/lurkers/)
[![CI](https://github.com/tiramisu-sh/lurkers/actions/workflows/ci.yml/badge.svg)](https://github.com/tiramisu-sh/lurkers/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/lurkers.svg)](https://pypi.org/project/lurkers/)
[![Downloads](https://img.shields.io/pypi/dm/lurkers.svg)](https://pypi.org/project/lurkers/)

Convenient API + CLI to fetch web content for agents.

> **Status: early PoC.** APIs will change.

## Sources

- **HTML** pages (any URL) — extracted to markdown via [trafilatura](https://trafilatura.readthedocs.io/)
- **YouTube** videos — title + channel + transcript
- **Twitter/X** posts — via [fxtwitter](https://fxtwitter.com/) (no auth required)
- **RSS/Atom feeds** — list of entries, each fetched through the unified dispatch

## Install

```bash
pip install lurkers
```

## Python

```python
import lurkers

# unified entry point — auto-detects source type
doc = lurkers.fetch("https://news.ycombinator.com/item?id=1")
doc = lurkers.fetch("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
doc = lurkers.fetch("https://x.com/elonmusk/status/12345")

# RSS / Atom: returns list[Document]
docs = lurkers.feed("https://news.ycombinator.com/rss", limit=10)

# async siblings — afetch / afeed mirror fetch / feed
import asyncio
doc = asyncio.run(lurkers.afetch("https://news.ycombinator.com/item?id=1"))
docs = asyncio.run(lurkers.afeed("https://example.com/rss.xml"))
```

Every fetch returns a `Document`:

```python
class Document(BaseModel):
    source: str               # canonical URL
    source_type: str          # "html" | "youtube" | "twitter"
    title: str | None
    content: str              # markdown / plain text
    fetched_at: datetime
    metadata: dict[str, Any]  # source-specific (video_id, author_handle, ...)
```

## CLI

```bash
lurkers fetch https://example.com/article            # JSON to stdout
lurkers fetch https://youtu.be/dQw4w9WgXcQ --pretty
lurkers feed https://news.ycombinator.com/rss -n 5
```

## License

[Apache-2.0](LICENSE).
