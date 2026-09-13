# CARD R6-15 — Prompt Resource UI

- Round: R6
- Priority: P1
- Status: DONE — independent Review PASS (2026-09-11)
- Depends on: R6-14

## Goal

Add Prompt management inside Resource Library structure.

## Before Owner

legacy prompt preset UI

## After Owner

generic Prompt resource UI

## In Scope

- List/search/view prompt versions.
- Create/update by new version.
- Expose package/source metadata.

## Out of Scope

- No top-level Prompt navigation.

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

- [x] Prompt lives under the existing Resources/提示词库 tab and does not
  create a new top-level category. The view uses canonical Prompt APIs for
  list/search, version viewing, creation, and new-version updates.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

The prompt tab rendered and mutated legacy prompt-library records directly.

After:

The existing Resources prompt tab renders canonical `PromptRegistry` entries,
loads immutable PromptVersions, and writes through `/api/v1/prompts` and its
version endpoint while displaying source metadata.

Duplicate owner removed:

The legacy prompt-library endpoints remain as a compatibility surface, but are
no longer the primary renderer or writer for the Resources Prompt tab.

## Next Recommended Card

`R6-16`

Do not execute the next card in the same Agent run.
