"""Core types for crawlers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Document(BaseModel):
    """A fetched piece of content from anywhere on the web."""

    source: str
    source_type: str
    title: str | None = None
    content: str
    fetched_at: datetime = Field(default_factory=_utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
