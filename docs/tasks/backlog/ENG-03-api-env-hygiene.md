# CARD ENG-03 — API .env Hygiene

- Round: ENG
- Priority: P1
- Status: BACKLOG
- Depends on: R4-41

## Goal

Remove tracked empty/unsafe env file patterns and provide examples.

## Before Owner

tracked API/.env

## After Owner

untracked secrets + .env.example

## In Scope

- Confirm no secret content/history issue.
- Untrack runtime env file.
- Add example/template and secret scan rule.

## Out of Scope

- Never print real credentials.

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

- [ ] No secret-bearing env file is tracked.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`ENG-04`

Do not execute the next card in the same Agent run.
