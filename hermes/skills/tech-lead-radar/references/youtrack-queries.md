# YouTrack Query Patterns (tested)

Working `search_issues` query patterns for building the review window (step 1). YouTrack's relative-date braces are inconsistent across fields — prefer the range form when a bare relative period returns nothing.

## Recently updated/created issues

```
updated: {Last week} .. *
created: {This week}
updated: {minus 2h} .. *
```

`updated: {This week}` alone can return an empty page even when matching issues exist — if a bare relative period returns nothing, retry with the `.. *` range form before concluding there is no data.

## Scope to specific projects

Comma-separate project keys for OR:

```
project: PROJ1, PROJ2, PROJ3 updated: {Last week} .. *
```

## Combine with state/assignee filters

```
project: PROJ1 #Unresolved updated: {Last week} .. *
project: PROJ1 for: me
State: -Fixed, -Verified, -Obsolete, -Duplicate
```

## Follow-up reads

`search_issues` returns only summary fields. Call `get_issue` on each candidate ID to read the full description, tags, comment/work-item counts, and linked issues before scoring — the summary alone is rarely enough to judge scope expansion or hidden complexity.
