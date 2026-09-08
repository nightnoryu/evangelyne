# Special Rules

## PM-Proposed Solutions

A task should receive additional attention when a PM or business-oriented stakeholder proposes a concrete technical implementation.

Do NOT treat this as inherently wrong.

Instead, check whether the proposed solution leaves important engineering questions unanswered.

For example:

> "Add a button that recalculates all clients synchronously."

Potential questions:

- How many clients can this affect?
- What is the expected execution time?
- What happens on timeout?
- Is the operation idempotent?
- What happens if it fails halfway through?
- Should it be asynchronous?
- How will progress be observed?

Report the engineering questions, not criticism of the PM.

## Test Coverage

Do not use "no tests" as an automatic reason to escalate.

Instead evaluate:

1. How risky is the behavior being changed?
2. How difficult is regression to detect manually?
3. How stable is the expected behavior?
4. What verification mechanism exists?
5. What is the cost of a regression?

A trivial configuration change may reasonably have no automated tests.

A substantial business-rule change without regression protection is much more interesting.
