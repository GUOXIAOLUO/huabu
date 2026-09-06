# CARD R16-06 — Scheme Comparison Workspace

- Round: R16
- Priority: P1
- Status: BACKLOG
- Depends on: R16-05

## Goal

Create a WholeHouse workspace extension for comparing design schemes using generic Artifact/Result refs.

## Before Owner

generic result compare only

## After Owner

WholeHouse comparison workspace extension

## In Scope

- Show render/material/product/design differences.
- Use package presentation extension rather than new node kind.
- Link decisions.

## Out of Scope

- No separate WholeHouse canvas.

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

- [ ] Workspace operates on generic refs and package schema.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R16-07`

Do not execute the next card in the same Agent run.
