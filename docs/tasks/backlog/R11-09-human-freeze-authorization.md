# CARD R11-09 — Human Freeze Authorization

- Round: R11
- Priority: P0
- Status: BACKLOG
- Depends on: R11-08

## Goal

Guarantee only authorized human action can freeze a formal version.

## Before Owner

potential generic state update

## After Owner

authorized freeze service

## In Scope

- Add authorization policy.
- Require target exact ArtifactVersion.
- Audit event.

## Out of Scope

- No Agent/executor freeze route.

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

- [ ] Tests prove agent/runtime identities cannot freeze.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R11-10`

Do not execute the next card in the same Agent run.
