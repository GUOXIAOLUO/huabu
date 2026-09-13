# CARD R7-10 — Typed Codex Protocol Messages

- Round: R7
- Priority: P1
- Status: DONE — independent Review PASS 2026-09-11
- Depends on: R7-09

## Goal

Move raw JSON handling behind typed compatibility/message models.

## Before Owner

raw dict dispatch

## After Owner

typed protocol boundary

## In Scope

- Define request/response/event models for used protocol subset.
- Validate incoming/outgoing envelopes.
- Keep protocol-version compatibility isolated.

## Out of Scope

- No Workbench business types inside raw protocol layer.

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

- [x] Bridge callers no longer depend on arbitrary raw dict shapes.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: `CodexBridge` built and dispatched arbitrary JSON dictionaries directly
for requests, responses, notifications, and protocol-version handling.

After: `workbench/codex/protocol.py` owns typed request/response/notification/
server-request envelopes, used operation parameter/result models, JSON parsing,
and isolated protocol-version compatibility. `CodexBridge` sends and receives
only validated protocol models and exposes typed operation results.

Duplicate owner removed: raw envelope dispatch and operation result-shape
ownership were removed from `workbench/codex/bridge.py`; no Workbench business
types were added to the protocol layer.

Focused evidence: bridge integration tests cover typed initialize/thread/turn/
model/config results and typed approval responses; protocol tests cover wire
aliases, invalid envelopes, response outcome validation, and unsupported
protocol versions. Focused tests pass (8); full verification passes with 789
tests, 154 Python AST files, 134 JavaScript files, 4 architecture guards, and
clean diff check.

## Next Recommended Card

`R7-11`

Do not execute the next card in the same Agent run.
