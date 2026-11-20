"""
Finds personal information (PII) in text, so patient details never leave this computer.

PII means "Personally Identifiable Information": anything that can identify a person,
like an email, a phone number, a date of birth or a patient ID number.
In healthcare this is extra important, because health data is protected by law
(for example HIPAA in the USA and GDPR in Europe).

The search box is checked before anything is sent to OpenAlex or Amazon Bedrock.
If someone types "Mr Smith, born 12/03/1980, call 07700 900123", we stop and warn them.
"""

import re

# Each rule is a "regular expression" (regex): a pattern that describes what the text looks like.
#   \d = any digit      \s = a space      [A-Z] = a capital letter     \b = the edge of a word
#   {3} = exactly 3 times     {6,} = 6 or more times     ? = optional     | = or
PII_PATTERNS = {
    "email address": r"[\w.+-]+@[\w-]+\.[\w.-]+",
    "phone number": r"\+?\d[\d\s().-]{7,}\d",  # digits mixed with spaces, dashes or brackets
    "date (possible date of birth)": r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b",  # like 12/03/1980
    "ID number (possible patient record or social security number)": r"\b\d{3}-\d{2}-\d{4}\b|\b\d{6,}\b",
    "person's name": r"\b(?:Mr|Mrs|Ms|Miss|Dr)\.?\s+[A-Z][a-z]+",  # a title and a name, like "Mr Smith"
}

# Placeholders used by redact_pii, so text can be kept without the personal details
REDACTION_LABELS = {
    "email address": "[EMAIL]",
    "phone number": "[PHONE]",
    "date (possible date of birth)": "[DATE]",
    "ID number (possible patient record or social security number)": "[ID]",
    "person's name": "[NAME]",
}


def is_real_match(kind: str, match: str) -> bool:
    """Extra check for phone numbers, which are easy to confuse with years.

    "2015-2020" or "2019 2020 2021" also look like digits with dashes or spaces,
    so a phone number needs at least 10 digits and must not be only years.
    """
    if kind != "phone number":
        return True
    digits = re.sub(r"\D", "", match)  # \D means "not a digit", so this keeps only the digits
    groups = re.findall(r"\d+", match)
    only_years = all(re.fullmatch(r"(19|20)\d\d", group) for group in groups)
    return len(digits) >= 10 and not only_years


def find_pii(text: str) -> list[str]:
    """Return the kinds of personal information found in the text, like ["email address"].

    It returns only the kinds, never the personal details themselves,
    so the warning on screen doesn't repeat them.
    """
    found = []
    for kind, pattern in PII_PATTERNS.items():
        for match in re.findall(pattern, text):  # re.findall gives every piece of text that fits the pattern
            if is_real_match(kind, match):
                found.append(kind)
                break  # One match is enough to report this kind
    return found


def redact_pii(text: str) -> str:
    """Replace personal information with placeholders, like "call 07700 900123" -> "call [PHONE]"."""
    for kind, pattern in PII_PATTERNS.items():
        # For each match, use the placeholder if it's real PII, or keep the original text if not
        text = re.sub(
            pattern,
            lambda match: REDACTION_LABELS[kind] if is_real_match(kind, match.group()) else match.group(),
            text,
        )
    return text
