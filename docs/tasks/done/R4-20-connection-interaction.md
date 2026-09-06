# CARD R4-20 — Connection Interaction Cutover

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-07T00:05+08:00
- Completed: 2026-09-07T00:15+08:00
- Depends on: R4-19

## Goal

Unify port hover, draft edge, validation and drop interaction.

## Before Owner

page-specific connect UI

## After Owner

InteractionController

## In Scope

- Migrate connection gesture lifecycle.
- Keep persistence mutation behind application service.
- Preserve cancel/error states.

## Out of Scope

- Do not encode legacy side effects in Core interaction.

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

- [x] Connection UI has one owner. (`createConnectionGestureController` on the InteractionController module owns the port-drag gesture lifecycle — captured move/up pair, hover pipeline (resolveTarget → validate → gesture.target/result), end dispatch (drop | noTarget | finish), detach-on-mouseup, cancel(); Classic `startLink` and Smart's port drag both begin controller gestures, and Smart's `portDragState` dispatcher branches are removed — pinned by wiring contract and the updated port-hover contract test.)
- [x] Persistence is not directly mutated by UI controller. (The controller module has no save/fetch API surface — pinned; commits flow through page callbacks: Classic `scheduleSave()`, Smart `handlePortDrop` → `scheduleSave()`, both behind the existing application service seams. Undo discard/commit and port-create-menu error states preserved.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Page-specific connect UI — Classic wired the draft-edge gesture via
direct window handler assignment inside `startLink`; Smart ran port-drag
hover/move/up branches inside its global dispatcher; hover validation was
duplicated between the two pages and the drop paths.

After: InteractionController — the connection gesture controller owns the
gesture lifecycle and hover pipeline over injected page callbacks; pages keep
draft rendering, DOM target resolution, shared intent/compatibility
validation, product branches (generator output / link-create menu), and
persistence behind application seams. The ownership-matrix connection-start
row and narrative record the boundary.

Duplicate owner removed: the per-page gesture wiring — Classic's direct
window-slot assignment and Smart's dispatcher `portDragState` branches no
longer exist; one gesture lifecycle owner remains per page, instantiated from
the shared controller.

## Next Recommended Card

`R4-21`

Do not execute the next card in the same Agent run.
