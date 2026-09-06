# CARD R6-13 — Prompt Registry

- Round: R6
- Priority: P1
- Status: BACKLOG
- Depends on: R6-12

## Goal

Index and discover system/package/project/user prompts.

## Before Owner

scattered presets/templates

## After Owner

PromptRegistry

## In Scope

- Define registration/discovery metadata.
- Support package/system sources.
- Add basic search/list.

## Out of Scope

- No Skill Runtime yet.

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

- [ ] Prompts are discoverable without scanning UI code.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-14`

Do not execute the next card in the same Agent run.
