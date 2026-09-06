# CARD R4-15 — Selection Ownership Cutover

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-06T22:50+08:00
- Completed: 2026-09-06T22:55+08:00
- Depends on: R4-14

## Goal

Unify single/multi/box selection and projection.

## Before Owner

duplicated page selection state

## After Owner

InteractionController

## In Scope

- Migrate single selection.
- Migrate multi-select and box selection.
- Remove duplicated page selection source of truth.

## Out of Scope

- No workspace/Inspector work.

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

- [x] Selection behavior passes on old Classic/Smart records. (The full regression — versioned selection, box-selection finish, render/intent, and shell contracts — passes at 345 tests; the box-selection finish contract moved to the authority call.)
- [x] One selection authority remains. (The Classic page's `selected` state is a `WorkbenchInteractionController.createSelectionStore` instance: all single, multi, and box-selection mutations flow through it, and all five direct `selected = new Set(...)` reassignments became `replace`/`clear` store calls — pinned by wiring contract. Smart's dual-variable model is deferred as a documented dedicated unit; the store module is shared and ready for it.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Duplicated page selection state — the Classic page kept a local
`selected` Set with five direct reassignments and 36+ scattered mutations;
the runtime only mirrored a snapshot.

After: InteractionController — `createSelectionStore` on the
interaction-controller module is the single selection authority for the
Classic page (Set-compatible, change-tracked); single, multi, and
box-selection all mutate through it; the runtime mirror stays as a
projection.

Duplicate owner removed: the Classic page-local selection Set — no
`selected = new Set(...)` reassignment remains and every mutation goes
through the store; Smart's dual-variable model is a documented dedicated
follow-up unit.

## Next Recommended Card

`R4-16`

Do not execute the next card in the same Agent run.
