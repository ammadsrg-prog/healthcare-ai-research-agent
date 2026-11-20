"""
Tests for the retraction alarm. Run them all with:  python -m pytest

None of these tests call OpenAlex or the AI, so they are free and fast.
"""

import pytest

from src.models import Paper
from src.openalex_client import work_to_paper
from src.report import format_reference
from src.summarizer import RetractedPaperError, summarize_paper


def make_paper(is_retracted: bool) -> Paper:
    return Paper(
        title="Mediterranean diet study",
        authors=["Ann Lee"],
        abstract="A normal abstract.",
        year=2013,
        url="https://doi.org/x",
        citation_count=100,
        is_retracted=is_retracted,
    )


def test_openalex_retracted_flag_is_read():
    # A small fake OpenAlex answer, shaped like the real one
    work = {"title": "Some study", "is_retracted": True, "abstract_inverted_index": None}
    assert work_to_paper(work).is_retracted is True


def test_missing_flag_means_not_retracted():
    assert work_to_paper({"title": "Some study"}).is_retracted is False


def test_summarizer_refuses_retracted_paper():
    # Refused BEFORE the AI is called, so this test costs nothing
    with pytest.raises(RetractedPaperError):
        summarize_paper(make_paper(is_retracted=True))


def test_reference_warns_when_retracted():
    assert format_reference(make_paper(is_retracted=True)).startswith("**[RETRACTED]**")


def test_reference_is_normal_when_not_retracted():
    assert "RETRACTED" not in format_reference(make_paper(is_retracted=False))
