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

## Exclude issues the Tech Lead is already across

The Tech Lead doesn't need the radar to surface issues they're already personally involved in — assigned to them, reviewing, or reported by them. Exclude with negated filters (verified working syntax, `-` prefix on the value, not on the field). Use `me` so the filter always resolves to whoever the radar runs as:

```
project: PROJ1 for: -me reporter: -me Reviewers: -me
```

Apply this exclusion whenever building the review window (step 1), before scoring anything — an issue the Tech Lead is already assigned to, reviewing, or reported personally should never appear in the radar output, regardless of its attention score.

## Follow-up reads

`search_issues` returns only summary fields. Call `get_issue` on each candidate ID to read the full description, tags, comment/work-item counts, and linked issues before scoring — the summary alone is rarely enough to judge scope expansion or hidden complexity.
