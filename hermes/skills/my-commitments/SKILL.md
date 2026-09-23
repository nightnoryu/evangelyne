---
name: my-commitments
description: Use when reviewing my YouTrack tasks needing my action.
---

# My Commitments

## Purpose

Show the user only the tasks where **they personally owe a concrete next action right now**.

This is not a task list. It is not a status report. It is not a review of the team's work.

The only question this skill answers:

> What is waiting on me, and what is the single next thing I should do about it?

Every reported item must survive this test: if the user did nothing this week, would something concretely go wrong or stay stuck because of *them*?

If the answer is no, do not report it.

## When to use

Trigger on requests like: "что от меня ждут", "мои задачи", "мои обязательства", "что за мной", personal morning/standup self-review, "где я торможу", and recurring scheduled personal reviews (its primary use — weekday cron).

Do **not** use for reviewing other people's issues or team-wide triage — that is `tech-lead-radar`. This skill looks only at issues assigned to the user.

---

## Safety — READ-ONLY

This skill **never writes to YouTrack**.

Never:
- edit an issue or its fields;
- change state, assignee, estimation, or due date;
- add or edit comments;
- create or link issues;
- log work;
- contact colleagues, mention people, or send messages anywhere.

Allowed writes: the local state file only (see [references/state-file.md](references/state-file.md)). That is the skill's own bookkeeping, not a YouTrack mutation.

If the user later asks for a comment or a field change, treat it as a separate explicit request outside this skill.

---

# Procedure

## 1. Get real time and prior state

Get the actual current time once from a real clock and reuse it for the whole run:

```bash
date -u +%Y-%m-%dT%H:%M:%SZ; TZ=Europe/Moscow date +%Y-%m-%d
```

Never infer "today" from the prompt text, from conversation history, or from a state entry. Deadline math is worthless with a guessed date.

Then read the state file (format, path, and re-notification rules: [references/state-file.md](references/state-file.md)). It tells you what was already reported and at what urgency, so today's run can stay quiet about unchanged things.

If the file is missing or unparseable, treat state as empty, add a one-line caveat to the report, and write a fresh valid file at the end.

## 2. Build the candidate set

Start here, nothing wider:

```
for: me #Unresolved
```

That is the whole scope — unresolved issues assigned to the user. Do not scan projects, teammates' issues, or resolved work.

Read [references/youtrack-access.md](references/youtrack-access.md) before querying. It has verified query syntax, per-project field-name differences, and tool argument limits that will otherwise cost you failed calls.

**Field names are not assumed — they are verified.** Call `get_issue_fields_schema` for each project present in the candidate set and confirm which fields actually exist there before relying on any of them. A deadline field is not guaranteed to exist in a project (verified: it does not exist in all of them). If a project has no deadline field, deadline-based signals simply do not apply to its issues — never substitute `updatedAt`, `createdAt`, or an estimation as a stand-in for a deadline.

## 3. Read enough to judge

`search_issues` returns summary fields only. For each candidate that might qualify, call `get_issue` for the full description and field values, and `get_issue_comments` for the recent discussion.

Comments are usually where the real signal lives — a direct question to the user, a "ждём ответа", a blocker, a review verdict. A summary line almost never shows this.

Skip the deeper read only for issues that obviously cannot qualify (e.g. a permanent umbrella/bucket issue with no deadline field and no recent discussion).

## 4. Apply the inclusion test

Include an issue **only** when at least one signal below is **confirmed by YouTrack data you actually read**.

### Signal A — Deadline near or passed

The project has a deadline field, the issue has an explicit value in it, and that date is today, imminent (within ~3 days), or already in the past.

Requires a real field value. No deadline field or an empty one = signal absent. Never infer a deadline from wording like "срочно", from a sprint name, or from a parent issue.

### Signal B — A decision or reply is awaited from the user

Someone asked the user something and it is unanswered: a direct question in a comment, a review finding handed back to them, a QA result needing their verdict, an explicit request to choose an approach.

Confirm by reading the comment thread: there is a request addressed to the user, and no later response from them resolving it.

### Signal C — Blocked, and the user can unblock it

The issue is blocked or waiting, **and** the concrete next step belongs to the user.

"Blocked" must be evidenced — a stated blocker in description or comments, a blocking link, a waiting state. And the unblocking step must be the user's, not someone else's. If the block is on a third party, the user owes nothing — exclude it.

### Signal D — Stalled on a step the user owns

