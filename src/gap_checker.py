"""
The gap checker: the AI suggests research gaps, then we check each one against real papers.

Most AI tools simply trust the AI. This file tests the AI's claims with real data:
if many papers already exist on a "gap", it probably isn't a real gap.
It also checks ClinicalTrials.gov, to show whether someone is studying the gap right now.
"""

import json
import re

import requests

from src.analyzer import number_papers
from src.bedrock_client import ask_ai
from src.models import Paper
from src.openalex_client import count_papers
from src.prompts import GAP_PROMPT
from src.trials_client import count_active_trials


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
    papers_text = number_papers(papers, summaries)
    prompt = GAP_PROMPT.format(papers=papers_text)

    # Same pattern as the summaries: check the answer, and try once more if it's broken
    for attempt in range(2):
        gaps = read_gaps(ask_ai(prompt, max_tokens=1000, task="suggest gaps", untrusted=papers_text))
        if gaps:
            return gaps

    raise ValueError("The AI did not return gaps we could read.")


# Words that describe the kind of study, not the topic. Papers rarely use them in a way a search can match,
# so a search that requires them finds almost nothing and makes every gap look "real".
VAGUE_WORDS = {
    "comparison", "compare", "effectiveness", "effective", "efficacy", "impact", "effect", "effects",
    "study", "studies", "research", "evidence", "outcomes", "analysis", "role", "use",
}
MAX_CONCEPTS = 3


def clean_search(query: str) -> str:
    """Repair the AI's search so it follows our rules, even when the AI ignored them.

    The prompt asks for 2 or 3 short concepts joined by AND, but the AI sometimes writes
    4 concepts, uses OR, or quotes long phrases like "diabetes mobile app". A quoted phrase
    must appear word for word, so long ones match almost nothing. Rules in a prompt are requests;
    checking in code is a guarantee.

    Example: '"diabetes mobile app" AND coaching AND "certified educator" AND comparison'
          -> 'diabetes mobile app AND coaching AND "certified educator"'
    """
    concepts = []
    for part in re.split(r"\s+AND\s+", query, flags=re.IGNORECASE):  # Split at every AND
        part = re.split(r"\s+(?:OR|NOT)\s+", part, flags=re.IGNORECASE)[0]  # Keep only the first choice of an OR
        part = part.strip(" ()")
        words = part.strip('"').split()

        if not words or part.lower().strip('"') in VAGUE_WORDS:
            continue  # Skip empty and vague concepts
        has_number = any(character.isdigit() for character in part)
        if len(words) >= 3 and not has_number:
            part = " ".join(words)  # 3+ words: remove the quotes, so the words can appear in any order
        elif len(words) >= 3:
            # Names with a number, like "type 1 diabetes" or "COVID 19", must stay exact:
            # without quotes, "type 1 diabetes" would also match papers about type 2 diabetes
            part = f'"{" ".join(words)}"'
        elif len(words) == 2:
            part = f'"{" ".join(words)}"'  # 2 words: keep them together as a phrase
        else:
            part = words[0]
        concepts.append(part)

    if not concepts:
        return query  # Nothing usable was left, so keep the AI's original
    return " AND ".join(concepts[:MAX_CONCEPTS])


def verdict(count: int) -> str:
    """Turn a number of matching papers into a simple verdict."""
    if count <= 10:
        return "🟢 Likely a real gap"
    if count <= 50:
        return "🟡 Partly studied"
    return "🔴 Already well studied"


def check_gaps(papers: list[Paper], summaries: list[str]) -> list[dict]:
    """Suggest gaps with the AI, then check each one against published papers and running trials."""
    gaps = suggest_gaps(papers, summaries)

    for gap in gaps:
        # 0. Repair the AI's search if it broke our rules. The original is kept, to show what changed.
        gap["ai_search"] = gap["search"]
        gap["search"] = clean_search(gap["search"])

        # 1. Finished research: published papers in OpenAlex
        count, examples = count_papers(gap["search"])
        gap["count"] = count
        gap["examples"] = examples
        gap["verdict"] = verdict(count)

        # 2. Research happening now: active clinical trials. This is extra information,
        # so if ClinicalTrials.gov is down, the gap check still works ("None" means "couldn't check").
        try:
            gap["trial_count"], gap["trials"] = count_active_trials(gap["search"])
        except requests.RequestException:
            gap["trial_count"], gap["trials"] = None, []

    return gaps
