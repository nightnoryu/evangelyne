# Subagent Scoring (for large review windows)

Used by [SKILL.md step 1](../SKILL.md#1-establish-the-review-window) when the review window has
enough candidates that scoring them all in the orchestrator's own context risks context rot (long
issue bodies + this whole skill's instructions competing for attention in one context).

One subagent per candidate issue, dispatched in parallel (batch all of them in a single
`delegate_task` call with multiple `tasks` entries — independent work, no need to serialize).

## What the orchestrator does before delegating

1. Run `search_issues` to get the candidate ID list (per
   [references/youtrack-queries.md](youtrack-queries.md)).
2. Read the state file once. For each candidate, pull its prior entry if any
   (`last_status`, `last_description_hash`, `last_attention`, `last_summary`).
3. Build one subagent task per candidate — do NOT dump the full state file or the full SKILL.md
   into every task; each task gets only that one issue's prior entry (or "no prior entry, treat
   as baseline" if none).

## Task template (fill in per issue)

```
goal: >
  Score YouTrack issue {ISSUE-ID} for Tech Lead attention per the tech-lead-radar scoring
  procedure. Read the issue with get_issue (full description, comments, linked issues, custom
  fields). Load skill_view(name='tech-lead-radar', file_path='references/signals.md') and
  skill_view(name='tech-lead-radar', file_path='references/special-rules.md') before scoring —
  they contain the signal catalog and calibration rules (PM-proposed solutions, test coverage)
  you must apply. Compare against the "prior state" given below to detect scope expansion,
  implementation-direction changes, and description/status changes. Assign an attention score
  0-10 with a one-line justification, pick an intervention window from
  (before_development, during_development, before_review, before_release, after_release,
  monitor_only), and list the 2-5 strongest reasons (concrete, not vague). Return ONLY the JSON
  object described in output_schema — no prose, no markdown report.

  YOU ARE READ-ONLY. Never call any YouTrack write/update/tag/comment/subscription/vote tool.
  Never write to any state file. Your only job is to read and return a verdict.

context: |
  Issue ID: {ISSUE-ID}
  Prior state entry (from previous radar run, or "none — baseline" if this is the first time
  this issue is seen):
  {prior_state_json_or_"none"}

  Score using the tech-lead-radar procedure: attention 0-10, where 0-3 ignore, 4-6 watch,
  7-8 review, 9-10 intervene. Signals to weigh: architecture impact, production risk, weak
  requirements/testing, complexity hidden behind simple wording, scope expansion vs prior state,
  implementation-direction shifts. Do not escalate solely for "no tests" — weigh against
  behavior risk and regression cost per special-rules.md.

output_schema:
  type: object
  required: [issue_id, url, attention, status, description_hash, summary]
  properties:
    issue_id: {type: string}
    url: {type: string, description: "exact url field from get_issue, never invented"}
    attention: {type: number}
    intervention_window: {type: string}
    status: {type: string, description: "current State custom field value, verbatim"}
    description_hash: {type: string, description: "sha256 hex of current description, truncated to 16 chars"}
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
   reporting threshold.

## Why this shape

- Subagents get a narrow, single-issue task — no competing multi-hundred-line skill document to
  skim past.
- The orchestrator never ingests full issue descriptions/comments for candidates — only compact
  JSON — so its own context stays small across a scan of any size, and it, not a subagent, is the
  only place state-file writes happen.
- Explicitly telling every subagent "you are read-only, never call a YouTrack write tool" in the
  task goal (not just relying on it inheriting the parent skill) closes the exact failure mode
  that motivated this file: a model reaching for the closest-sounding write tool instead of
  following a buried instruction.
