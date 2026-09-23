# State file and re-notification

Purpose: stop the skill from repeating the same warning every weekday morning. Without it, a daily run says the same three things until the user stops reading it.

## Path

```
/opt/data/my-commitments-state.json
```

Fixed absolute path. Read with `read_file`, write with `write_file` (full overwrite — always read-modify-write the whole object).

Write scratch files, if ever needed, under `/opt/data/tmp/`. The write sandbox is scoped to `/opt/data`; `/tmp` writes are denied.

Missing file = empty state `{}`; create it at the end of the run.

## Format

Keyed by issue ID, one entry per issue examined in any past run:

```json
{
  "CRM-9911": {
    "last_seen": "2026-09-23T19:25:14Z",
    "last_state": "Reopened",
    "last_due_date": null,
    "last_comment_at": "2026-09-21T14:03:00Z",
    "last_signal": "B",
    "last_urgency": "yellow",
    "reported": true,
    "reported_at": "2026-09-23T19:25:14Z",
    "reported_reason": "QA вернула задачу, ответа нет",
    "snoozed_until": null
  }
}
```

### Fields

- `last_seen` — real-clock UTC ISO timestamp of this run. One value per run, reused for every entry touched. Never inferred from the prompt.
- `last_state` — the `State` value verbatim from YouTrack.
- `last_due_date` — the deadline field value (`yyyy-MM-dd`), or `null` when the project has no deadline field or the field is empty. `null` means "no deadline known", never "no deadline exists" — the distinction is in the project schema, not here.
- `last_comment_at` — timestamp of the newest comment seen (converted from epoch ms). Used to detect new discussion.
- `last_signal` — which inclusion signal fired: `"A"`/`"B"`/`"C"`/`"D"`, or `null` if none.
- `last_urgency` — `"red"` / `"yellow"` / `"white"` / `null`. Enables escalation comparison.
- `reported` — whether it appeared in the last report.
- `reported_reason` — one-line reason, so a repeat can be recognised as the *same* reason.
- `snoozed_until` — optional date; while in the future, suppress unless urgency escalates. Set only when the user explicitly says "not now" about that issue.

## Re-notification rules

An issue already in state with `reported: true` is reported again **only** if at least one holds:

1. **Urgency escalated** — `white → yellow`, `yellow → red`, or deadline moved from future to today/past.
2. **New relevant discussion** — `last_comment_at` advanced and the new comment bears on the user's action (a new question, a new blocker, a QA verdict).
3. **State changed** — `last_state` differs (e.g. `Code Review → Reopened`).
4. **Deadline changed** — `last_due_date` differs.
5. **A different signal now fires** — e.g. was D (stalled), now B (someone is waiting).
6. **Cooling-off elapsed** — still genuinely action-required and ≥7 days since `reported_at`. Re-raise once, flagged as a reminder.

Otherwise stay silent about it, but still refresh its entry.

If nothing qualifies after this filter, the correct output is the single no-action line. A quiet report is a success, not a failure to find something.

### Marking repeats

When re-reporting, state the history and what changed:

- `(повторно с 2026-09-21 — срок теперь просрочен)`
- `(говорил 2026-09-16, появился новый комментарий от QA)`
- `(напоминание, висит 7 дней без движения)`

Never re-raise an item as if it were new.

## Read-modify-write rules

1. Read the full file at the start of the run.
2. Leave entries for issues not touched this run untouched — never prune.
3. Update or insert an entry for **every** issue examined, including ones that did not qualify. Entries for non-qualifying issues are what make tomorrow's diff possible.
4. Write the full object back at the end.

## Failure handling

If the file exists but does not parse: do not abort the run. Add one caveat line to the report (`состояние не читалось, отчёт построен с нуля`), treat state as empty, and overwrite with a valid object at the end.
