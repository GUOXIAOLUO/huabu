# CARD R9-09 — ArtifactVersion and Lineage

- Round: R9
- Priority: P0
- Status: BACKLOG
- Depends on: R9-08

## Goal

Create immutable ArtifactVersion with execution/input lineage.

## Before Owner

mutable outputs

## After Owner

ArtifactVersion

## In Scope

- Define immutable version payload/content refs.
- Attach source run/attempt/input/prompt/model/skill lineage.
- Add repository/service/API.

## Out of Scope

- Do not overwrite prior versions.

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

- [ ] Every formal result version has lineage.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R9-10`

Do not execute the next card in the same Agent run.
