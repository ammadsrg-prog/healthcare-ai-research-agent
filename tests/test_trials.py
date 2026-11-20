"""
Tests for the clinical trials check. Run them all with:  python -m pytest

None of these tests call ClinicalTrials.gov, OpenAlex or the AI: monkeypatch swaps
those functions for fake ones during the test, so the tests are free and always give the same result.
"""

import requests

import src.gap_checker as gap_checker
from src.trials_client import study_to_trial

# A small fake ClinicalTrials.gov result, shaped like the real one
FAKE_STUDY = {
    "protocolSection": {
        "identificationModule": {"nctId": "NCT05041907", "briefTitle": "Finding Treatments for COVID-19"},
        "statusModule": {"overallStatus": "NOT_YET_RECRUITING", "startDateStruct": {"date": "2021-09-30"}},
    }
}


def test_study_is_turned_into_a_trial():
    trial = study_to_trial(FAKE_STUDY)
    assert trial.nct_id == "NCT05041907"
    assert trial.title == "Finding Treatments for COVID-19"
    assert trial.status == "Not yet recruiting"
    assert trial.start_date == "2021-09-30"
    assert trial.url == "https://clinicaltrials.gov/study/NCT05041907"


def test_missing_fields_do_not_crash():
    trial = study_to_trial({})
    assert trial.title == "Untitled trial"
    assert trial.url == ""


def use_fake_gaps(monkeypatch):
    """Replace the AI and OpenAlex with fakes that return fixed answers."""
    monkeypatch.setattr(gap_checker, "suggest_gaps", lambda papers, summaries: [{"gap": "A gap", "search": "x AND y"}])
    monkeypatch.setattr(gap_checker, "count_papers", lambda query: (5, []))


def test_gap_gets_trial_results(monkeypatch):
    use_fake_gaps(monkeypatch)
    monkeypatch.setattr(gap_checker, "count_active_trials", lambda query: (2, ["trial 1", "trial 2"]))

    gap = gap_checker.check_gaps([], [])[0]
    assert gap["verdict"] == "🟢 Likely a real gap"
    assert gap["trial_count"] == 2
    assert gap["trials"] == ["trial 1", "trial 2"]


def test_gap_check_still_works_when_trials_site_is_down(monkeypatch):
    use_fake_gaps(monkeypatch)

    def site_down(query):
        raise requests.ConnectionError("ClinicalTrials.gov is down")

    monkeypatch.setattr(gap_checker, "count_active_trials", site_down)

    gap = gap_checker.check_gaps([], [])[0]
    assert gap["count"] == 5  # The paper check still worked
    assert gap["trial_count"] is None  # None means "couldn't check"
    assert gap["trials"] == []
