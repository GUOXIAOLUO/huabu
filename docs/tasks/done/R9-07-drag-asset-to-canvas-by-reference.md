# CARD R9-07 — Drag Asset to Canvas by Reference

- Round: R9
- Priority: P0
- Status: DONE — independent Review PASS; archived 2026-09-14
- Depends on: R9-06

## Goal

Ensure resource drag creates a reference node, not copied file content.

## Before Owner

legacy upload/create behavior

## After Owner

AssetVersionRef-based Canvas materialization

## In Scope

- Add drag payload contract.
- Create Asset node referencing exact version.
- Verify file is not duplicated.

## Out of Scope

- No automatic new AssetVersion on drag.

## Compatibility / Migration

- Preserve existing behavior and data unless the card explicitly authorizes a migration.

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

- Add/run the smallest behavioral tests that prove this card's goal.
- Run `./scripts/agent-verify.sh`.

## Definition of Done

- [x] Multiple Canvas nodes can reference the same version safely.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: Canvas accepted legacy URL/file payloads and had no AssetVersion reference path.

After: `WorkbenchAssetReferenceMaterializer` consumes the version identity payload and routes creation through the existing `NodeCreationService` endpoint; each node stores only `asset_version_ref {asset_id, version_id}`.

Duplicate owner removed: none introduced; the inspector remains the drag-payload producer and the Canvas creation controller remains the mutation seam.

## Next Recommended Card

`R9-08`

Do not execute the next card in the same Agent run.
