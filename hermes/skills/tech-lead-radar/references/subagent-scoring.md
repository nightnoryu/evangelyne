# Subagent Scoring (for large review windows)

Used by [SKILL.md step 1](../SKILL.md#1-establish-the-review-window) when the review window has
enough candidates that scoring them all in the orchestrator's own context risks context rot (long
issue bodies + this whole skill's instructions competing for attention in one context).

**At most 3 subagents run concurrently; each scores a CHUNK of issues, not one issue.** Split
the candidate list into up to 3 roughly equal chunks and dispatch them as one parallel
`delegate_task` call with 3 `tasks` entries. Never fan out one subagent per issue: in a
2026-11-20 run, 25 of 40 per-issue subagents died with provider stalls ("Provider has been
unresponsive for 5 consecutive stale attempts", broken pipe) after 15–25 minutes each.
Chunked dispatch (3 subagents × ~10–15 issues) produces the same verdicts without the stall
storm.

Chunk-failure handling: if a chunk fails, read its live transcript for the real cause — the
delegation wrapper's error text is unreliable (it reports "output_schema mismatch" even when the
transcript shows a provider stall). Retry the chunk once; if it fails again, score that chunk's
issues directly in the orchestrator with `get_issue` instead of losing them.

## What the orchestrator does before delegating

1. Run `search_issues` to get the candidate ID list (per
   [references/youtrack-queries.md](youtrack-queries.md)).
2. Read the state file once. For each candidate, pull its prior entry if any
   (`last_status`, `last_description_hash`, `last_attention`, `last_summary`).
3. Build one task per chunk. Each task lists its chunk's issue IDs and carries, per issue, the
   prior entry MINUS `last_description_hash` (status, attention, summary only — or "no prior
   entry, treat as baseline"). Keep `last_description_hash` out of subagent context entirely:
   given a hash string in context, models echo it back instead of computing the real one (seen
   in the 2026-11-20 run). The orchestrator keeps hashes itself for its own change detection.

## Task template (fill in per issue)

```
goal: >
  Score the YouTrack issues listed in context (one chunk of the radar window) for Tech Lead
  attention per the tech-lead-radar scoring procedure. For EACH issue: read it with get_issue
  (full description, comments, linked issues, custom fields). Load
  skill_view(name='tech-lead-radar', file_path='references/signals.md') and
  skill_view(name='tech-lead-radar', file_path='references/special-rules.md') before scoring —
  they contain the signal catalog and calibration rules (PM-proposed solutions, test coverage)
  you must apply. Compare each issue against its prior state (or treat as baseline) to detect
  scope expansion, implementation-direction changes, and description/status changes. Assign each
  an attention score 0-10 with a one-line justification, pick an intervention window from
  (before_development, during_development, before_review, before_release, after_release,
  monitor_only), and list the 2-5 strongest reasons (concrete, not vague). Return ONLY the JSON
  object described in output_schema — no prose, no markdown.

  YOU ARE READ-ONLY. Never call any YouTrack write/update/tag/comment/subscription/vote tool.
  Never write to any state file. Your only job is to read and return a verdict.

context: |
  Chunk issues (score each one): {ISSUE-ID-1}, {ISSUE-ID-2}, ...
  Per issue, prior state entry from the previous radar run (or "none — baseline" if this is the
  first time this issue is seen) — status/attention/summary ONLY, deliberately no
  description_hash:
  {prior_state_entries_or_"none"}

  Score using the tech-lead-radar procedure: attention 0-10, where 0-3 ignore, 4-6 watch,
  7-8 review, 9-10 intervene. Signals to weigh: architecture impact, production risk, weak
  requirements/testing, complexity hidden behind simple wording, scope expansion vs prior state,
  implementation-direction shifts. Do not escalate solely for "no tests" — weigh against
  behavior risk and regression cost per special-rules.md.

output_schema:
  type: object
  required: [verdicts]
  properties:
    verdicts:
      type: array
      items:
        type: object
        required: [issue_id, url, attention, status, description_hash, summary]
        properties:
          issue_id: {type: string}
          url: {type: string, description: "exact url field from get_issue, never invented"}
          attention: {type: number}
          intervention_window: {type: string}
          status: {type: string, description: "current State custom field value, verbatim"}
          description_hash: {type: string, description: "sha256 hex of the CURRENT description from YOUR OWN get_issue call, truncated to 16 chars; hash the empty string if description is null; never reuse any hash string from the task context"}
          summary: {type: string, description: "one-line plain summary of what the issue currently is"}
          reasons: {type: array, items: {type: string}}
          scope_change: {type: string, description: "what changed vs prior state, or empty string if no prior state / no change"}
          questions: {type: array, items: {type: string}, description: "questions to suggest to the Tech Lead, not solutions"}
```

## What the orchestrator does after delegating

1. Collect each subagent's JSON verdict (validated against `output_schema` — that's automatic via
   `delegate_task`'s `output_schema` mechanism, with one correction retry on failure).
2. Build the final Russian-language report per [SKILL.md § Output](../SKILL.md#output) from the
   compact verdicts only — never paste a subagent's raw reasoning transcript into the report.
3. Update the state file (read-modify-write) using each verdict's `attention`, `status`,
   `description_hash`, `summary`, and append an `alerts` entry for anything crossing the
   reporting threshold. For every issue you REPORT (attention >= 7), recompute the hash yourself
   from your own `get_issue` (you verify those issues exist anyway) and overwrite the subagent's
   value on mismatch — subagent hashes have proven unreliable, and a wrong hash causes false
   "description changed" signals on the next run.

## Why this shape

- Subagents get a narrow chunk task — no competing multi-hundred-line skill document to skim
  past, and a small enough fan-out (≤3 concurrent) that the provider is not saturated.
- The orchestrator never ingests full issue descriptions/comments for candidates — only compact
  JSON — so its own context stays small across a scan of any size, and it, not a subagent, is the
  only place state-file writes happen.
- Explicitly telling every subagent "you are read-only, never call a YouTrack write tool" in the
  task goal (not just relying on it inheriting the parent skill) closes the exact failure mode
  that motivated this file: a model reaching for the closest-sounding write tool instead of
  following a buried instruction.
