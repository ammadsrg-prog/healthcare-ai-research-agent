"""
The gap checker: the AI suggests research gaps, then we check each one against real papers.

Most AI tools simply trust the AI. This file tests the AI's claims with real data:
if many papers already exist on a "gap", it probably isn't a real gap.
"""

import json

from src.analyzer import number_papers
from src.bedrock_client import ask_ai
from src.models import Paper
from src.openalex_client import count_papers
from src.prompts import GAP_PROMPT


def read_gaps(answer: str) -> list[dict]:
    """Pull the list of gaps out of the AI's answer. Returns [] if it can't be read."""
    # The AI sometimes adds words around the JSON, so we cut out the part
    # from the first "[" to the last "]".
    start = answer.find("[")
    end = answer.rfind("]")
    if start == -1 or end == -1:
        return []

    try:
        items = json.loads(answer[start : end + 1])  # turn JSON text into Python lists and dicts
    except json.JSONDecodeError:
        return []

    # Keep only items that have both a gap and a search
    return [item for item in items if isinstance(item, dict) and item.get("gap") and item.get("search")]


def suggest_gaps(papers: list[Paper], summaries: list[str]) -> list[dict]:
    """Ask the AI to suggest research gaps, each with a search query to check it."""
    prompt = GAP_PROMPT.format(papers=number_papers(papers, summaries))

    # Same pattern as the summaries: check the answer, and try once more if it's broken
    for attempt in range(2):
        gaps = read_gaps(ask_ai(prompt, max_tokens=1000))
        if gaps:
            return gaps

    raise ValueError("The AI did not return gaps we could read.")


def verdict(count: int) -> str:
    """Turn a number of matching papers into a simple verdict."""
    if count <= 10:
        return "🟢 Likely a real gap"
    if count <= 50:
        return "🟡 Partly studied"
    return "🔴 Already well studied"


def check_gaps(papers: list[Paper], summaries: list[str]) -> list[dict]:
    """Suggest gaps with the AI, then search OpenAlex to check each one."""
    gaps = suggest_gaps(papers, summaries)

    for gap in gaps:
        count, examples = count_papers(gap["search"])
        gap["count"] = count
        gap["examples"] = examples
        gap["verdict"] = verdict(count)

    return gaps
