# CARD R6-12 — Prompt / PromptVersion

- Round: R6
- Priority: P0
- Status: BACKLOG
- Depends on: R6-11

## Goal

Make Prompt a versioned first-class resource.

## Before Owner

anonymous embedded prompt strings

## After Owner

Prompt + PromptVersion

## In Scope

- Define domain model/versioning.
- Add repository/service/API.
- Keep legacy embedded prompt compatibility.

## Out of Scope

- No prompt marketplace.

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

- [ ] Prompt versions are immutable/readable and resolvable by ref.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-13`

Do not execute the next card in the same Agent run.
