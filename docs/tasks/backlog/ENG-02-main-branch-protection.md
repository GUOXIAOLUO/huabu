# CARD ENG-02 — Main Branch Protection

- Round: ENG
- Priority: P1
- Status: BACKLOG
- Depends on: R4-41

## Goal

Protect main after R4 stabilization.

## Before Owner

unprotected main

## After Owner

protected main with required review/checks

## In Scope

- Require PR/review as appropriate.
- Require CI checks.
- Document emergency path.

## Out of Scope

- Do not block local development workflows unnecessarily.

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

- [ ] Main cannot accept unchecked direct changes under normal policy.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`ENG-03`

Do not execute the next card in the same Agent run.
