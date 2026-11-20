"""
Describes the data our app works with.
"""

from dataclasses import dataclass


@dataclass
class Paper:
    """One research paper. Think of it as a form with these boxes to fill in."""

    title: str
    authors: list[str]
    abstract: str
    year: int | None
    url: str
    citation_count: int
    journal: str = ""  # Where it was published. The default "" means "unknown".
