# CARD R8-22 — Result to Canvas Materialization

- Round: R8
- Priority: P0
- Status: BACKLOG
- Depends on: R8-21

## Goal

Materialize selected result explicitly as a Canvas node.

## Before Owner

implicit/legacy output nodes

## After Owner

explicit materialization service/action

## In Scope

- Define materialization command.
- Create generic compatible node/ref.
- Preserve source run/attempt lineage.

## Out of Scope

- Never auto-create one node per output.

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

- [ ] Only explicit user/application action creates Canvas node.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R9-01`

Do not execute the next card in the same Agent run.
