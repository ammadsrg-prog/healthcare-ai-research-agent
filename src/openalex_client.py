"""
Talks to the OpenAlex API: sends a search and turns the results into Paper objects.
"""

import requests

from config.settings import OPENALEX_API_KEY
from src.models import Paper

OPENALEX_URL = "https://api.openalex.org/works"

# OpenAlex sorts every paper into a research field, each with an ID number.
# These are the health fields, so our searches only return healthcare research.
HEALTH_FIELDS = {
    "27": "Medicine",
    "29": "Nursing",
    "30": "Pharmacology, Toxicology and Pharmaceutics",
    "35": "Dentistry",
    "36": "Health Professions",
}

# Two rules for OpenAlex, joined by a comma (which means AND):
#   1. the paper's main field must be one of the health fields ("|" means OR)
#   2. the paper must have an abstract, so the AI always has something to read
HEALTH_FILTER = "primary_topic.field.id:" + "|".join(HEALTH_FIELDS) + ",has_abstract:true"


def rebuild_abstract(inverted_index: dict | None) -> str:
    """Turn OpenAlex's scrambled abstract back into normal text.

    OpenAlex stores each word with the positions where it appears, like
    {"AI": [0], "helps": [1], "doctors": [2]}. We put each word back in its place.
    """
    if not inverted_index:
        return ""

    positioned_words = []
    for word, positions in inverted_index.items():
        for position in positions:
            positioned_words.append((position, word))

    positioned_words.sort()
    return " ".join(word for position, word in positioned_words)


def work_to_paper(work: dict) -> Paper:
    """Copy the fields we care about from one OpenAlex result into a Paper."""
    authors = []
    for authorship in work.get("authorships", []):
        authors.append(authorship["author"]["display_name"])

    # The journal's name is a few levels deep, and any level can be empty, so "or {}" avoids a crash
    source = (work.get("primary_location") or {}).get("source") or {}

    return Paper(
        title=work.get("title") or "Untitled",
        authors=authors,
        abstract=rebuild_abstract(work.get("abstract_inverted_index")),
        year=work.get("publication_year"),
        url=work.get("doi") or work.get("id") or "",
        citation_count=work.get("cited_by_count", 0),
        journal=source.get("display_name") or "",
    )


def ask_openalex(params: dict) -> dict:
    """Send one request to OpenAlex and return its raw answer."""
    if OPENALEX_API_KEY:
        params["api_key"] = OPENALEX_API_KEY

    response = requests.get(OPENALEX_URL, params=params, timeout=30)
    response.raise_for_status()  # Stop with an error if the request failed
    return response.json()


def search_papers(query: str, limit: int = 10) -> list[Paper]:
    """Search OpenAlex for healthcare papers on a topic and return a list of Papers."""
    answer = ask_openalex({"search": query, "per_page": limit, "filter": HEALTH_FILTER})
    return [work_to_paper(work) for work in answer["results"]]


def count_papers(query: str, examples: int = 3) -> tuple[int, list[Paper]]:
    """Count how many healthcare papers match a search, and return a few of them.

    The gap checker uses this to see whether a "gap" has already been studied.
    It only looks in titles and abstracts. The normal search also looks inside
    full papers, where a word mentioned once in passing would count as a match.
    """
    # Inside a filter, a comma means "and another rule", so we remove commas from the query
    clean_query = query.replace(",", " ")
    title_and_abstract_filter = HEALTH_FILTER + ",title_and_abstract.search:" + clean_query
    answer = ask_openalex({"filter": title_and_abstract_filter, "per_page": examples})
    total = answer["meta"]["count"]  # OpenAlex tells us how many papers matched in total
    papers = [work_to_paper(work) for work in answer["results"]]
    return total, papers
