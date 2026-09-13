# CARD R8-03 — ExecutionProfile

- Round: R8
- Priority: P0
- Status: DONE — independent Review PASS; archived 2026-09-12
- Depends on: R8-02

## Goal

Represent reusable execution configuration independently from Skill and Model.

## Before Owner

embedded legacy execution config

## After Owner

ExecutionProfile

## In Scope

- Define executor/runtime/model selection/default params/safety/timeouts refs.
- Persist/version appropriately.

## Out of Scope

- Do not store secrets directly.

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

- [x] Task can reference a profile without duplicating executor internals.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: Execution configuration was embedded in legacy execution paths and
Task references had no versioned profile contract.

After: Versioned immutable `ExecutionProfile` records own opaque executor,
runtime-connection, model-availability, safety-policy, default-parameter, and
timeout references. `InMemoryExecutionProfileRepository` preserves exact
`id + version` records without storing secrets.

Duplicate owner removed: SkillBinding continues to hold only an opaque profile
reference; executor internals, provider credentials, and execution-policy
semantics remain owned by their respective boundaries. Durable profile storage
and R8-04 policy remain deferred.

## Next Recommended Card

`R8-04`

Do not execute the next card in the same Agent run.
