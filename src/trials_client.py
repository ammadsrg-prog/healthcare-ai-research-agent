"""
Talks to ClinicalTrials.gov: finds clinical trials that are running right now.

A paper describes research that is finished. A clinical trial that is recruiting
describes research that is happening NOW. So for each research gap, this tells us:
"Is someone already working on this?"

ClinicalTrials.gov is run by the US National Library of Medicine. It is free and needs no key.
"""

import requests

from src.models import Trial

TRIALS_URL = "https://clinicaltrials.gov/api/v2/studies"

# Trials that are still going on. Finished, stopped and withdrawn trials are left out.
ACTIVE_STATUSES = ["RECRUITING", "NOT_YET_RECRUITING", "ACTIVE_NOT_RECRUITING", "ENROLLING_BY_INVITATION"]


def study_to_trial(study: dict) -> Trial:
    """Copy the fields we need from one ClinicalTrials.gov result into a Trial."""
    protocol = study.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    nct_id = identification.get("nctId", "")

    return Trial(
        nct_id=nct_id,
        title=identification.get("briefTitle") or "Untitled trial",
        # "NOT_YET_RECRUITING" becomes "Not yet recruiting"
        status=status.get("overallStatus", "").replace("_", " ").capitalize(),
        start_date=status.get("startDateStruct", {}).get("date", ""),
        url=f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "",
    )


def count_active_trials(query: str, examples: int = 3) -> tuple[int, list[Trial]]:
    """Count the active clinical trials that match a search, and return a few of them.

    The query can use AND and "quotes", like the gap checker's searches.
    """
    response = requests.get(
        TRIALS_URL,
        params={
            "query.term": query,
            "filter.overallStatus": ",".join(ACTIVE_STATUSES),
            "countTotal": "true",  # Ask for the total number of matches, not only the first page
            "pageSize": examples,
            "fields": "NCTId,BriefTitle,OverallStatus,StartDate",  # Only the fields we use, so the answer is small
        },
        timeout=30,
    )
    response.raise_for_status()  # Stop with an error if the request failed
    answer = response.json()
    trials = [study_to_trial(study) for study in answer.get("studies", [])]
    return answer.get("totalCount", 0), trials
