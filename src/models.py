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
    is_retracted: bool = False  # True if the paper was officially withdrawn (for errors or fraud)


@dataclass
class Trial:
    """One clinical trial from ClinicalTrials.gov: a study that is testing a treatment on people."""

    nct_id: str  # The trial's official ID, like "NCT05041907"
    title: str
    status: str  # Like "Recruiting" (looking for patients now)
    start_date: str  # Like "2024-07" or "" if unknown
    url: str
