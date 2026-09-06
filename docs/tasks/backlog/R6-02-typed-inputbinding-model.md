# CARD R6-02 — Typed InputBinding Model

- Round: R6
- Priority: P0
- Status: BACKLOG
- Depends on: R6-01

## Goal

Replace transitional list[dict] input bindings with a typed domain model.

## Before Owner

untyped NodeRecord input_bindings

## After Owner

InputBinding model

## In Scope

- Define binding id/target/source_type/source_ref/role/order/enabled/metadata.
- Add validation/serialization.
- Add compatibility adapter for existing payloads.

## Out of Scope

- No execution yet.

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

- [ ] Typed model round-trips and legacy payloads remain readable.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-03`

Do not execute the next card in the same Agent run.
