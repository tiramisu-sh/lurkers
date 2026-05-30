"""Twitter/X fetcher tests (fxtwitter mocked)."""

from __future__ import annotations

import httpx
import respx

import lurkers
from lurkers.twitter import parse_tweet_url


def test_parse_tweet_url():
    assert parse_tweet_url("https://twitter.com/elonmusk/status/123") == ("elonmusk", "123")
    assert parse_tweet_url("https://x.com/elonmusk/status/456") == ("elonmusk", "456")
    assert parse_tweet_url("https://mobile.twitter.com/jack/status/789") == ("jack", "789")
    assert parse_tweet_url("https://twitter.com/elonmusk") is None
    assert parse_tweet_url("https://example.com/foo") is None


def test_parse_tweet_url_mirrors():
    assert parse_tweet_url("https://fxtwitter.com/elonmusk/status/123") == ("elonmusk", "123")
    assert parse_tweet_url("https://fixupx.com/jack/status/456") == ("jack", "456")
    assert parse_tweet_url("https://vxtwitter.com/a/status/789") == ("a", "789")


def test_twitter_fetch_via_fxtwitter():
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://api.fxtwitter.com/elonmusk/status/12345").mock(
            return_value=httpx.Response(
                200,
                json={
                    "tweet": {
                        "text": "Just had a great day. Cats are wonderful!",
                        "author": {"screen_name": "elonmusk", "name": "Elon Musk"},
                        "likes": 1234,
                        "retweets": 56,
                        "replies": 12,
                        "views": 9999,
                        "created_at": "2026-05-01T12:00:00Z",
                    }
                },
            )
        )
        doc = lurkers.fetch("https://x.com/elonmusk/status/12345")

    assert doc.source_type == "twitter"
    assert "Cats are wonderful" in doc.content
    assert doc.metadata["author_handle"] == "elonmusk"
    assert doc.metadata["likes"] == 1234
    assert doc.metadata["tweet_id"] == "12345"
