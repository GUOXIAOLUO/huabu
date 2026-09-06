# CARD R6-14 — Prompt Resolver

- Round: R6
- Priority: P0
- Status: BACKLOG
- Depends on: R6-13

## Goal

Resolve default/project/task/runtime prompt layers into a deterministic ResolvedPrompt.

## Before Owner

call-site prompt assembly

## After Owner

PromptResolver

## In Scope

- Define precedence.
- Snapshot resolved prompt ref/content metadata for future execution.
- Test overrides.

## Out of Scope

- No model calls.

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

- [ ] Precedence is deterministic and version refs are preserved.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-15`

Do not execute the next card in the same Agent run.
