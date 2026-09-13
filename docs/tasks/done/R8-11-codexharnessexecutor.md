# CARD R8-11 — CodexHarnessExecutor

- Round: R8
- Priority: P0
- Status: DONE — independent Review PASS; archived 2026-09-12
- Depends on: R8-10

## Goal

Promote hardened Codex bridge into a formal Executor implementation.

## Before Owner

Codex compatibility bridge

## After Owner

CodexHarnessExecutor

## In Scope

- Adapt Executor contract to Codex bridge.
- Map events via normalizer.
- Respect profile/sandbox/timeout/cancel.

## Out of Scope

- No Agent orchestration tools yet.

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

- [x] Generic Task can run via CodexHarnessExecutor through ExecutionService.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: `CodexBridge` was the only hardened Codex runtime boundary; no formal
provider-neutral Executor implementation owned a Codex turn.

After: `CodexHarnessExecutor` adapts the existing bridge to the generic
Executor lifecycle. `ExecutionService.execute` creates the durable Attempt,
streams normalized events, persists them through `ExecutionEventService`, and
normalizes the durable Run result.

Duplicate owner removed: none; the Codex bridge retains protocol transport,
authentication, Harness sandbox policy, and Agent loop ownership. The new
Executor owns only Workbench lifecycle translation, timeout/cancel boundaries,
and typed outputs.

## Developer Verification

- Focused: `29` tests covering Executor lifecycle, profile authority,
  read-only sandbox, event mapping, timeout interruption, repeatable cancel,
  active-handle cancellation through `ExecutionService`, and durable Run/
  Attempt/Event state.
- Full: `./scripts/agent-verify.sh` PASS — `856` tests, `191` Python AST
  files, `135` JavaScript files, `4` architecture guards, and clean diff
  check.
- Developer Git Review: PASS after repairing timeout interruption, active
  cancellation handle reuse, normalized nested item text coverage, and the
  atomic timeout-interrupt cancellation race handling.
- Independent Review: PASS; archived after review on 2026-09-12. R8-12 is
  activated as the sole next dependency-satisfied task; implementation was not
  started in this run.

## Next Recommended Card

`R8-12`

Do not execute the next card in the same Agent run.
