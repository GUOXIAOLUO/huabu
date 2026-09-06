# CARD R4-08 — Rendering Ownership Characterization

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-06T19:05+08:00
- Completed: 2026-09-06T19:20+08:00
- Depends on: R4-07

## Goal

Create a precise rendering ownership map before cutover.

## Before Owner

Classic/Smart/shared mixed ownership

## After Owner

documented ownership matrix

## In Scope

- Inventory Group, Image, Video, Prompt, Loop, Output and provider-shaped nodes.
- For each, record create/update/destroy/listener/media-state owner.
- Identify legacy DOM adoption paths.

## Out of Scope

- No broad rendering rewrite in this card.

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

- [x] Every retained node family has a current owner and target owner. (Group/Image/Prompt/Loop/Output/MiniMax/provider-shaped — both Classic and Smart variants — mapped for create/update/destroy/listeners/media-state in the "Rendering ownership map" section of `docs/plans/R4_OWNERSHIP_MATRIX.md`, with file:line evidence and the six legacy DOM adoption paths.)
- [x] Next migration unit is selected. (The mounted-card lifecycle: route targeted refresh/delete through the `UnifiedRenderHost` handle's `destroy()` — adapters currently never call it, cards die by omission — starting from the three Smart batch mounts and two Classic mounts.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Classic/Smart/shared mixed ownership — rendering responsibilities were
scattered across two monolithic adapters and the shared modules without a
per-family map of who creates, updates, destroys, listens, and owns media
state.

After: Documented ownership matrix — the "Rendering ownership map" section in
`docs/plans/R4_OWNERSHIP_MATRIX.md` records per-family current/target owners
with line evidence, the shared seam list (load-order stable, registry media >
source-payload), the throwaway-DOM/omission-destruction pipeline facts, and the
selected next migration unit. A source-contract test anchors the map's core
claims.

Duplicate owner removed: none — characterization-only card; no ownership moved
and no product behavior changed (the matrix rendering rows gained their
evidence and target-owner column instead).

## Next Recommended Card

`R4-09`

Do not execute the next card in the same Agent run.
