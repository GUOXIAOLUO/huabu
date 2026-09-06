# CARD R4-16 — Viewport / Pan / Zoom Cutover

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-06T23:02+08:00
- Completed: 2026-09-06T23:18+08:00
- Depends on: R4-15

## Goal

Unify viewport state and pan/zoom behavior.

## Before Owner

page runtime viewport wiring

## After Owner

InteractionController + runtime-state

## In Scope

- Migrate pan.
- Migrate zoom/fit/center.
- Preserve viewport persistence/restore.

## Out of Scope

- No semantic zoom redesign.

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

- [x] Pan/zoom/restore pass. (Board pan wires through the InteractionController session lifecycle with the pan kernel session unchanged; wheel zoom goes through `canvasViewportController.zoomAt`; fit/restore/handoff-set/centering dispatch through `set`/`centerOn`. Persistence/restore untouched — local viewport save, payload viewport, and recovery flows pass in the full regression: 347 tests.)
- [x] No duplicate viewport owner. (`createViewportController` is the single dispatch path over the runtime-state kernel for the Classic page; the duplicate `applyCanvasRuntimeViewport` helper is deleted — kernel is the sole dispatch owner, pinned by wiring contract. Smart's pan/zoom wiring is a documented deferred unit.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Page runtime viewport wiring — Classic dispatched viewport commands
through a page-local helper (`applyCanvasRuntimeViewport`), wired pan via
direct window handler assignment and zoom inline in `board.onwheel`.

After: InteractionController + runtime-state — `createViewportController` owns
mutation dispatch over the kernel with the page shell as a callback; the
board-pan pointer session runs through the controller session lifecycle; all
five Classic viewport flows (pan/zoom/fit/restore/handoff+centering) dispatch
through the controller. The ownership-matrix pan/zoom rows and map section
record the boundary.

Duplicate owner removed: the page-local viewport dispatch helper
(`applyCanvasRuntimeViewport`) — every Classic viewport mutation now goes
through the viewport controller; Smart's wiring is a documented deferred
unit.

## Next Recommended Card

`R4-17`

Do not execute the next card in the same Agent run.
