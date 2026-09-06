# CARD R4-14 — Establish InteractionController

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-06T22:10+08:00
- Completed: 2026-09-06T22:23+08:00
- Depends on: R4-13

## Goal

Create a single interaction owner over the existing pure runtime-state/math kernel.

## Before Owner

Classic/Smart page interaction state

## After Owner

Unified InteractionController

## In Scope

- Define interaction lifecycle and event wiring.
- Use runtime-state as state/math kernel.
- Migrate one bounded interaction responsibility first.

## Out of Scope

- No full rewrite in one patch.

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

- [x] One complete interaction responsibility has a single unified owner. (The Classic node-drag and node-resize pointer-session lifecycle — begin wiring, move dispatch, mouseup end, programmatic end — is owned by `WorkbenchInteractionController` (`static/js/workbench/canvas/interaction-controller.js`); `startNodeDrag`/`startNodeResize` begin controller sessions and the direct `window.onmousemove`/`window.onmouseup` assignments are gone. Behavioral test pins the lifecycle semantics; wiring contract pins both session kinds and the removed assignments. Smart's multi-concern dispatcher is deliberately deferred and documented.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Classic/Smart page interaction state — each page wired pointer
sessions by assigning the window move/up handler slot directly (Classic
per-session assignment; Smart one permanent multi-concern dispatcher), with
no session tracking or explicit end.

After: Unified InteractionController — `create({windowRef})` owns
pointer-session lifecycle over the runtime-state kernel's pure sessions
(`begin`/`end`/`activeKind` with supersede-on-begin and guarded no-ops after
mouseup); Classic's node-drag and node-resize sessions are migrated; the
ownership-matrix drag row and map section record the boundary.

Duplicate owner removed: Classic's direct window move/up handler assignments
for node-drag and node-resize — the page now begins controller sessions
instead; Smart's dispatcher migration is documented as the follow-up unit.

## Next Recommended Card

`R4-15`

Do not execute the next card in the same Agent run.
