# CARD R4-22 — File Drop Unified Creation

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-07T06:53+08:00
- Depends on: R4-21 (DONE, review closed)

## Goal

Route image/video/pdf/file drop through unified creation.

## Before Owner

page-specific file drop

## After Owner

CreationController

## In Scope

- Characterize file drop types.
- Create via NodeCreationService/compat adapter.
- Preserve old records and upload behavior.

## Out of Scope

- Do not build AssetVersion runtime.

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

- [x] File drop creates through unified boundary and reloads correctly.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

Classic and Smart created top-level dropped media by directly constructing page-owned nodes and saving raw Canvas payloads.

After:

`CreationController` creates supported top-level dropped media through `NodeCreationService`; the Legacy compatibility repository persists the media payload needed for reload.

Duplicate owner removed:

The default top-level Classic and Smart file-drop materialization paths no longer need page-generated node IDs or raw node appends. Target-node fills, group layout and unsupported compatibility paths remain adapter-owned.

## Next Recommended Card

`R4-23`

Do not execute the next card in the same Agent run.
