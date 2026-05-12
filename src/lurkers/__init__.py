"""lurkers: convenient API + CLI to fetch web content for agents."""

from .dispatch import afetch, detect_source_type, fetch
from .rss import afeed, feed
from .types import Document

__all__ = ["Document", "afeed", "afetch", "detect_source_type", "feed", "fetch"]
__version__ = "0.1.0"
