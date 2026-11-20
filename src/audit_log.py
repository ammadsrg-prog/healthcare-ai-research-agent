"""
The audit log: a diary of everything important the app does.

Every AI call, search and safety block is written down with the time and the details.
Companies need this for AI governance: to answer "what did the AI do, when, and what did it cost?"

Two privacy rules:
  1. We never save prompts, abstracts or AI answers, only facts about them (sizes, tokens, times).
     Saving less data means less can leak. This is called "data minimisation".
  2. Search topics are saved with personal details removed (see src/pii.py).

The log is a "JSON Lines" file: one JSON object per line, so new events are simply added
at the end and old ones are never changed.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

# The log lives in the project's logs folder, which is never uploaded (it's in .gitignore)
LOG_FILE = Path(__file__).parent.parent / "logs" / "audit.jsonl"


def log_event(event: str, **details) -> None:
    """Add one event to the audit log, for example: log_event("search", topic="asthma", papers=10).

    **details collects any extra named values into a dictionary.
    """
    record = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),  # UTC, so times are the same everywhere
        "event": event,
        **details,  # ** unpacks the dictionary, adding its keys to the record
    }
    LOG_FILE.parent.mkdir(exist_ok=True)  # Create the logs folder the first time
    with LOG_FILE.open("a", encoding="utf-8") as file:  # "a" means append: add to the end, never overwrite
        file.write(json.dumps(record) + "\n")


def read_events(limit: int = 200) -> list[dict]:
    """Return the newest events first, up to the limit."""
    if not LOG_FILE.exists():
        return []
    events = []
    for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # Skip a damaged line instead of crashing
    return list(reversed(events))[:limit]
