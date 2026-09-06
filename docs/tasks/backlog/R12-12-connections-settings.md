# CARD R12-12 — Connections Settings

- Round: R12
- Priority: P1
- Status: BACKLOG
- Depends on: R12-11

## Goal

Unify Codex/API/ComfyUI/RunningHub/MCP/Local Bridge settings.

## Before Owner

provider/integration scattered settings

## After Owner

Connections settings UI

## In Scope

- List connection categories/status.
- Create/edit/test supported connections.
- Keep credentials secure.

## Out of Scope

- No external app-specific workflow UI.

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

- [ ] External connectivity has one management surface.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R13-01`

Do not execute the next card in the same Agent run.
