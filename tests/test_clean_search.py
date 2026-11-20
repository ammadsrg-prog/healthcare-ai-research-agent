"""
Tests for clean_search, which repairs the AI's gap searches. Run them all with:  python -m pytest

Every "broken" example here is a real kind of mistake the AI made during testing.
"""

import pytest

from src.gap_checker import clean_search


@pytest.mark.parametrize(
    "ai_search, repaired",
    [
        # A good search is left exactly as it is
        ('"mobile app" AND diabetes AND "older adults"', '"mobile app" AND diabetes AND "older adults"'),
        # 4 concepts, a vague word and a long quoted phrase (the real mistake from the live test)
        (
            '"diabetes mobile app" AND coaching AND "certified educator" AND comparison',
            'diabetes mobile app AND coaching AND "certified educator"',
        ),
        # OR makes a search far too wide: keep only the first choice
        ('diabetes AND (app OR smartphone) AND "older adults"', 'diabetes AND app AND "older adults"'),
        # NOT is removed
        ("asthma AND children NOT adults", "asthma AND children"),
        # Lower-case "and" is still understood
        ("asthma and inhaler and adherence", "asthma AND inhaler AND adherence"),
        # More than 3 concepts: keep the first 3
        ("a1 AND b2 AND c3 AND d4 AND e5", "a1 AND b2 AND c3"),
        # Vague words are dropped, even in quotes
        ('dementia AND "effectiveness" AND music', "dementia AND music"),
        # Names with a number stay exact, or "type 1 diabetes" would also match type 2 papers
        ('"diabetes mobile app" AND "type 1 diabetes"', 'diabetes mobile app AND "type 1 diabetes"'),
    ],
)
def test_searches_are_repaired(ai_search, repaired):
    assert clean_search(ai_search) == repaired


def test_search_with_nothing_usable_is_kept():
    assert clean_search("comparison AND effectiveness") == "comparison AND effectiveness"
