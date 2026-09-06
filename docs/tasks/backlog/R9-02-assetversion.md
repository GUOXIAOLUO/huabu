# CARD R9-02 — AssetVersion

- Round: R9
- Priority: P0
- Status: BACKLOG
- Depends on: R9-01

## Goal

Add immutable/versioned asset content records with checksums/provenance.

## Before Owner

mutable file metadata

## After Owner

AssetVersion

## In Scope

- Define version/content location/checksum/mime/size/provenance/timestamps.
- Create versioning rules.

## Out of Scope

- Do not duplicate file bytes on Canvas drag.

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

- [ ] Version refs are stable and immutable.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R9-03`

Do not execute the next card in the same Agent run.
