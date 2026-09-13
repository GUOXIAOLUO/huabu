# CARD R7-08 — Codex Unexpected EOF Handling

- Round: R7
- Priority: P0
- Status: DONE — independent Review PASS; closed 2026-09-11
- Depends on: R7-07

## Goal

Fail all pending requests predictably when App Server exits unexpectedly.

## Before Owner

incomplete EOF behavior

## After Owner

explicit transport failure lifecycle

## In Scope

- Detect EOF.
- Fail pending futures.
- Normalize terminal error.
- Test recovery/restart path.

## Out of Scope

- No silent auto-substitution.

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

- [x] No pending request hangs after EOF.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

The stdout reader stopped silently at EOF, leaving pending request futures to
wait until timeout and providing no normalized terminal transport signal.

After:

`CodexBridge` detects unexpected stdout EOF, fails every pending request with
one explicit `CodexBridgeError`, emits a normalized transport-error event, and
leaves restart/recovery explicit to the caller.

Duplicate owner removed:

No auto-substitution, Agent tools, protocol DTO ownership, or second process
lifecycle was introduced; the existing bridge remains the sole transport owner.

## Next Recommended Card

`R7-09`

Do not execute the next card in the same Agent run.

## Implementation Evidence

Focused `tests/test_codex_bridge.py` coverage passes (5 tests), including
pending-request failure on unexpected EOF, normalized terminal event, and
explicit recover/restart. Existing stderr-drain and shutdown coverage remains
green. `./scripts/agent-verify.sh` passes with 786 tests, 152 Python AST files,
134 JavaScript files, 4 architecture guards, and clean diff check. R7-08
remains ACTIVE pending independent Review; R7-09 was not started.
