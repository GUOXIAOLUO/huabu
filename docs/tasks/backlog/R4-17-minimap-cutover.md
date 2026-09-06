# CARD R4-17 — Minimap Cutover

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-16

## Goal

Move minimap projection/interaction under unified ownership and retain performance.

## Before Owner

mixed page/shared minimap behavior

## After Owner

Unified interaction/render path

## In Scope

- Migrate minimap update/interaction.
- Profile 100/300 node cases.
- Remove duplicate timers/listeners.

## Out of Scope

- No visual redesign.

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

Add or run the smallest behavioral tests that prove this card's exact goal.
Do not rely only on source-string checks when runtime behavior can be tested.

## Regression

Run:

```bash
./scripts/agent-verify.sh
```

## Definition of Done

- [ ] 100/300 node minimap performance remains acceptable.
- [ ] One minimap owner.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-18`

Do not execute the next card in the same Agent run.
