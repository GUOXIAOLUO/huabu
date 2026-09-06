# CARD R4-11 — Image / Media Rendering Cutover

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-06T20:32+08:00
- Completed: 2026-09-06T21:05+08:00
- Depends on: R4-10

## Goal

Move normal image/video rendering and media state projection to the unified renderer path.

## Before Owner

page-created media DOM + shared helper

## After Owner

MediaRenderer under RenderRuntime

## In Scope

- Characterize image/video states.
- Move normal DOM lifecycle to MediaRenderer/RenderRuntime.
- Preserve legacy payload compatibility.
- Remove page ownership for migrated media lifecycle.

## Out of Scope

- Do not build R9 Asset runtime.

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

- [x] Image/video load/error/select/reload paths pass. (Preview-fallback, high-res, playback-state, and versioned media tests pass unchanged; the new projection moves continuity across remounts without altering load/error handling. Full regression 337 tests PASS.)
- [x] Page runtimes no longer create primary media DOM for migrated cases. (On the default path the primary media DOM is MediaRenderer's — mounted inside NodeShell through the runtime — and renderer elements now carry the state signature; the page-level sweeps exclude `.node-shell-mounted` cards, so the pages project only the flags-off fallback DOM, which remains the bounded rollback path.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Page-created media DOM + shared helper — MediaRenderer created the
default-path media elements, but playback-state continuity was projected by
page render sweeps (which could not even see renderer elements, since they
lacked the state signature), leaving mounted media continuity implicit.

After: MediaRenderer under RenderRuntime — the runtime owns media-state
projection for its mounted cards (`mediaState` capture on unmount, restore on
mount, injected over the shared module), MediaRenderer elements carry the
signature URL, and the page sweeps exclude shell-mounted cards. Characterized:
image/video states split between renderer-created default-path DOM and the
adapter fallback markup for flags-off.

Duplicate owner removed: page-level media-state projection for mounted cards —
both sweeps now exclude `.node-shell-mounted`, leaving that responsibility to
the runtime; the ownership-matrix Image rows and map section record the
cutover.

## Next Recommended Card

`R4-12`

Do not execute the next card in the same Agent run.
