#!/usr/bin/env python3
"""
Set or clear Tech Lead feedback (not_interesting / especially_interesting) for a
YouTrack issue in the tech-lead-radar local state file.

This script NEVER touches YouTrack. It only reads/writes the local state file at
/opt/data/tech-lead-radar-state.json (full read-modify-write, per references/state-file.md).

Usage:
    python3 set_feedback.py ISSUE-ID not_interesting
    python3 set_feedback.py ISSUE-ID especially_interesting
    python3 set_feedback.py ISSUE-ID clear

Exit codes:
    0 on success (prints the resulting entry as JSON)
    1 on bad arguments or state-file parse failure
"""
import json
import sys
from datetime import datetime, timezone

STATE_PATH = "/opt/data/tech-lead-radar-state.json"
VALID_VALUES = {"not_interesting", "especially_interesting", "clear"}


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: set_feedback.py ISSUE-ID <not_interesting|especially_interesting|clear>", file=sys.stderr)
        return 1

    issue_id, value = sys.argv[1], sys.argv[2]
    if value not in VALID_VALUES:
        print(f"Invalid value '{value}'. Must be one of: {sorted(VALID_VALUES)}", file=sys.stderr)
        return 1

    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            state = json.load(f)
    except FileNotFoundError:
        state = {}
    except json.JSONDecodeError as e:
        print(f"State file exists but failed to parse as JSON: {e}", file=sys.stderr)
        return 1

    entry = state.setdefault(issue_id, {})

    if value == "clear":
        entry.pop("feedback", None)
        entry.pop("feedback_set_at", None)
    else:
        entry["feedback"] = value
        entry["feedback_set_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(json.dumps({issue_id: entry}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
