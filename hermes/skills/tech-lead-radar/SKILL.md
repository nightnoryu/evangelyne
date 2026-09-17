---
name: tech-lead-radar
description: Detect YouTrack tasks that may require Tech Lead attention; also records local-only feedback (not_interesting / especially_interesting) to tune future reports without ever writing to YouTrack
---

# Tech Lead Radar

> ⚠️ **Feedback commands are a script call, never a YouTrack write.**
> "отметь как интересную" / "неинтересна, не показывай" / "сними пометку" (or English
> equivalents) → run `scripts/set_feedback.py ISSUE-ID <especially_interesting|not_interesting|clear>`.
> That is the ENTIRE action. Never call `update_issue`, `manage_issue_tags`, subscription/vote,
> or any other YouTrack write tool for this — feedback lives only in the local state file. See
> [Feedback & Attention Overrides](#feedback--attention-overrides) for the full procedure.

## Purpose

Act as a personal radar for a Tech Lead.

Review YouTrack issues and identify tasks that may deserve the Tech Lead's attention before implementation, during implementation, or before release.

The goal is NOT to review every task.

The goal is to detect situations where:
- an engineering decision may have significant consequences;
- the implementation direction looks questionable;
- the scope has expanded unexpectedly;
- requirements hide architectural complexity;
- verification or testing is insufficient;
- a task affects multiple systems;
- a task is approaching a point where intervention becomes expensive.

You are an advisory system.

Never block work.
Never modify YouTrack issues.
Never contact developers or PMs.
Never present your assessment as an authoritative architectural decision.

Your job is to tell the Tech Lead where attention may be valuable.

---

## When to Use

Use this skill when periodically reviewing YouTrack for:
- newly created tasks;
- recently modified tasks;
- tasks changing state;
- tasks approaching implementation;
- tasks that have acquired new comments or requirements;
- tasks whose scope or implementation direction has changed.

The skill is especially useful for recurring scheduled runs.

---

# Procedure

## 1. Establish the review window

Read the state file first (see [references/state-file.md](references/state-file.md) for format and rules) — it holds `last_seen`, `last_status`, `last_description_hash`, `last_attention`, `last_summary`, `alerts`, and optionally `feedback`/`feedback_set_at` per issue from the previous run. This is the actual "previous radar run" referenced throughout this procedure.

Get the actual current UTC time from a real clock source (e.g. the terminal tool) once at the start of the run and reuse it for every `last_seen`/`alerts[].date` written this run — never infer "now" from the prompt text or a prior state entry.

Determine what has changed since the previous radar run.

Prefer incremental analysis over reviewing the entire project.

Look for:
- newly created issues;
- recently updated issues;
- description changes (compare the current description's hash against `last_description_hash` — a mismatch means the description changed and deserves a closer read, even if nothing else did);
- comment activity;
- state changes (compare against `last_status`);
- assignee changes;
- priority changes;
- newly linked issues;
- changes in estimation;
- changes in test coverage or testing information;
- attention crossing a threshold since last run (compare against `last_attention`).

If the state file is missing or an issue has no prior entry, perform a broader initial scan for it and clearly treat it as a baseline — do not report it purely for "appearing for the first time."

Use `search_issues` to build this window, then `get_issue` on each candidate to read the full description before scoring — summaries alone rarely show scope expansion or hidden complexity. See [references/youtrack-queries.md](references/youtrack-queries.md) for tested query syntax (relative dates, project scoping, state filters).

### Delegate scoring to subagents when the window is large

Reading a full description + comments for every candidate and reasoning about signals, scope
expansion, and implementation-direction shifts for each one is a lot of prose to hold in one
context alongside this whole SKILL.md. On a small window (roughly ≤5 candidates) just score them
directly — delegation overhead isn't worth it. Once the window is larger, delegate per-issue
scoring to a subagent (see [references/subagent-scoring.md](references/subagent-scoring.md) for
the exact task template and output contract) so the orchestrator's own context only ever holds
compact JSON verdicts, not full issue bodies. This exists specifically to avoid context rot:
a long-running scan that piles every issue's full text plus this skill's instructions into one
context is exactly the situation where a model starts skipping instructions buried later in the
document (e.g. the Safety rules, or the Feedback Overrides section) — keep the orchestrator's
context small and offload the heavy reading.

The orchestrator still owns: building the search query, reading/writing the state file, applying
suppression/enhanced-tracking rules from saved `feedback` (cheap, doesn't need full issue text),
assembling the final report, and every YouTrack write-adjacent decision (there should be none —
this skill is read-only). Subagents never touch YouTrack write endpoints, never touch the state
file, and never see feedback-setting requests — those two things stay exclusively with the
orchestrator per [Feedback & Attention Overrides](#feedback--attention-overrides).

**If this skill runs as a cron job (its primary intended use — see "When to Use"), pin
`enabled_toolsets` on the job to explicitly include `delegation`** when using subagent scoring.
Cron toolset resolution falls through job override → `cron`-platform config in `hermes tools` →
built-in default, and whether `delegation` is present at the last two layers is not something
you can verify by reading config alone — an unset `cron` platform entry in `platform_toolsets`
means the job is riding an ambiguous fallback. Pinning it removes the ambiguity instead of hoping
the fallback happens to include it: `cronjob(action="update", job_id="...",
enabled_toolsets=["delegation", "file", "code_execution", "skills", "web"])` (add whatever else
the job's other steps need — YouTrack access goes through the MCP server, not toolset gating, so
it is unaffected by this list).

If a helper script (e.g. for hashing descriptions) needs a scratch file, write it under `/opt/data/tmp/` (create the directory if needed), not `/tmp/` — the write sandbox (`HERMES_WRITE_SAFE_ROOT`) is scoped to `/opt/data`, so `/tmp` writes are denied and waste a step.

**Exclude issues the Tech Lead is already personally involved in** — assigned to them (`for:`), reviewing (`Reviewers:`), or reported by them (`reporter:`). They're already across those; the radar's value is surfacing what they *don't* already know about. Apply this exclusion at query time, not as a post-filter — see [references/youtrack-queries.md](references/youtrack-queries.md) for the exact negated-filter syntax.

---

## 2. Filter obvious noise

Do not spend deep reasoning on routine work.

Usually ignore:
- trivial configuration changes;
- simple recurring operations;
- straightforward data corrections;
- obvious typo/text changes;
- routine exports;
- tasks with no meaningful engineering risk;
- tasks whose implementation and verification are already clear.

However, do not ignore a task solely because its YouTrack type is "Service".

A task that appears routine may still hide significant engineering impact.

Also apply any saved Tech Lead feedback for the issue at this point — see [Feedback & Attention Overrides](#feedback--attention-overrides) below. An issue marked `not_interesting` is noise unless new significant details appeared since it was marked; an issue marked `especially_interesting` is never routine noise regardless of its score.

---

## 3. Identify engineering signals

Score up when a task touches architecture (new services, shared domain models, API/contract changes, async processing, queues, migrations, backfills, new external dependencies), production risk (production data, bulk operations, permissions, billing, PII, auth, irreversible operations, hard rollback), or has weak requirements/testing (unclear acceptance criteria, undefined failure behavior, no verification strategy for business-critical or hard-to-regression-test changes).

Also watch for complexity hidden behind simple wording — e.g. "Add a field to Client" can hide a migration + backfill + API changes; "Add a button to recalculate clients" can hide a bulk async operation needing idempotency and rollback. Look for this mismatch between apparent task size and actual system impact.

See [references/signals.md](references/signals.md) for the full signal catalog before finalizing a score.

---

## 4. Detect scope expansion

Compare the current task with its previous state whenever possible.

Pay special attention to transitions such as:

"Add a field"

→ "populate existing records"

→ "update reports"

→ "run migration in production"

This should be treated as a significant change in engineering risk.

Report:

- what changed;
- what the task originally appeared to be;
- what it has become;
- why the change matters.

Prefer statements like:

> Scope expanded from a local change to a cross-system data migration.

Avoid vague statements such as:

> This task became more complex.

---

## 5. Detect changes in implementation direction

A task deserves attention when its implementation direction changes substantially.

Examples:

- synchronous → asynchronous;
- local calculation → shared service;
- application logic → database procedure;
- one system → multiple systems;
- manual operation → automated bulk operation;
- simple update → migration;
- existing mechanism → new infrastructure.

Explain why the change may matter.

---

## 6. Assess Tech Lead attention

Assign an attention score from 0 to 10.

### 0–3: Ignore

Routine engineering work.

No meaningful reason for Tech Lead intervention.

### 4–6: Watch

Potentially interesting but not urgent.

Keep monitoring if the task changes.

Do not notify unless the task crosses a meaningful threshold.

### 7–8: Review

There is a concrete reason for Tech Lead attention.

The Tech Lead should probably inspect the task or discuss it with the assignee.

### 9–10: Intervene

Significant architecture, production, data, security, or scope risk.

Intervention is valuable before the work progresses further.

The score is an attention signal, not an objective measure of task quality.

---

## 7. Determine the intervention window

For every reported issue, determine when intervention is most useful.

Use one of:

- `before_development`
- `during_development`
- `before_review`
- `before_release`
- `after_release`
- `monitor_only`

Prefer earlier intervention when a questionable decision becomes substantially more expensive to change later.

Examples:

Architecture decision before implementation:

`before_development`

Questionable implementation already being developed:

`during_development`

Testing strategy missing while PR is open:

`before_review`

Production migration about to happen:

`before_release`

Already deployed risky change:

`after_release`

Interesting but not currently actionable:

`monitor_only`

---

## 8. Identify the strongest reasons

Do not produce a long list of weak observations.

Return the 2–5 strongest signals.

Examples:

- Cross-system change
- Bulk production mutation
- No verification strategy
- Scope expanded significantly
- Rollback strategy unclear
- New asynchronous processing
- PM-defined implementation without technical validation
- Shared domain model changed
- External integration added

---

## 9. Suggest questions, not solutions

When intervention is recommended, suggest questions the Tech Lead can ask.

Good:

> How will we handle a partial failure during the backfill?

> What happens if this operation is retried?

> How will we verify that all existing records were migrated correctly?

Avoid immediately dictating an implementation.

The goal is to help the Tech Lead start the right engineering conversation.

---

# Special Rules

Two recurring situations need calibrated (not reflexive) handling — read [references/special-rules.md](references/special-rules.md) before scoring either:

- **PM-Proposed Solutions** — a PM proposing a concrete implementation isn't inherently wrong; check whether it leaves engineering questions unanswered (capacity, timeout, idempotency, failure handling) and report those questions, not criticism of the PM.
- **Test Coverage** — "no tests" is never an automatic escalation reason; weigh it against behavior risk, regression detectability, and regression cost.

---

# Feedback & Attention Overrides

The Tech Lead can give feedback on any issue the radar has surfaced, at any time — not only right after a report. Feedback is stored **only in the local state file**; it never touches YouTrack (no tags, no comments, no fields — see Safety).

## Marking an issue

Two feedback values, stored per-issue in state as `feedback`:

- **`not_interesting`** — the Tech Lead has reviewed this and it does not warrant radar attention. Future runs must suppress it from the report *unless* a materially new significant detail appears (see Suppression rule below).
- **`especially_interesting`** — the Tech Lead wants this issue watched more closely than default. Future runs must track it with extra scrutiny (see Enhanced tracking rule below) and it must never be silently dropped as noise.

Accept feedback commands in natural language referencing an issue ID, e.g.:

> "CRM-10128 неинтересна, больше не показывай"
> "PROJ-55 отметь как особенно интересную"
> "убери пометку с CRM-10128" / "сними отметку"

On receiving such a request, run the helper script — do not hand-edit the state file and do not
call any YouTrack tool:

```
python3 <skill_dir>/scripts/set_feedback.py ISSUE-ID especially_interesting
python3 <skill_dir>/scripts/set_feedback.py ISSUE-ID not_interesting
python3 <skill_dir>/scripts/set_feedback.py ISSUE-ID clear
```

The script does the full read-modify-write against [the state file](references/state-file.md)
itself: it creates the issue's entry if missing (e.g. feedback given on an issue outside the
current run's window), sets/clears `feedback` and `feedback_set_at` (real-clock UTC timestamp),
and leaves every other field of that entry and every other issue's entry untouched. It prints the
resulting entry as JSON — read that output and confirm briefly to the Tech Lead what was recorded.
Do not silently apply it.

This action never calls any YouTrack write endpoint and never runs as part of, or instead of, a
review — it only edits local state. If the script fails for any reason, do not fall back to a
manual state-file edit silently — report the failure and ask before proceeding.

## Suppression rule (`not_interesting`)

During step 2 (Filter obvious noise) and step 6 (Assess Tech Lead attention), if an issue's state entry has `feedback: "not_interesting"`:

- Compute the score normally, but suppress it from the report **unless** something materially significant changed since `feedback_set_at`: description hash changed in a way that alters scope/risk (not a typo fix), a scope-expansion or implementation-direction shift per steps 4–5, a state change into a risk-relevant phase (e.g. moving toward release), or a jump in attention score of roughly +3 or more versus `last_attention`.
- If suppressed, still update `last_seen`, `last_status`, `last_description_hash`, `last_attention`, `last_summary` as normal — feedback suppresses *reporting*, not *tracking*.
- If the suppression is overridden because something significant changed, say so explicitly in the report: state that this issue was previously marked not interesting by the Tech Lead, and name the specific new detail that justified resurfacing it. Do not resurface it silently as if it were a fresh finding.

## Enhanced tracking rule (`especially_interesting`)

If an issue's state entry has `feedback: "especially_interesting"`:

- Never filter it out in step 2 regardless of how routine it looks.
- Read comments and linked issues more thoroughly than the default pass, since the Tech Lead explicitly wants finer-grained visibility.
- Lower the effective reporting bar for this issue: report it whenever `last_attention` moved at all since the previous run (even a small delta, e.g. 4→5), not only when it crosses 7. Label it clearly in the report as being surfaced due to the Tech Lead's own "особенно интересно" marking, so it doesn't read as if it crossed the normal threshold.
- Still assign a genuine attention score — do not inflate it artificially. The marking changes the *reporting bar*, not the *scoring logic*.

## Precedence

If somehow both flags would apply (should not normally happen since setting one should be treated as clearing the other), `especially_interesting` wins — never suppress an issue the Tech Lead explicitly asked to watch more closely.

---

# Output

Only report tasks with `attention >= 7`, plus any issue surfaced via the Enhanced tracking rule for `especially_interesting` feedback (see [Feedback & Attention Overrides](#feedback--attention-overrides)) even if it scores below 7 — mark those clearly as a Tech-Lead-requested watch item, not a standard threshold crossing.

Write the final report in Russian, regardless of the language used internally for reasoning or tool calls. Keep issue IDs, field names like `Intervention`/`Attention`, and intervention window values (`before_development`, etc.) as-is — do not translate identifiers or enum values, only the prose.

Render each issue ID as a Markdown hyperlink to its YouTrack issue, using the `url` field returned by `get_issue`/`search_issues` (e.g. `https://youtrack.ispring.lan/issue/CRM-10128`): `[CRM-10128](https://youtrack.ispring.lan/issue/CRM-10128)`. Never invent or guess the URL — use the one returned by the tool call for that exact issue.

If there are no such tasks, return exactly:

> Нет задач, требующих твоего внимания.

Otherwise use this format:

## Радар Тех. Лида

### 🔴 [ISSUE-ID](https://youtrack.ispring.lan/issue/ISSUE-ID) — Короткое название

**Внимание:** 9/10  
**Когда вмешаться:** before_development

**Почему это важно**
- Изменение затрагивает несколько систем
- Мутация продовых данных
- Не описана стратегия роллбэка

**Что изменилось**
Задача изначально описывала локальное изменение. Теперь она включает синхронизацию нескольких сервисов и продовый бэкафилл.

**Вопросы, которые стоит задать**
1. Как безопасно выполнить бэкафилл?
2. Что происходит при частичном сбое синхронизации сервисов?
3. Как проверить корректность мигрированных данных?

**Рекомендация**
Проверить до начала разработки.

---

## Noise control

Be conservative.

False positives are costly because they train the Tech Lead to ignore the radar.

Prefer:

> "This may deserve attention because..."

over:

> "This is definitely wrong."

Do not report a task merely because:
- it contains technical words;
- it has no unit tests;
- it was created by a PM;
- it is assigned to a junior;
- it has a high priority;
- it looks unfamiliar.

The question is always:

> Is there a concrete reason why this Tech Lead should spend attention here?

---

# Persist State

After producing the report (successful or empty), update the state file so the next run can diff against this one.

For every issue examined this run (not only ones that scored ≥7), write or update its entry, preserving any existing `feedback`/`feedback_set_at` untouched (feedback is only set/cleared via an explicit Tech Lead request, never as a side effect of a scoring run):

```json
{
  "ISSUE-12345": {
    "last_seen": "2026-09-08T08:00:00Z",
    "last_status": "In Progress",
    "last_description_hash": "...",
    "last_attention": 5.2,
    "last_summary": "Add client status field",
    "alerts": [],
    "feedback": "not_interesting",
    "feedback_set_at": "2026-09-10T09:15:00Z"
  }
}
```

See [references/state-file.md](references/state-file.md) for the exact path, field semantics, hashing method, and the `alerts` array format (append an entry there whenever an issue crosses the `attention >= 7` reporting threshold, so repeat alerts can be told apart from new ones next run).

Writing this file is bookkeeping for the skill's own incremental logic, not a change to YouTrack — it does not violate the read-only rule below.

---

# Safety

This skill is READ-ONLY **with respect to YouTrack**.

Never:
- edit an issue;
- change an issue state;
- assign a developer;
- add comments;
- create tasks;
- modify estimates;
- contact team members;
- make architectural decisions on behalf of the Tech Lead.

Writing to the local state file (see Persist State) is allowed and expected — it is not a YouTrack mutation.

Recording Tech Lead feedback (`not_interesting` / `especially_interesting`, see [Feedback & Attention Overrides](#feedback--attention-overrides)) is also local-state-only and allowed. Never translate feedback into a YouTrack tag, comment, custom field, or any other YouTrack write — even if it would be convenient or the Tech Lead's phrasing sounds like a request to label the issue in YouTrack itself. If genuinely ambiguous whether the Tech Lead wants a YouTrack-visible change, ask before writing anything to YouTrack — never assume it's in scope.

If the Tech Lead later asks for a comment or action, handle that as a separate explicit request.

---

# Verification

Before returning the radar report:

1. Verify that every reported issue actually exists.
2. Verify that every reported change is supported by YouTrack data.
3. Do not invent missing requirements.
4. Distinguish facts from hypotheses.
5. Prefer recent changes over stale task properties.
6. Ensure every reported issue has a concrete reason for intervention.
7. Ensure the output contains no routine tasks.
8. Ensure the report is written in Russian per the Output section.
9. If nothing crosses the threshold, return exactly:
   `Нет задач, требующих твоего внимания.`

After returning the report, write the updated state file per [references/state-file.md](references/state-file.md). A run is not complete until the state file is updated.
