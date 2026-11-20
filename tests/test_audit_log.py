"""
Tests for the audit log. Run them all with:  python -m pytest

"tmp_path" and "monkeypatch" are pytest helpers:
  - tmp_path is an empty temporary folder, made fresh for each test
  - monkeypatch swaps a value only during the test
Together they make the log write to a temporary file, so tests never touch the real log.
"""

import src.audit_log as audit_log


def use_temporary_log(tmp_path, monkeypatch):
    monkeypatch.setattr(audit_log, "LOG_FILE", tmp_path / "logs" / "audit.jsonl")


def test_empty_log_returns_no_events(tmp_path, monkeypatch):
    use_temporary_log(tmp_path, monkeypatch)
    assert audit_log.read_events() == []


def test_logged_event_can_be_read_back(tmp_path, monkeypatch):
    use_temporary_log(tmp_path, monkeypatch)
    audit_log.log_event("search", topic="asthma", papers_found=10)

    events = audit_log.read_events()
    assert len(events) == 1
    assert events[0]["event"] == "search"
    assert events[0]["topic"] == "asthma"
    assert events[0]["papers_found"] == 10
    assert "time" in events[0]


def test_newest_event_comes_first(tmp_path, monkeypatch):
    use_temporary_log(tmp_path, monkeypatch)
    audit_log.log_event("first")
    audit_log.log_event("second")
    assert [e["event"] for e in audit_log.read_events()] == ["second", "first"]


def test_limit_keeps_only_newest(tmp_path, monkeypatch):
    use_temporary_log(tmp_path, monkeypatch)
    for number in range(5):
        audit_log.log_event("search", number=number)
    assert [e["number"] for e in audit_log.read_events(limit=2)] == [4, 3]


def test_damaged_line_is_skipped(tmp_path, monkeypatch):
    use_temporary_log(tmp_path, monkeypatch)
    audit_log.log_event("good")
    with audit_log.LOG_FILE.open("a", encoding="utf-8") as file:
        file.write("this is not json\n")
    assert [e["event"] for e in audit_log.read_events()] == ["good"]
