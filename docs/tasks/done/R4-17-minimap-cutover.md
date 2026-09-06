# CARD R4-17 — Minimap Cutover

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-06T23:25+08:00
- Completed: 2026-09-06T23:29+08:00
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

- [x] 100/300 node minimap performance remains acceptable. (Characterization test pins the linear projection sweep and bounded per-node template work with no layout reads; `updateMinimapViewport` remains the viewport-only fast path — consistent with the recorded 300-node samples, visible 15 ms / offscreen 149 ms P2 follow-up unchanged.)
- [x] One minimap owner. (`WorkbenchInteractionController.createMinimapController` owns the drag interaction — gated pointer capture, projection/apply callbacks, detach-on-mouseup; the Classic minimap no longer assigns `window.onmousemove`/`window.onmouseup`. rAF schedulers verified as the single debounce owners, no duplicate timers existed.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Mixed page/shared minimap behavior — projection math in runtime-state
but the drag interaction wired by direct window handler assignment in the
page.

After: Unified interaction/render path — `createMinimapController` owns the
interaction lifecycle; projection math stays in the kernel; page supplies
`project`/`apply` callbacks over the R4-16 viewport controller. The
ownership-matrix minimap-related rows and map section record the boundary.

Duplicate owner removed: the Classic minimap's direct window-slot pointer
session — replaced by the controller's captured move/up pair detached at
mouseup; no duplicate timers existed (rAF schedulers verified sole owners).

## Next Recommended Card

`R4-18`

Do not execute the next card in the same Agent run.
