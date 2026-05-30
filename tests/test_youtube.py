"""YouTube fetcher tests: video-id parsing + transcript mocked."""

from __future__ import annotations

import httpx
import pytest
import respx

import lurkers
from lurkers.youtube import TranscriptUnavailable, extract_video_id


def test_extract_video_id():
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("https://m.youtube.com/watch?v=abcdef") == "abcdef"
    assert extract_video_id("https://www.youtube.com/shorts/xyz123") == "xyz123"
    assert extract_video_id("https://www.youtube.com/live/ALCeJcUP8M0") == "ALCeJcUP8M0"
    assert extract_video_id("https://example.com/not-youtube") is None


class _FakeSnippet:
    def __init__(self, text: str) -> None:
        self.text = text


def test_youtube_fetch(monkeypatch):
    fake_transcript = [_FakeSnippet("Hello world."), _FakeSnippet("This is a test video.")]

    import youtube_transcript_api

    monkeypatch.setattr(
        youtube_transcript_api.YouTubeTranscriptApi,
        "fetch",
        lambda self, video_id, languages=None: fake_transcript,
    )

    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://www.youtube.com/oembed").mock(
            return_value=httpx.Response(
                200,
                json={
                    "title": "Cat Video",
                    "author_name": "Cat Channel",
                    "author_url": "https://www.youtube.com/c/cat",
                    "thumbnail_url": "https://i.ytimg.com/vi/abc/default.jpg",
                },
            )
        )
        doc = lurkers.fetch("https://www.youtube.com/watch?v=abc123")

    assert doc.source_type == "youtube"
    assert doc.title == "Cat Video"
    assert "Hello world" in doc.content
    assert "This is a test video" in doc.content
    assert doc.metadata["video_id"] == "abc123"
    assert doc.metadata["channel"] == "Cat Channel"


def test_youtube_transcript_unavailable_raises(monkeypatch):
    """A missing transcript must surface as a failure, not as fake content."""
    import youtube_transcript_api

    def _boom(self, video_id, languages=None):
        raise RuntimeError("IpBlocked")

    monkeypatch.setattr(youtube_transcript_api.YouTubeTranscriptApi, "fetch", _boom)

    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://www.youtube.com/oembed").mock(
            return_value=httpx.Response(200, json={"title": "T", "author_name": "A"})
        )
        with pytest.raises(TranscriptUnavailable):
            lurkers.fetch("https://www.youtube.com/watch?v=abc123")


def test_youtube_empty_transcript_raises(monkeypatch):
    """A transcript that fetches OK but is all-blank is also a failure, not content."""
    import youtube_transcript_api

    monkeypatch.setattr(
        youtube_transcript_api.YouTubeTranscriptApi,
        "fetch",
        lambda self, video_id, languages=None: [_FakeSnippet("   "), _FakeSnippet("")],
    )

    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://www.youtube.com/oembed").mock(
            return_value=httpx.Response(200, json={"title": "T", "author_name": "A"})
        )
        with pytest.raises(TranscriptUnavailable):
            lurkers.fetch("https://www.youtube.com/watch?v=abc123")
