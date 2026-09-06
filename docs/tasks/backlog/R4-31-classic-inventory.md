# CARD R4-31 — Classic Capability Inventory

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-30

## Goal

Classify Classic-only retained capabilities before deleting Classic runtime.

## Before Owner

canvas.js owns product capabilities

## After Owner

explicit disposition map

## In Scope

- Inventory provider cards, Comfy, RunningHub, MiniMax, LTX, video, output/log/asset/cascade/execution.
- Assign target owner/disposition.

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

- [ ] Every Classic-only capability has target disposition.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-32`

Do not execute the next card in the same Agent run.
