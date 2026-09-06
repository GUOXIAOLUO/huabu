# CARD R9-06 — Asset Inspector and Versions

- Round: R9
- Priority: P1
- Status: BACKLOG
- Depends on: R9-05

## Goal

Show preview, metadata, versions, provenance and usage references.

## Before Owner

legacy asset panels

## After Owner

Asset Inspector

## In Scope

- Render current version/history.
- Show used-by references where available.
- Expose drag/open/version actions.

## Out of Scope

- No approval semantics.

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

- [ ] Asset versions are understandable and traceable.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R9-07`

Do not execute the next card in the same Agent run.
