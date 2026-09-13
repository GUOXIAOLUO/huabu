# CARD R6-20 — Skill Selector

- Round: R6
- Priority: P1
- Status: DONE — independent Review PASS (2026-09-11)
- Depends on: R6-19

## Goal

Let users choose Skills inside a generic Task Rich Node.

## Before Owner

manual/legacy task capability selection

## After Owner

Skill selector UI

## In Scope

- Support search/recent/recommended/installed packs.
- Bind selected skill through SkillBinding.
- Keep Task NodeKind unchanged.

## Out of Scope

- No industry-specific Task node types.

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

- [x] Changing Skill changes binding, not NodeKind.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

Task Skill selection was an untyped/manual placeholder with no shared
discovery view.

After:

`WorkbenchSkillSelector` consumes an injected discovery registry and exposes
search results, recent exact refs, recommended exact refs, and enabled Pack
views, and mounts that UI into the Task Rich Node content slot. Selecting a
registered Skill writes an exact `SkillBinding` to the existing Task Rich Node
while preserving its `task` kind.

Duplicate owner removed:

No second discovery registry, execution path, Provider branch, or industry
specific Task NodeKind was added.

## Next Recommended Card

`R6-21`

Do not execute the next card in the same Agent run.

## Independent Review

PASS — 2026-09-11. The selector is mounted through the Task Rich Node content
slot, supports the required discovery views, and changes only SkillBinding
while preserving the Task NodeKind. No prohibited runtime ownership was added.
