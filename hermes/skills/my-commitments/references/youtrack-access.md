# YouTrack access — verified behaviour

Trust this over assumptions; re-verify with `get_issue_fields_schema` when a new project appears in the candidate set.

## Base query

```
for: me #Unresolved
```

`for: me` resolves to the authenticated user — use it rather than hardcoding a login, so the skill keeps working if the account changes. Confirm identity with `get_current_user` when you need the login for comment-author comparisons.

## Deadline field — exists per project, verify every time

The deadline field is named **`Due Date`** (with a space), format `yyyy-MM-dd`.

Verified presence:

| Project | `Due Date` exists | Notes |
|---------|-------------------|-------|
| CRM | yes | also `Testers`, `Requester`, `Test Coverage`, `TestStatus` |
| TDR | yes | also `Approver`, `Remaining effort` |
| TT | **no** | no deadline field at all — deadline signals never apply here |

So: **never assume a deadline field exists.** Call `get_issue_fields_schema(projectKey="…")` for each project in the candidate set and check before using it. For a project without `Due Date`, deadline-based reporting is simply unavailable — do not fall back to `updatedAt`, `createdAt`, `Estimation`, or sprint names as a pseudo-deadline.

## Reviewer field name differs by project

- CRM, TDR → `Reviewers` (array of logins)
- TT → `Reviewer` (singular)

Using the wrong one silently returns nothing. Check the schema.

## Filtering on deadlines

`has: {Due Date}` works and is the cheap way to find issues that actually carry a deadline:

```
for: me #Unresolved has: {Due Date}
```

Note: at the time of verification this returned **zero** issues for the user — none of their assigned unresolved tasks had a deadline set. That is a normal, expected result, not a broken query. Do not "fix" it by inventing deadlines; it means Signal A is inactive and the report must rest on Signals B/C/D.

Other working forms:

```
for: me #Unresolved Due Date: {minus 7d} .. {Today}
State: -Fixed, -Verified, -Obsolete, -Duplicate
updated: {Last week} .. *
```

Relative-date braces are inconsistent across fields. If a bare relative period returns an empty page, retry with the `.. *` range form before concluding there is no data.

## Tool call gotchas (each of these costs a wasted call)

- `search_issues`: `limit` **maximum is 20**. Passing 25 fails validation.
- `search_issues`: returns summary fields only. Pass `customFieldsToReturn` explicitly to get anything beyond the `['Type','State','Assignee']` default — e.g. `["State","Type","Assignee","Priority","Due Date","Reviewers"]`. Fields you do not request come back absent, which is easy to misread as "empty".
- `get_issue_fields_schema`: the argument is **`projectKey`**, not `project`.
- `find_projects`: the argument is **`nameContains`**, required; empty string lists all.
- `get_issue`: returns `url`, `description`, `commentsCount`, `linkedIssueCounts`, `parentIssue`, `tags`. Use its `url` verbatim in the report.
- `get_issue_comments`: returns `author` (login), `text`, `createdAt`/`updatedAt` as **epoch milliseconds**. Convert before comparing to dates.

## Judging "awaiting my reply" from comments

Compare comment `author` against the user's login from `get_current_user`. A request is unanswered when a comment from someone else poses a question or hands work back, and there is **no later comment by the user** resolving it. A later comment by the user on an unrelated point does not count as an answer — read the content.

Comment threads are also where blockers appear in prose ("ждём", "заблокировано", "нужно решение"). These are evidence; a quiet thread is not.

## Umbrella issues to exclude

Per-person yearly bucket issues (pattern: `[Имя Фамилия] Рабочие вопросы 2026`, `… Встречи 2026`, `… Code Review 2026`, project TT) are permanent containers. They are always open, always assigned, always "stale". Never report them.
