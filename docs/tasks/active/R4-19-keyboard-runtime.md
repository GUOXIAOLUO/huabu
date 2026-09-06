# CARD R4-19 — Keyboard Runtime Cutover

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-06T23:50+08:00
- Completed: 2026-09-06T23:58+08:00
- Depends on: R4-18

## Goal

Unify keyboard command handling.

## Before Owner

page-specific keyboard handlers

## After Owner

Unified command/interaction runtime

## In Scope

- Migrate delete/copy/paste/select-all/group shortcuts.
- Preserve undo/redo compatibility as characterized.
- Remove duplicate listeners.

## Out of Scope

- Do not redesign command palette.

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

- [x] Keyboard behavior passes with one listener/owner path. (`createKeyboardRuntime` on the InteractionController module installs exactly one keydown/keyup listener pair per page; the Classic main keydown/keyup pair and the Smart main keydown handler register with it, and the direct `window.addEventListener('keydown'/'keyup')` blocks for those handlers are removed — pinned by wiring contract. Dispatch order, short-circuit on true, and handler unregistration are pinned behaviorally. The composed delete/copy/paste/group/undo-redo handlers are unchanged, preserving undo/redo compatibility; the full regression passes at 354 tests.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Page-specific keyboard handlers — each page added its own
`window.addEventListener('keydown'/'keyup')` for the main shortcut block,
duplicating listener ownership.

After: Unified command/interaction runtime — `createKeyboardRuntime` owns the
window keyboard listener pair and ordered handler dispatch; both adapters
register their main handlers with it. The Smart Escape-only dispatcher and
inspector-scoped listeners remain scoped/complementary. The ownership-matrix
keyboard row and narrative record the boundary.

Duplicate owner removed: the per-page direct window keyboard listener blocks
for the main shortcut handlers — one listener pair per adapter remains,
owned by the keyboard runtime.

## Next Recommended Card

`R4-20`

Do not execute the next card in the same Agent run.
