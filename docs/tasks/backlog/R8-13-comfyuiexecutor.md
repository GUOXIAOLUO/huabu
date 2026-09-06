# CARD R8-13 — ComfyUIExecutor

- Round: R8
- Priority: P1
- Status: BACKLOG
- Depends on: R8-12

## Goal

Wrap ComfyUI workflows behind the generic Executor contract.

## Before Owner

ComfyUI-shaped Canvas/execution behavior

## After Owner

ComfyUIExecutor

## In Scope

- Define workflow/profile references.
- Map input roles to workflow inputs.
- Normalize progress/output.

## Out of Scope

- Do not recreate ComfyUI graph in main Canvas.

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

- [ ] Task can execute a ComfyUI-backed Skill without provider-shaped Canvas node dependency.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-14`

Do not execute the next card in the same Agent run.
