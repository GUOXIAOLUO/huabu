# CARD R6-03 — Binding Resolver

- Round: R6
- Priority: P0
- Status: BACKLOG
- Depends on: R6-02

## Goal

Resolve generic binding references into normalized inputs.

## Before Owner

call-site-specific resolution

## After Owner

BindingResolver

## In Scope

- Support asset-like, artifact-like, collection, entity-like and literal references at the abstraction level available.
- Keep unresolved/future references explicit.
- Return typed errors.

## Out of Scope

- No model invocation.

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

- [ ] Bindings resolve deterministically and do not rely on Canvas edges.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-04`

Do not execute the next card in the same Agent run.
