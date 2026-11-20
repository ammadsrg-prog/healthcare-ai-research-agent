"""
Tests for the guardrail code in bedrock_client.py. Run them all with:  python -m pytest

These tests never call AWS: they check how we build the request and read the reply.
monkeypatch turns the guardrail "on" or "off" only during a test.
"""

import src.bedrock_client as bedrock_client
from src.bedrock_client import build_content, guardrail_reasons

PROMPT = "Summarize this.\n<paper>\nTitle: X\nAbstract: Y\n</paper>\nUse six headings."
PAPER = "Title: X\nAbstract: Y"


def test_without_guardrail_prompt_is_sent_as_plain_text(monkeypatch):
    monkeypatch.setattr(bedrock_client, "BEDROCK_GUARDRAIL_ID", "")
    assert build_content(PROMPT, PAPER) == [{"text": PROMPT}]


def test_with_guardrail_only_the_paper_is_checked(monkeypatch):
    monkeypatch.setattr(bedrock_client, "BEDROCK_GUARDRAIL_ID", "test-id")
    content = build_content(PROMPT, PAPER)
    assert content == [
        {"text": "Summarize this.\n<paper>\n"},
        {"guardContent": {"text": {"text": PAPER}}},
        {"text": "\n</paper>\nUse six headings."},
    ]


def test_ai_still_receives_the_whole_prompt(monkeypatch):
    monkeypatch.setattr(bedrock_client, "BEDROCK_GUARDRAIL_ID", "test-id")
    pieces = []
    for block in build_content(PROMPT, PAPER):
        pieces.append(block["text"] if "text" in block else block["guardContent"]["text"]["text"])
    assert "".join(pieces) == PROMPT


def test_reasons_are_read_from_the_trace():
    # A small fake trace, shaped like the real one from AWS
    trace = {
        "guardrail": {
            "inputAssessment": {
                "id1": {"contentPolicy": {"filters": [{"type": "PROMPT_ATTACK", "action": "BLOCKED"}]}}
            },
            "outputAssessments": {
                "id1": [
                    {
                        "topicPolicy": {"topics": [{"name": "Personal medical advice", "action": "BLOCKED"}]},
                        "sensitiveInformationPolicy": {"piiEntities": [{"type": "EMAIL", "action": "ANONYMIZED"}]},
                    }
                ]
            },
        }
    }
    blocked, masked = guardrail_reasons(trace)
    assert blocked == ["prompt attack", "personal medical advice"]
    assert masked == ["email"]


def test_empty_trace_has_no_reasons():
    assert guardrail_reasons({}) == ([], [])