No meaningful progress for a long time, **and** there is confirmed evidence that the next step is the user's.

**Absence of updates is not, by itself, evidence of anything.** A quiet issue may be correctly parked, deprioritised, or waiting on someone else. Staleness only counts when paired with independent evidence of the user's ownership of the next step — e.g. they are assignee *and* the last comment leaves an open action on them, or the state means "waiting for the assignee to act".

Stale + assigned-to-me + nothing else = **not reportable**.

### Always exclude

- Permanent umbrella / bucket / time-tracking issues that exist to collect work items and never "complete".
- Issues where the next action is genuinely someone else's.
- Issues with no confirmed signal, however important they look.

## 5. Separate fact from inference

Keep these strictly distinct in the report:

| Fact | Inference |
|------|-----------|
| Field values, dates, states, comment text, authors, links | Why it matters, what is probably blocking, what to do next |

State facts plainly. Mark inferences as inferences ("похоже", "вероятно", "судя по комментарию"). Never present a guess as a YouTrack fact, and never invent a deadline, a blocker, or a request that is not in the data.

## 6. Rank by urgency

Sort the report by urgency, most urgent first:

1. **🔴 Сегодня** — deadline passed or today; someone is actively blocked waiting on the user.
2. **🟡 На этой неделе** — deadline imminent; an unanswered request that is holding progress.
3. **⚪ Не срочно, но за мной** — confirmed ownership of the next step, no time pressure yet.

Urgency comes from the evidence, not from `Priority`. A `Critical` issue with nothing awaited from the user is not urgent *for this report*.

## 7. Apply re-notification control

Do not repeat yesterday's warnings verbatim. Before including an item already present in state, check the rules in [references/state-file.md](references/state-file.md): report again only on a **material change** or an **escalation of urgency**.

When re-reporting something previously flagged, say so explicitly and say what changed — e.g. `(повторно с 2026-09-21, срок теперь просрочен)`. Never re-raise an unchanged item at unchanged urgency.

---

# Output

Write in **Russian**, short and scannable. Keep issue IDs, field names, and state values verbatim — translate prose only.

Link every issue using the `url` returned by the tool call for that exact issue. Never construct, guess, or pattern-match a URL.

Each item gets exactly three things:
- **Причина** — the confirmed signal, with the fact behind it.
- **Действие** — one concrete next step the user can do themselves. One. Not a list of options.
- the urgency tier it sits in.

No preamble, no summary of how many issues were scanned, no encouragement.

If nothing qualifies, return exactly this single line and nothing else:

> Сейчас от тебя ничего не ждут.

Otherwise:

```
## Что за мной

### 🔴 [CRM-10194](https://youtrack.ispring.lan/issue/CRM-10194) — Настроить тариф «Обучение»
**Причина:** Due Date 2026-09-08 — просрочен. State: Open.
**Действие:** Выставить новый реальный срок или закрыть задачу, если она больше не нужна.

### 🟡 [CRM-9911](https://youtrack.ispring.lan/issue/CRM-9911) — 500 при фильтрации по email type
**Причина:** QA вернула задачу (State: Reopened), в последнем комментарии Елена описала рассинхрон значений — ответа от тебя нет.
**Действие:** Ответить на комментарий QA: подтвердить, баг это в отображении столбца или в фильтре.

### ⚪ [CRM-9888](https://youtrack.ispring.lan/issue/CRM-9888) — Перенос crm2 в кубер
**Причина:** Следующий шаг за тобой по последнему комментарию, движения нет с 2026-09-01. Срока у задачи нет.
**Действие:** Решить, берёшь в этот спринт или явно откладываешь.
```

Aim for at most ~5 items. If more qualify, report the most urgent and add one line: `Ещё N задач ждут действия — скажи, если нужен полный список.`

---

# Persist state

After producing the report (including an empty one), update the state file per [references/state-file.md](references/state-file.md) for **every issue examined**, not just reported ones.

The run is not complete until this write happens — without it, tomorrow's run repeats today's warnings.

---

# Verification

Before returning:

1. Every reported issue exists and was actually read this run.
2. Every reason cites a real field value or a real comment — nothing inferred presented as fact.
3. No deadline claim without a verified deadline field holding a value.
4. No item included on staleness alone.
5. Every item has exactly one concrete action the user can perform themselves.
6. Every link came from a tool response `url`.
7. Sorted by urgency; re-reported items marked with what changed.
8. Report is in Russian and short.
9. Nothing was written to YouTrack.
10. State file written.
