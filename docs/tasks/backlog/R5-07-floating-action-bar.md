# CARD R5-07 — Floating Action Bar

- Round: R5
- Priority: P1
- Status: BACKLOG
- Depends on: R5-06

## Goal

Add contextual single/multi-selection actions without permanently bloating node cards.

## Before Owner

embedded/permanent node controls

## After Owner

generic FloatingActionBar

## In Scope

- Define action contribution contract.
- Support single- and multi-selection context.
- Wire generic open/copy/delete/group/create-collection placeholders where available.

## Out of Scope

- Do not implement Collection semantics before R6.
- Do not hardcode WholeHouse actions.

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

- [ ] Toolbar appears only contextually.
- [ ] Actions are registry/intent driven.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R5-08`

Do not execute the next card in the same Agent run.
