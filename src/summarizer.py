"""
Turns one Paper into a short summary using the AI.
"""

from src.bedrock_client import ask_ai
from src.injection import check_paper
from src.models import Paper
from src.prompts import SUMMARY_PROMPT


class UnsafePaperError(Exception):
    """Raised when a paper looks like a prompt-injection attack, so it is never sent to the AI."""


class RetractedPaperError(Exception):
    """Raised when a paper was retracted, so the AI never presents its withdrawn findings as facts."""


def summarize_paper(paper: Paper) -> str:
    """Ask the AI to summarize a paper from its title and abstract."""
    # Backup safety checks: even if some other code forgets to check, a risky paper never reaches the AI
    if paper.is_retracted:
        raise RetractedPaperError("This paper was retracted.")
    if check_paper(paper):
        raise UnsafePaperError("This paper's text contains instructions aimed at an AI.")

    prompt = SUMMARY_PROMPT.format(title=paper.title, abstract=paper.abstract)

    # The AI occasionally sends back an incomplete answer, so we check
    # for the last heading and try once more before giving up.
    for attempt in range(2):
        summary = ask_ai(
            prompt,
            max_tokens=1000,
            task="summarize",
            untrusted=f"Title: {paper.title}\nAbstract: {paper.abstract}",  # The part the guardrail checks
        )
        if "Limitations" in summary:
            return summary

    raise ValueError("The AI did not return a complete summary.")
