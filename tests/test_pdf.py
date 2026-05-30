"""PDF fetcher tests (HTTP mocked; PDFs synthesized in-memory)."""

from __future__ import annotations

import httpx
import pytest
import respx

import lurkers


def _tiny_pdf(text: str = "Hello lurkers PDF") -> bytes:
    """Build a minimal one-page PDF with a single line of extractable text."""
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
    ]
    stream = b"BT /F1 24 Tf 72 720 Td (" + text.encode() + b") Tj ET"
    objs.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += str(i).encode() + b" 0 obj\n" + body + b"\nendobj\n"
    xref_pos = len(out)
    n = len(objs) + 1
    out += b"xref\n0 " + str(n).encode() + b"\n0000000000 65535 f \n"
    for off in offsets:
        out += ("%010d 00000 n \n" % off).encode()
    out += b"trailer\n<< /Size " + str(n).encode() + b" /Root 1 0 R >>\nstartxref\n" + str(xref_pos).encode() + b"\n%%EOF"
    return bytes(out)


def test_pdf_fetch_by_url():
    pdf = _tiny_pdf("Quarterly results were strong.")
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://example.com/report.pdf").mock(
            return_value=httpx.Response(200, content=pdf, headers={"content-type": "application/pdf"})
        )
        doc = lurkers.fetch("https://example.com/report.pdf")

    assert doc.source_type == "pdf"
    assert "Quarterly results were strong." in doc.content
    assert doc.metadata["pages"] == 1


def test_html_route_delegates_pdf_by_content_type():
    """A non-.pdf URL that serves application/pdf is still handled as a PDF."""
    pdf = _tiny_pdf("Served from an extensionless URL.")
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://example.com/download").mock(
            return_value=httpx.Response(200, content=pdf, headers={"content-type": "application/pdf"})
        )
        doc = lurkers.fetch("https://example.com/download")

    assert doc.source_type == "pdf"
    assert "extensionless URL" in doc.content


def test_pdf_no_text_raises():
    """An image-only / textless PDF must fail rather than return empty content."""
    pdf = _tiny_pdf("")  # empty text operand -> no extractable text
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://example.com/scan.pdf").mock(
            return_value=httpx.Response(200, content=pdf, headers={"content-type": "application/pdf"})
        )
        with pytest.raises(ValueError):
            lurkers.fetch("https://example.com/scan.pdf")
