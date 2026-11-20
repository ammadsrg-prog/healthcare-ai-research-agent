"""
Automatic tests for the PII detector. Run them all with:  python -m pytest

Each test gives the code an example and checks the answer with "assert".
If an assert is wrong, pytest shows which test failed. This way, a future change
that breaks the safety check is caught at once, without testing by hand.
"""

from src.pii import find_pii, redact_pii


# --- Personal details that MUST be found ---

def test_finds_email():
    assert find_pii("results for jane.doe@hospital.org") == ["email address"]


def test_finds_phone_number():
    assert "phone number" in find_pii("call 07700 900123 about diabetes")


def test_finds_date_of_birth():
    assert "date (possible date of birth)" in find_pii("born 12/03/1980 with asthma")


def test_finds_social_security_number():
    assert find_pii("SSN 123-45-6789") == ["ID number (possible patient record or social security number)"]


def test_finds_medical_record_number():
    assert find_pii("MRN 4829173 heart failure") == ["ID number (possible patient record or social security number)"]


def test_finds_name_with_title():
    assert find_pii("Mr Smith has type 2 diabetes") == ["person's name"]


def test_finds_several_kinds_at_once():
    found = find_pii("Mrs Patel, 01/02/1975, 0300 123 4567")
    assert len(found) == 3


# --- Normal medical topics that must NOT be blocked (no false alarms) ---

def test_normal_topic_is_allowed():
    assert find_pii("type 2 diabetes mobile app") == []


def test_patient_safety_is_not_a_name():
    assert find_pii("Patient Safety in intensive care") == []


def test_year_range_is_not_a_phone_number():
    assert find_pii("diabetes trials 2015-2020") == []


def test_list_of_years_is_not_a_phone_number():
    assert find_pii("COVID-19 vaccines 2019 2020 2021") == []


def test_disease_names_with_numbers_are_allowed():
    assert find_pii("COVID-19 and H1N1 in children under 5") == []


# --- Redaction ---

def test_redact_replaces_personal_details():
    assert redact_pii("email jane@nhs.uk or call 07700 900123") == "email [EMAIL] or call [PHONE]"


def test_redact_keeps_normal_text():
    assert redact_pii("asthma trials 2015-2020") == "asthma trials 2015-2020"
