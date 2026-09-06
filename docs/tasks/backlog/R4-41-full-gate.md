# CARD R4-41 — R4 Full Acceptance Gate

- Round: R4
- Priority: P0
- Status: BACKLOG
- Depends on: R4-40

## Goal

Prove Unified Canvas Cutover is complete before activating R5.

## Before Owner

R4 in_progress

## After Owner

R4 PASS or explicit blocker report

## In Scope

- Run data/restart/stale-write tests.
- Run selection/drag/resize/zoom/pan/keyboard/connect/group/clipboard.
- Run media/workflow compatibility.
- Run 100/300 node performance and listener/timer/DOM duplication checks.
- Verify one page/runtime/persistence/render/interaction/creation owner.

## Out of Scope

- Do not mark PASS with known duplicate runtime ownership.

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

- [ ] Every formal R4 gate item passes or R4 remains in_progress with concrete blockers.
- [ ] Only after full PASS may active_round become R5.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R5-01`

Do not execute the next card in the same Agent run.
