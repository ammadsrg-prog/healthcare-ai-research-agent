"""
Builds the research report: everything the app found, in one document you can download.

The AI does not write this report. Python puts together results we already have
(summaries, comparison, checked gaps), so making a report costs nothing.
The references come straight from OpenAlex, never from the AI, so they are always
real papers. AI tools sometimes invent references that don't exist; this design prevents that.
"""

from datetime import date

from src.models import Paper


def format_reference(paper: Paper) -> str:
    """Write one paper as a reference, like: Smith J, Lee K, et al. (2021). Title. Journal. Link"""
    # Up to 3 authors, then "et al." (Latin for "and others"), as in many medical journals
    authors = ", ".join(paper.authors[:3]) or "Unknown authors"
    if len(paper.authors) > 3:
        authors += ", et al."

    reference = f"{authors} ({paper.year or 'n.d.'}). {paper.title}."  # n.d. means "no date"
    if paper.journal:
        reference += f" *{paper.journal}*."  # Journal names are written in italics
    if paper.url:
        reference += f" {paper.url}"
    if paper.is_retracted:
        reference = "**[RETRACTED]** " + reference  # A warning, so nobody cites it as valid evidence
    return reference


def build_report(
    topic: str,
    papers: list[Paper],
    summaries: list[str],
    comparison: str | None,
    gaps: list[dict] | None,
) -> str:
    """Put all the results together into one report, written in Markdown.

    papers and summaries must be in the same order as when they were compared,
    so that [1] in the comparison means the same paper as [1] in the references.
    """
    lines = [
        f"# Research report: {topic}",
        "",
        f"*Made with the Healthcare AI Research Agent on {date.today():%d %B %Y}.*",
        "",
        "> **Note:** This report is for studying research, not medical advice. "
        "The summaries and comparison were written by AI from paper abstracts only, "
        "so they can contain mistakes. Check the original papers before relying on them.",
        "",
    ]

    lines += ["## 1. Papers reviewed", ""]
    for number, (paper, summary) in enumerate(zip(papers, summaries), start=1):
        lines += [f"### [{number}] {paper.title}", "", summary, ""]

    # The comparison and gaps are only added if they were made in the app
    if comparison:
        lines += ["## 2. Comparison", "", comparison, ""]

    if gaps:
        lines += [
            "## 3. Research gaps (checked against OpenAlex and ClinicalTrials.gov)",
            "",
            "The AI suggested each gap, then we counted the healthcare papers on it in OpenAlex "
            "and the active clinical trials on it in ClinicalTrials.gov. "
            "The count is a strong hint, not proof: papers using different words can be missed.",
            "",
        ]
        for gap in gaps:
            lines += [
                f"**{gap['verdict']}**: {gap['gap']}",
                "",
                f"- Searched for: `{gap['search']}`",
                f"- Healthcare papers found: {gap['count']}",
            ]
            for example in gap["examples"]:
                lines.append(f"- Example: {format_reference(example)}")
            trial_count = gap.get("trial_count")
            if trial_count is not None:
                lines.append(f"- Active clinical trials (ClinicalTrials.gov): {trial_count}")
                for trial in gap.get("trials", []):
                    lines.append(f"- Trial: {trial.title} ({trial.nct_id}, {trial.status}). {trial.url}")
            lines.append("")

    lines += ["## References", ""]
    for number, paper in enumerate(papers, start=1):
        lines.append(f"{number}. {format_reference(paper)}")

    return "\n".join(lines)
