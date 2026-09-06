# CARD R16-07 — CAD Review Workspace

- Round: R16
- Priority: P1
- Status: BACKLOG
- Depends on: R16-06

## Goal

Add read/review-focused CAD workspace extension for WholeHouse.

## Before Owner

file-only CAD viewing

## After Owner

CAD Review workspace extension

## In Scope

- Display supported CAD preview/metadata/annotations where feasible.
- Capture review findings linked to AssetVersion.
- Integrate cad-review Skill.

## Out of Scope

- No full CAD authoring requirement.
- No direct GuiGui control.

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

- [ ] Review findings are version-specific and exportable.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R16-08`

Do not execute the next card in the same Agent run.
