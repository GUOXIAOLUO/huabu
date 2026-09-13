# CARD R8-06 — Execution Input Preview

- Round: R8
- Priority: P1
- Status: DONE — independent Review PASS; archived 2026-09-12
- Depends on: R8-05

## Goal

Show users exactly what single/batch items will execute before starting.

## Before Owner

opaque run button

## After Owner

Execution Input Preview UI

## In Scope

- Render item count/roles/missing data/concurrency/start index.
- Allow safe policy edits before run.
- Block invalid items according to policy.

## Out of Scope

- No hidden mutation of input resources.

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

- [x] User can inspect concrete run items and missing inputs.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: task execution was represented only by opaque legacy run controls; no
shared preview owner existed.

After: `WorkbenchExecutionInputPreview` owns read-only projection display,
missing-input reporting, policy validation/editing, and the guarded start
intent. `TaskRichNode`/`NodeShell` provide only the mounting seam.

Duplicate owner removed: none; legacy executors and input resources remain
unchanged and no hidden resource mutation was introduced.

## Next Recommended Card

`R8-07`

Do not execute the next card in the same Agent run.
