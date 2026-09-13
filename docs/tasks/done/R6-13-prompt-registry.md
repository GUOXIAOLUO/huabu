# CARD R6-13 — Prompt Registry

- Round: R6
- Priority: P1
- Status: DONE
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

- [x] Prompts are discoverable without scanning UI code through `PromptRegistry`
  and `GET /api/v1/prompts?project_id=...`; search and source filtering are
  covered by behavioral tests.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

Prompt discovery was implicit in UI presets/templates; project Prompts had no
list/search boundary.

After:

`workbench/application/prompt_registry.py` owns explicit registration metadata
and discovery for system/package/user registrations plus authorized project
Prompts. The canonical Prompt API exposes the same boundary.

Duplicate owner removed:

No duplicate registry was added; UI preset migration remains deferred and
existing legacy behavior is preserved.

Independent Review:

PASS — 2026-09-11. DoD, architecture constraints, ownership evidence, and
the 740-test verification result passed. The user-source visibility boundary
was also verified; no R6-14 implementation was included.

## Next Recommended Card

`R6-14`

Do not execute the next card in the same Agent run.
