# CARD R4-21 — Unified CreationController

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-07T00:22+08:00
- Completed: 2026-09-07T06:12+08:00
- Depends on: R4-20

## Goal

Route all normal node creation entry points through one controller and NodeCreationService.

## Before Owner

page-specific creation entry points

## After Owner

CreationController → NodeCreationService

## In Scope

- Inventory context menu/toolbar/file drop/paste/workflow/connected creation.
- Route one by one through CreationController.
- Remove direct raw Canvas creation paths.

## Out of Scope

- Do not expand NodeCreationService into UI/business logic.

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

- [x] All migrated entry points use same creation boundary. (`createCreationController` on the InteractionController module owns the versioned command envelope and delegates the NodeCreationService client call + result application to injected callbacks; all ten blank-create entry points — Classic Image/Prompt/Loop/Group/Output, Smart Prompt/Loop/Group/MiniMax/Image — call controller singletons and no page calls `WorkbenchNodeClient.create(canvas.id, ...)` directly for blank entries. Inventory recorded in the matrix: provider-shaped `addNode`, file-drop, paste/workflow fragments, and connected creation (service-backed) remain page-owned compatibility for later units.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Page-specific creation entry points — ten blank-create sites with
duplicated versioned command boilerplate (request id, project, source,
definition ref, expected revision) calling the client directly.

After: CreationController → NodeCreationService — the controller owns the
command envelope; pages hold singletons with the client injected as `create`
/`applyResult` callbacks plus their request-id factory. Behavioral test pins
envelope normalization and apply delegation; wiring contracts pin one
controller per adapter and zero direct client create calls.

Duplicate owner removed: per-page versioned command envelope construction for
blank entries — the ten sites now delegate envelope + service-call +
result-application ownership to the shared controller seam.

## Next Recommended Card

`R4-22`

Do not execute the next card in the same Agent run.
