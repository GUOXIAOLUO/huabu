# CARD R12-03 — PackageVersion

- Round: R12
- Priority: P0
- Status: BACKLOG
- Depends on: R12-02

## Goal

Represent package versions and compatibility explicitly.

## Before Owner

implicit code version

## After Owner

PackageVersion metadata

## In Scope

- Persist installed versions.
- Check Workbench compatibility.
- Expose migrations.

## Out of Scope

- No auto-upgrade of project semantics.

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

- [ ] Multiple project locks can refer to different package versions conceptually.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R12-04`

Do not execute the next card in the same Agent run.
