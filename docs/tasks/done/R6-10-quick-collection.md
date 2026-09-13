# CARD R6-10 — Quick Collection

- Round: R6
- Priority: P1
- Status: DONE — independent Review PASS; archived 2026-09-11
- Depends on: R6-09

## Goal

Create a Collection quickly from selected resources/nodes.

## Before Owner

manual/ad hoc grouping

## After Owner

Quick Collection action

## In Scope

- Add multi-select action contribution.
- Create collection from eligible references.
- Prompt for title minimally and preserve order.

## Out of Scope

- Do not conflate with Group.

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

- [x] Selected resources can become a Collection without changing visual Group semantics.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

The floating multi-select action bar offered Group but had no Collection creation path.

After:

Quick Collection filters eligible asset, artifact, and Collection references in selection order,
prompts once for a title, persists the Collection through the canonical API, and creates its
Canvas representation through `NodeCreationService`.

Duplicate owner removed:

None; Group remains responsible for visual organization and Quick Collection owns only the
resource aggregate creation flow.

## Independent Review

PASS — reviewed against `AGENTS.md`, the R6-10 goal and DoD, the canonical
Collection and NodeCreationService boundaries, typed reference/order behavior,
Group separation, focused tests, full verification, and the complete worktree
diff relative to `HEAD` `1a78ca50d15e7e906514835bd52e7b93205bd8b2`.

## Next Recommended Card

`R6-11`

Do not execute the next card in the same Agent run.
