"""PDF fetcher: download the bytes and extract text via pypdf.

Many PDFs are served from URLs that don't end in .pdf (arxiv /pdf/<id>,
openreview /pdf?id=...), so the html fetcher also content-type-sniffs and
delegates here, passing the already-downloaded bytes via `_content`.
"""

from __future__ import annotations

import asyncio
from io import BytesIO

import httpx

from ._http import build_client
from .types import Document


async def afetch_pdf(
    url: str,
    *,
    client: httpx.AsyncClient | None = None,
    _content: bytes | None = None,
) -> Document:
    if _content is None:
        own_client = client is None
        if own_client:
            client = build_client()
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.content
        finally:
            if own_client:
                await client.aclose()
    else:
        data = _content

    text, title, n_pages = await asyncio.to_thread(_extract_pdf, data)
    if not text.strip():
        raise ValueError("no extractable text from PDF (scanned/image-only?)")

    return Document(
        source=url,
        source_type="pdf",
        title=title,
        content=text,
        metadata={"pages": n_pages, "bytes": len(data)},
    )


def _extract_pdf(data: bytes) -> tuple[str, str | None, int]:
    """Sync pypdf extraction (intended to run in a thread)."""
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(BytesIO(data))
    except (PdfReadError, OSError, ValueError) as e:
        raise ValueError(f"could not parse PDF: {e}") from e

    title: str | None = None
    try:
        if reader.metadata and reader.metadata.title:
            title = str(reader.metadata.title).strip() or None
    except Exception:  # noqa: BLE001 - metadata is best-effort
        pass

    parts: list[str] = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
        except Exception:  # noqa: BLE001 - skip unreadable pages, keep the rest
            t = ""
        if t.strip():
            parts.append(t.strip())

    return "\n\n".join(parts).strip(), title, len(reader.pages)


def fetch_pdf(url: str) -> Document:
    return asyncio.run(afetch_pdf(url))
