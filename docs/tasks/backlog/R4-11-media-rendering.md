# CARD R4-11 — Image / Media Rendering Cutover

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-10

## Goal

Move normal image/video rendering and media state projection to the unified renderer path.

## Before Owner

page-created media DOM + shared helper

## After Owner

MediaRenderer under RenderRuntime

## In Scope

- Characterize image/video states.
- Move normal DOM lifecycle to MediaRenderer/RenderRuntime.
- Preserve legacy payload compatibility.
- Remove page ownership for migrated media lifecycle.

## Out of Scope

- Do not build R9 Asset runtime.

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

Add or run the smallest behavioral tests that prove this card's exact goal.
Do not rely only on source-string checks when runtime behavior can be tested.

## Regression

Run:

```bash
./scripts/agent-verify.sh
```

## Definition of Done

- [ ] Image/video load/error/select/reload paths pass.
- [ ] Page runtimes no longer create primary media DOM for migrated cases.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-12`

Do not execute the next card in the same Agent run.
