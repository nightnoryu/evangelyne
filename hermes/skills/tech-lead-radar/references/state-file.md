# State File

Persists the radar's per-issue memory between runs so it can diff incrementally instead of re-scoring every issue from scratch.

## Path

```
/opt/data/tech-lead-radar-state.json
```

Fixed absolute path, not per-profile. Read it with `read_file`, write it with `write_file` (full overwrite — always read-modify-write the whole object, never patch a fragment).

If the file does not exist yet, treat the state as empty (`{}`) and create it on this run's write step.

## Format

Top-level object keyed by YouTrack issue ID. One entry per issue that has been examined in any past run:

```json
{
  "ISSUE-12345": {
    "last_seen": "2026-09-08T08:00:00Z",
    "last_status": "In Progress",
    "last_description_hash": "...",
    "last_attention": 5.2,
    "last_summary": "Add client status field",
    "alerts": []
  }
}
```

### Field semantics

- `last_seen` — ISO 8601 UTC timestamp (`Z` suffix) of this run's execution time, not the issue's own `updated` field.
- `last_status` — the issue's `State` custom field value at this run, verbatim from YouTrack (e.g. `Open`, `In Progress`, `Code Review`).
- `last_description_hash` — a short deterministic hash (e.g. sha256 hex, truncated to 16 chars is fine) of the issue's current `description` field. Used purely to detect "did the description change since last run" without storing the full text. Recompute and compare on every run.
- `last_attention` — the attention score (0–10, decimals allowed) assigned this run. Decimals let borderline scores be tracked precisely (e.g. `6.5` watched closely without crossing into report territory) even though the report itself only surfaces whole-number-looking thresholds.
- `last_summary` — a short (one-line) plain description of what the issue currently is, for a human skimming the state file directly. Not shown in the chat report; this is a debugging/audit aid.
- `alerts` — array of past alert records for this issue, oldest first. Append one entry each time the issue crosses `attention >= 7` and gets included in a report:

```json
{
  "alerts": [
    {
      "date": "2026-09-08T08:00:00Z",
      "attention": 8,
      "reason": "Scope expanded to production migration"
    }
  ]
}
```

Use this history to distinguish a fresh escalation from a repeat one — if the issue already has a recent alert at a similar or higher attention level with the same core reason, say so explicitly in the report ("previously flagged on 2026-09-05 for the same reason") instead of presenting it as new.

## Read-modify-write rules

1. Read the full file at the start of step 1 (Establish the review window).
2. Keep entries for issues not touched this run untouched — do not prune or drop them just because they weren't in this run's window.
3. Update or insert an entry for every issue actually examined this run (scored, even if below the reporting threshold).
4. Write the full object back at the end of the run (see Verification step in SKILL.md — the run isn't complete until this write happens).

## Failure handling

If the file exists but fails to parse as JSON, do not crash the run: report the issue to the Tech Lead as a one-line caveat ("state file was unreadable, ran a full baseline scan instead"), treat state as empty for this run, and overwrite it with a fresh valid object at the end.
