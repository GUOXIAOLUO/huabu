# CARD R6-14 — Prompt Resolver

- Round: R6
- Priority: P0
- Status: DONE
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

- [x] Precedence is deterministic (`runtime > task > project > default`) and
  selected version refs/content metadata are preserved in immutable
  `ResolvedPrompt` snapshots; override and duplicate-layer behavior is tested.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

Prompt assembly had no single layer precedence or snapshot owner.

After:

`workbench/application/prompt_resolver.py` owns provider-neutral layer
resolution and returns the immutable `ResolvedPrompt` domain snapshot.

Duplicate owner removed:

No model-call or provider-specific assembly was added; existing call-sites are
unchanged and remain compatible until a later migration card.

Independent Review:

PASS — 2026-09-11. DoD, architecture constraints, and PromptResolver ownership
passed; the 743-test verification result was confirmed. No R6-15 implementation
was included.

## Next Recommended Card

`R6-15`

Do not execute the next card in the same Agent run.
