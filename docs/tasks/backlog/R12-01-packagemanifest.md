# CARD R12-01 — PackageManifest

- Round: R12
- Priority: P0
- Status: BACKLOG
- Depends on: R11-15

## Goal

Define the installable package contract for domain extensions.

## Before Owner

hardcoded future vertical modules

## After Owner

PackageManifest

## In Scope

- Define id/version/compatibility/definitions/skills/prompts/entities/catalogs/workflows/workspaces/integrations metadata.
- Validate manifest.

## Out of Scope

- No WholeHouse implementation yet.

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

- [ ] Package can declare extensions without Core code changes.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R12-02`

Do not execute the next card in the same Agent run.
