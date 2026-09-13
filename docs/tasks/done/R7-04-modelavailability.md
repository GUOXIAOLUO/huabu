# CARD R7-04 — ModelAvailability

- Round: R7
- Priority: P0
- Status: DONE — independent Review PASS; closed 2026-09-11
- Depends on: R7-03

## Goal

Represent a model available through a specific connection/runtime.

## Before Owner

implicit provider+model pair

## After Owner

ModelAvailability

## In Scope

- Define model ref/connection ref/status/limits/runtime route.
- Add availability repository/service.

## Out of Scope

- Codex itself is not a ModelDefinition.

## Compatibility / Migration

- Preserve existing behavior and data unless the card explicitly authorizes a migration.

## Execution Pattern

```text
characterize
→ focused test
→ establish seam
→ implement/migrate
→ verify
→ remove duplicate ownership
```

## Focused Tests

- Add/run the smallest behavioral tests that prove this card's goal.
- Run `./scripts/agent-verify.sh`.

## Definition of Done

- [x] Same model can have multiple availability routes.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

Model access was represented as an implicit provider-plus-model pair, without
an explicit route identity or availability record.

After:

`ModelAvailability` owns model reference, neutral provider/runtime route,
route reference, executor type, normalized capabilities, constraints, enabled
flag, status, and native metadata. The application service and repository
boundary register and query multiple explicit routes without selecting or
executing them.

Duplicate owner removed:

No ModelDefinition identity, ProviderConnection, CredentialRef, Executor,
Codex protocol, Canvas, or Node persistence ownership was added. Durable
availability storage remains deferred; the in-memory repository is the bounded
repository seam for this card.

## Next Recommended Card

`R7-05`

Do not execute the next card in the same Agent run.

## Implementation Evidence

Focused `tests/test_model_availability.py` coverage passes (2 tests), proving
one model can expose independent provider and runtime routes, repository/service
lookup, v2 schema identity, and separation from ModelDefinition/provider
credentials. The domain also rejects duplicate capabilities and credential-like
metadata. Related provider/model tests remain green. `./scripts/agent-verify.sh`
passes with 778 tests, 149 Python AST files, 133 JavaScript files, 4
architecture guards, and clean diff check. R7-04 remains ACTIVE pending
independent Review; R7-05 was not started.
