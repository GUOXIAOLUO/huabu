# CARD R4-09 — Establish Unified RenderRuntime

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-06T19:25+08:00
- Completed: 2026-09-06T19:33+08:00
- Depends on: R4-08

## Goal

Create a real RenderRuntime that owns lifecycle rather than another helper facade.

## Before Owner

page runtimes + hosts

## After Owner

Unified RenderRuntime

## In Scope

- Define mount/update/unmount contract.
- Own renderer selection and NodeShell lifecycle.
- Wire one bounded node family through it.
- Prove duplicate page ownership is removed for that responsibility.

## Out of Scope

- Do not migrate every node family at once.

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

- [x] RenderRuntime owns a complete lifecycle slice. (`WorkbenchRenderRuntime` in `static/js/workbench/canvas/render-runtime.js` owns the mounted-handle registry keyed by node id: mount/mountAll record, same-id remount destroys the previous handle in order, unmount destroys and forgets, unmountAll clears on canvas load. Behavioral sandbox test proves the ordering; all five adoption mounts, both delete flows, and both canvas-load resets in the two adapters route through it.)
- [x] At least one former page owner is removed. (Per-page direct card mounting through `UnifiedRenderHost.mountAdapterCard(s)` with discarded handles no longer exists — each adapter keeps exactly one injected host mount and every card mount/unmount flows through the runtime; pinned by the wiring contract test, which also replaced three prior direct-mount assertions.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Page runtimes + hosts — both adapters called `UnifiedRenderHost.mountAdapterCard(s)` directly at every mount site and discarded the returned handles; cards died by omission from the next render sweep and nobody owned mounted-card destruction.

After: Unified RenderRuntime — `WorkbenchRenderRuntime` owns the mounted-card lifecycle (mount bookkeeping, ordered destroy on unmount/remount, batch mounting, canvas-load reset) with the host mount injected once per page; the R4-08 map section records the unit as completed.

Duplicate owner removed: per-page direct card-mount ownership (five direct host call sites reduced to one injected mount per adapter; all unmount/destruction flows moved into the runtime).

## Next Recommended Card

`R4-10`

Do not execute the next card in the same Agent run.
