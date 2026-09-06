# CARD R4-18 — Drag / Resize Cutover

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-06T23:36+08:00
- Completed: 2026-09-06T23:43+08:00
- Depends on: R4-17

## Goal

Unify node drag and resize behavior.

## Before Owner

duplicated page interaction

## After Owner

InteractionController

## In Scope

- Migrate single drag/resize.
- Preserve multi-selection/group behavior where characterized.
- Persist/reload correctly.

## Out of Scope

- No new snapping product feature.

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

- [x] Drag/resize/save/reload pass. (Full regression 352 tests including the shared drag/resize projection contracts with updated factory identifiers; session math, multi-selection/group membership, thumb-detach, DOM application, persistence and reload unchanged.)
- [x] No duplicate product owner. (`createNodeDragSessionFactory`/`createNodeResizeSessionFactory` on the InteractionController module own node drag/resize session construction over the kernel; all five page session-creation sites call controller factory singletons and no page wires `WorkbenchCanvasRuntime` kernel session methods directly — pinned by wiring contract.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Duplicated page interaction — each page invoked kernel session
creation directly (`WorkbenchCanvasRuntime?.createNodeDragSession` /
`createNodeResizeSession`) at five sites with no shared seam.

After: InteractionController — the factories own session construction
(injected kernel, validation); pages hold factory singletons. The
ownership-matrix drag row and narrative record the boundary.

Duplicate owner removed: direct kernel session-creation calls in the page
runtimes — replaced by controller factory singletons; the kernel remains the
pure math owner and the controller the sole construction seam.

## Next Recommended Card

`R4-19`

Do not execute the next card in the same Agent run.
