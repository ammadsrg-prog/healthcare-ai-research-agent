"""
Compares several summarized papers to find shared findings, differences and research gaps.
"""

from src.bedrock_client import ask_ai
from src.models import Paper
from src.prompts import COMPARISON_PROMPT


def number_papers(papers: list[Paper], summaries: list[str]) -> str:
    """Write each paper as a numbered block of text, like "[1] Title (2021)" plus its summary.

    Both the comparison and the gap checker send papers to the AI this way.
    """
    paper_texts = []
    for number, (paper, summary) in enumerate(zip(papers, summaries), start=1):
        paper_texts.append(f"[{number}] {paper.title} ({paper.year or 'year unknown'})\n{summary}")
    return "\n\n".join(paper_texts)


def compare_papers(papers: list[Paper], summaries: list[str]) -> str:
    """Ask the AI to compare papers, using the summary written for each one."""
    papers_text = number_papers(papers, summaries)
    prompt = COMPARISON_PROMPT.format(papers=papers_text)

    # Like the summaries, we check the answer reached the last heading
    # and try once more before giving up.
    for attempt in range(2):
        comparison = ask_ai(prompt, max_tokens=2000, task="compare", untrusted=papers_text)
        if "Research gaps" in comparison:
            return comparison

    raise ValueError("The AI did not return a complete comparison.")
