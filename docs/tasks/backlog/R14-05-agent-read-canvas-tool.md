# CARD R14-05 — Agent read_canvas Tool

- Round: R14
- Priority: P0
- Status: BACKLOG
- Depends on: R14-04

## Goal

Expose structured Canvas read projection to Agent.

## Before Owner

potential raw Canvas JSON

## After Owner

read_canvas projection

## In Scope

- Return nodes/edges/selection/context through application read model.
- Include revision.
- Filter implementation-only payloads.

## Out of Scope

- No raw DOM or direct mutable object refs.

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

- [ ] Agent gets sufficient context without persistence internals.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R14-06`

Do not execute the next card in the same Agent run.
