# CARD R5-06 — NodeShell V2 Contract

- Round: R5
- Priority: P1
- Status: BACKLOG
- Depends on: R5-05

## Goal

Stabilize the generic shell contract for Rich Node presentation.

## Before Owner

R4 shell/renderer contracts

## After Owner

NodeShell V2

## In Scope

- Define header/title/status/ports/content/actions/footer/resize slots.
- Define intent events instead of business callbacks.
- Preserve existing renderer compatibility through adapters.

## Out of Scope

- No WholeHouse-specific UI.
- No Skill Runtime.

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

- [ ] Shell contains no provider/industry logic.
- [ ] Existing generic nodes can render through the contract.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R5-07`

Do not execute the next card in the same Agent run.
