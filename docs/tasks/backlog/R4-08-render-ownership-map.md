# CARD R4-08 — Rendering Ownership Characterization

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-07

## Goal

Create a precise rendering ownership map before cutover.

## Before Owner

Classic/Smart/shared mixed ownership

## After Owner

documented ownership matrix

## In Scope

- Inventory Group, Image, Video, Prompt, Loop, Output and provider-shaped nodes.
- For each, record create/update/destroy/listener/media-state owner.
- Identify legacy DOM adoption paths.

## Out of Scope

- No broad rendering rewrite in this card.

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

- [ ] Every retained node family has a current owner and target owner.
- [ ] Next migration unit is selected.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-09`

Do not execute the next card in the same Agent run.
