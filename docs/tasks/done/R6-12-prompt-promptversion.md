# CARD R6-12 — Prompt / PromptVersion

- Round: R6
- Priority: P0
- Status: DONE — independent Review PASS
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

- [x] Prompt versions are immutable/readable and resolvable by ref.

## Independent Review

- Result: PASS
- Scope: DoD, architecture constraints, and Ownership transition reviewed against the R6-12 implementation and tests.
- Evidence: focused Prompt API tests 2/2; `./scripts/agent-verify.sh` 738/738 tests, AST 125, JavaScript 127, architecture guards 4/4, diff check PASS.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: Prompt content existed as anonymous embedded strings and legacy prompt-library records.

After: `PromptDefinition` owns stable project-scoped identity and `PromptVersion` owns immutable content addressed by `(prompt_id, version)`; repository/service/API provide authorized create, read, resolve, and append-version operations.

Duplicate owner removed: No new duplicate runtime was introduced; legacy embedded prompt compatibility remains explicitly outside this card's canonical Prompt persistence boundary.

## Next Recommended Card

`R6-13`

Do not execute the next card in the same Agent run.
