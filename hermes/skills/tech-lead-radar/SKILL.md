---
name: tech-lead-radar
description: Detect YouTrack tasks that may require Tech Lead attention
---

# Tech Lead Radar

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

Read the state file first (see [references/state-file.md](references/state-file.md) for format and rules) — it holds `last_seen`, `last_status`, `last_description_hash`, `last_attention`, `last_summary`, and `alerts` per issue from the previous run. This is the actual "previous radar run" referenced throughout this procedure.

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

# Output

Only report tasks with `attention >= 7`.

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

For every issue examined this run (not only ones that scored ≥7), write or update its entry:

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
