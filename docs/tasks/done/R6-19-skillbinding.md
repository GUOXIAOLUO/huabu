# CARD R6-19 — SkillBinding

- Round: R6
- Priority: P0
- Status: DONE — independent Review PASS (2026-09-11)
- Depends on: R6-18

## Goal

Bind a Skill version and parameters to a generic Task Rich Node.

## Before Owner

Task skill placeholder

## After Owner

typed SkillBinding

## In Scope

- Define skill id/version/enabled/parameters/prompt override/execution profile ref.
- Persist on Task.
- Validate against SkillDefinition schema.

## Out of Scope

- No execution.

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

- [x] Task reload restores exact Skill version and parameters.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

Task Rich Node stored only an untyped Skill placeholder and had no typed
parameter validation boundary.

After:

`SkillBinding` owns the exact Skill id/version, enabled state, parameters,
optional Prompt override, and Execution Profile reference. It validates exact
SkillDefinition identity and the definition's parameter schema. Task Rich Node
persists the structured binding and restores its exact version and parameters.

Duplicate owner removed:

No execution, Skill discovery, Provider, or Package Runtime ownership was
added; Task Rich Node remains a presentation/state adapter.

## Next Recommended Card

`R6-20`

Do not execute the next card in the same Agent run.

## Independent Review

PASS — 2026-09-11. The exact-version SkillBinding contract, SkillDefinition
parameter validation, and Task reload persistence satisfy the card DoD without
adding execution, discovery, Provider, or Package Runtime ownership.
