# CARD R12-11 — CapabilityResolver

- Round: R12
- Priority: P0
- Status: BACKLOG
- Depends on: R12-10

## Goal

Resolve Skill capability requirements to Integration/Executor/Human routes.

## Before Owner

hardcoded route decisions

## After Owner

CapabilityResolver

## In Scope

- Match available integrations/executors/human fallback policies.
- Return explicit route/reason.
- Support project package constraints.

## Out of Scope

- No silent route substitution.

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

- [ ] Same Skill can resolve different valid implementation routes.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R12-12`

Do not execute the next card in the same Agent run.
