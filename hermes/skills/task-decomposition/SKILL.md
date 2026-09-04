---
name: task-decomposition
description: Use when planning a feature, project, or initiative — decomposes work into atomic blocks organized by milestones, each independently releasable with clear value. Handles roadmap creation, sprint planning, breaking down epics, WBS, parallel workstreams, and delivery planning.
---

# Task Decomposition

Decomposes any feature or project into a structured `roadmap.md` with atomic tasks grouped into milestones. Each milestone delivers independent value and can be released separately. Parallel workstreams are identified and scheduled together.

## Process

### 1. Clarify Scope

Ask the user targeted questions. Do not ask all at once — probe iteratively based on answers. Cover:

| Dimension | Questions |
|-----------|-----------|
| **Goal** | What problem are we solving? What does success look like? |
| **Users** | Who benefits? Internal team, end users, ops? |
| **Constraints** | Deadlines, tech limits, dependencies on other teams? |
| **Existing** | What already exists? Legacy code, partial implementations? |
| **Risk** | What could go wrong? Unknowns, integrations, data migration? |
| **Definition of done** | What counts as "shippable"? Tests, docs, monitoring? |

If the user already provided context, use it and only ask what's genuinely missing.

### 2. Identify Milestones

A milestone is a **shippable slice of value**. Not a technical phase. Each milestone should:

- Deliver something a user or stakeholder can see/use
- Be completable by a small team in 1-3 weeks
- Stand alone — not depend on a later milestone
- Build on earlier milestones naturally

Structure milestones as **incremental value delivery**:

```
Milestone 1: Minimum valuable slice (core flow works)
Milestone 2: Expand coverage / polish / edge cases
Milestone 3: Scale, performance, automation, observability
```

### 3. Decompose into Atomic Blocks

Under each milestone, list tasks that are:

- **Atomic**: One task = one reviewable unit of work
- **Small**: Estimable at ≤ 2 days of focused work
- **Actionable**: Starts with a verb, describes concrete output
- **Independent**: No hidden dependencies on other tasks in the same milestone

When a task spans multiple domains (frontend + backend + infra), split it.

### 4. Map Dependencies and Parallelism

For each milestone, identify:

- **Sequential chains**: Task B cannot start until Task A finishes
- **Parallel tracks**: Tasks that can run simultaneously (mark them)
- **Cross-milestone blockers**: Things that must finish before the next milestone starts

Use this notation in the roadmap:
- `ParallelGroup:` wraps tasks runnable in parallel
- `→` marks dependency (A → B means B waits for A)

### 5. Produce `roadmap.md`

Write the file. Follow the template in [assets/roadmap-template.md](assets/roadmap-template.md).

After writing, present a summary to the user:
- Number of milestones
- Total atomic blocks
- Critical path (longest sequential chain)
- Parallel opportunities

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Milestones are technical phases ("design", "implement", "test") | Make milestones about delivered value |
| Tasks are vague ("improve performance", "handle errors") | Specify the exact change and its observable result |
| Tasks are too big ("build the API") | Split into endpoints, models, validation, docs |
| Dependencies hidden inside tasks | Surface them explicitly with `→` notation |
| Milestone depends on a later milestone to be useful | Reorder or restructure so value arrives earlier |

## Check

Before delivering the roadmap, verify:

- [ ] Every milestone is independently shippable
- [ ] Every task is atomic (≤ 2 days of work)
- [ ] Parallel opportunities are marked
- [ ] Dependencies are explicit, not implied
- [ ] The first milestone delivers real value on its own
