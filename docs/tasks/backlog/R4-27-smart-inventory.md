# CARD R4-27 — Smart Capability Inventory

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-26

## Goal

Classify every Smart-only retained capability before deleting Smart runtime.

## Before Owner

smart-canvas.js owns product capabilities

## After Owner

explicit migrate/compat/remove/defer decisions

## In Scope

- Inventory Composer, prompt presets, asset UX, media edit/crop/draw/panorama, group actions, cascade/execution.
- Mark each KEEP/MIGRATE/COMPAT/REMOVE/DEFER-R8.

## Out of Scope

- No blind deletion.

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

- [ ] Every Smart-only capability has a disposition and target owner.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-28`

Do not execute the next card in the same Agent run.
