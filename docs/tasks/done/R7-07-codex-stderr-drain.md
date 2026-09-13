# CARD R7-07 — Codex stderr Drain

- Round: R7
- Priority: P0
- Status: DONE — independent Review PASS; closed 2026-09-11
- Depends on: R7-06

## Goal

Prevent Codex App Server stderr pipe buildup and preserve diagnostics.

## Before Owner

undrained stderr task

## After Owner

managed stderr drain

## In Scope

- Add lifecycle-managed drain.
- Bound/log diagnostics safely.
- Test shutdown.

## Out of Scope

- No Agent tools yet.

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

- [x] Long-running bridge cannot deadlock on stderr pipe.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

Codex App Server stderr was piped but had no managed reader, allowing sustained
diagnostics to fill the OS pipe and block the long-running bridge.

After:

`CodexBridge` starts a lifecycle-managed stderr drain with bounded in-memory
diagnostics and redaction of common secret values; shutdown cancels and awaits
both stdout and stderr tasks before process cleanup.

Duplicate owner removed:

No Agent tools, protocol/domain ownership, or alternate process lifecycle was
introduced; the existing bridge remains the sole stdio process owner.

## Next Recommended Card

`R7-08`

Do not execute the next card in the same Agent run.

## Implementation Evidence

Focused `tests/test_codex_bridge.py` coverage passes (4 tests), including a
20,000-line stderr fixture proving initialization proceeds without pipe
deadlock, diagnostics are bounded/redacted, and shutdown stops the child.
`./scripts/agent-verify.sh` passes with 785 tests, 152 Python AST files, 134
JavaScript files, 4 architecture guards, and clean diff check. R7-07 remains
ACTIVE pending independent Review; R7-08 was not started.
