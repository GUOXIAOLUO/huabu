# CARD R9-03 — Asset Repository and Migration

- Round: R9
- Priority: P0
- Status: BACKLOG
- Depends on: R9-02

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

- [ ] Existing assets are addressable by AssetVersionRef.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R9-04`

Do not execute the next card in the same Agent run.
