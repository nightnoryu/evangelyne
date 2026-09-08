# Engineering Signals Catalog

Detailed signal catalog for step 3 (Identify engineering signals). Open this when scoring a task's attention level.

## Architecture

Increase attention when a task involves:

- new services;
- changing service boundaries;
- changes to shared domain models;
- changes to APIs;
- changes to contracts between systems;
- asynchronous processing;
- queues;
- background jobs;
- event-driven flows;
- database migrations;
- large data backfills;
- changes to shared infrastructure;
- introducing a new external dependency.

## Production risk

Increase attention when a task involves:

- production data;
- bulk operations;
- changes affecting many users or clients;
- permissions or access control;
- billing or financial logic;
- personally identifiable information;
- authentication;
- external integrations;
- irreversible operations;
- migrations;
- scheduled jobs;
- changes with difficult rollback.

## Complexity hidden behind simple wording

Pay special attention when a task looks deceptively simple.

Examples:

"Add a field to Client"

may actually imply:

- database migration;
- backfill;
- PowerBI changes;
- API changes;
- compatibility with existing clients.

"Add a button to recalculate clients"

may imply:

- a potentially huge bulk operation;
- asynchronous processing;
- idempotency;
- authorization;
- progress tracking;
- retry handling;
- rollback;
- observability.

Look for this mismatch between apparent task size and actual system impact.

## Requirements quality

Increase attention when:

- acceptance criteria are unclear;
- implementation details are prescribed without technical discussion;
- important edge cases are unspecified;
- failure behavior is undefined;
- rollback is not considered for risky changes;
- the task crosses system boundaries but describes only one side;
- the proposed solution appears to solve the symptom rather than the underlying problem.

## Testing and verification

Increase attention when:

- there is no apparent test strategy;
- the task changes business-critical behavior without describing verification;
- a substantial refactoring has no regression protection;
- a data migration has no validation strategy;
- a new integration has no integration/contract testing strategy;
- a production change has no monitoring or observability consideration.

Do not blindly require unit tests for every task.

Ask:

> How will we know this works, and how will we know it stays working?

The appropriate answer may be:
- unit tests;
- integration tests;
- contract tests;
- end-to-end tests;
- migration validation;
- monitoring;
- manual verification;
- another explicit verification strategy.
