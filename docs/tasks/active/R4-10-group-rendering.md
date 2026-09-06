# CARD R4-10 — Group Rendering Cutover

- Round: R4
- Priority: P1
- Status: ACTIVE
- Activated: 2026-09-06T19:38+08:00
- Depends on: R4-09

## Goal

Use Group as the first complete rendering ownership proof.

## Before Owner

Classic/Smart group rendering

## After Owner

Unified RenderRuntime

## In Scope

- Move group mount/update/unmount to unified rendering.
- Preserve position/size/reload/delete behavior.
- Remove duplicate group rendering callbacks from page runtimes.

## Out of Scope

- Do not redesign Group semantics.

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

- [ ] Create/render/update/move/resize/reload/delete pass.
- [ ] Only one product rendering owner remains.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-11`

Do not execute the next card in the same Agent run.
