# CARD R9-12 — Result to Artifact

- Round: R9
- Priority: P0
- Status: BACKLOG
- Depends on: R9-11

## Goal

Explicitly promote selected run result into a formal ArtifactVersion.

## Before Owner

tray-only result

## After Owner

Artifact materialization action

## In Scope

- Create/new version with lineage.
- Support title/type metadata.
- Link Task/Run/result.

## Out of Scope

- No automatic Approved/Frozen.

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

- [ ] Formal output is explicit and traceable.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R9-13`

Do not execute the next card in the same Agent run.
