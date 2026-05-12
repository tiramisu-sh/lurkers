"""lurkers CLI."""

from __future__ import annotations

import json
import sys

import typer

from .dispatch import fetch as _fetch
from .rss import feed as _feed

app = typer.Typer(
    help="Convenient API + CLI to fetch web content for agents.",
    no_args_is_help=True,
    add_completion=False,
)


@app.command("fetch")
def fetch_cmd(
    url: str = typer.Argument(..., help="URL to fetch (HTML, YouTube, or Twitter; auto-detected)."),
    pretty: bool = typer.Option(False, "--pretty", help="Indent JSON output."),
) -> None:
    """Fetch a single URL; print the Document as JSON to stdout."""
    doc = _fetch(url)
    indent = 2 if pretty else None
    sys.stdout.write(doc.model_dump_json(indent=indent))
    sys.stdout.write("\n")


@app.command("feed")
def feed_cmd(
    url: str = typer.Argument(..., help="RSS/Atom feed URL."),
    limit: int = typer.Option(None, "--limit", "-n", help="Max entries to fetch."),
    pretty: bool = typer.Option(False, "--pretty", help="Indent JSON output."),
) -> None:
    """Fetch an RSS/Atom feed; print a JSON array of Documents to stdout."""
    docs = _feed(url, limit=limit)
    payload = [d.model_dump(mode="json") for d in docs]
    indent = 2 if pretty else None
    json.dump(payload, sys.stdout, indent=indent, default=str)
    sys.stdout.write("\n")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
