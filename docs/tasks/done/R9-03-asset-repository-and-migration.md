# CARD R9-03 — Asset Repository and Migration

- Round: R9
- Priority: P0
- Status: DONE — independent Review PASS
- Depends on: `R9-02` (DONE, independent Review PASS)

## Goal

Persist assets/versions and migrate existing file metadata safely.

## Before Owner

files + legacy JSON metadata

## After Owner

AssetRepository

## In Scope

- Build repository/service/API.
- Map existing assets.
- Verify checksums/paths and no data loss.

## Out of Scope

- No Resource Library visual redesign yet.

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

- [x] Existing assets are addressable by AssetVersionRef.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: legacy `data/asset_library.json` metadata and filesystem paths were read and written by `main.py` helpers.

After: `SqliteAssetRepository` owns Asset/AssetVersion persistence; `AssetLibraryMigrationService` maps legacy items into immutable version records.

Duplicate owner removed: not yet; legacy JSON remains as a compatibility source until a separately authorized cutover.

## Next Recommended Card

`R9-04`

Do not execute the next card in the same Agent run.

## Developer Verification

- Focused `tests/test_asset_repository_migration.py`: 5 tests PASS.
- `./scripts/agent-verify.sh`: 1191 tests PASS; AST, JavaScript syntax,
  architecture guards, and `git diff --check` PASS.
- Asset and AssetVersion API reads require project authorization; focused tests
  cover missing actors (401) and non-members (403).
- Independent Review remains pending; this card stays ACTIVE.

## Independent Review

- PASS — current Active Task implementation and tests satisfy the card DoD,
  architecture constraints, and ownership change requirements.
- Reviewed after migration-conflict and project-read authorization repairs.
