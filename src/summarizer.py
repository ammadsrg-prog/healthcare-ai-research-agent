"""
Turns one Paper into a short summary using the AI.
"""

from src.bedrock_client import ask_ai
from src.models import Paper
from src.prompts import SUMMARY_PROMPT


def summarize_paper(paper: Paper) -> str:
    """Ask the AI to summarize a paper from its title and abstract."""
    prompt = SUMMARY_PROMPT.format(title=paper.title, abstract=paper.abstract)

    # The AI occasionally sends back an incomplete answer, so we check
    # for the last heading and try once more before giving up.
    for attempt in range(2):
        summary = ask_ai(prompt, max_tokens=1000)
        if "Limitations" in summary:
            return summary

    raise ValueError("The AI did not return a complete summary.")
