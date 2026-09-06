# CARD R7-12 — Codex Event Normalizer

- Round: R7
- Priority: P0
- Status: BACKLOG
- Depends on: R7-11

## Goal

Normalize Codex protocol events into Workbench-neutral runtime events.

## Before Owner

raw Codex events leaked upward

## After Owner

EventNormalizer

## In Scope

- Map lifecycle/progress/output/error events.
- Preserve raw diagnostic ref when needed.
- Test stable normalized schema.

## Out of Scope

- No Agent UI.

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

- [ ] Upper layers can observe events without Codex protocol knowledge.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R7-13`

Do not execute the next card in the same Agent run.
