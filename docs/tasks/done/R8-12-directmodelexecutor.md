# CARD R8-12 — DirectModelExecutor

- Round: R8
- Priority: P1
- Status: DONE — independent Review PASS; archived 2026-09-12
- Depends on: R8-11

## Goal

Add a generic direct model/API execution route if supported by current product needs.

## Before Owner

provider-specific direct calls

## After Owner

DirectModelExecutor

## In Scope

- Adapt generic executor contract.
- Use ProviderConnection/ModelAvailability.
- Normalize outputs/events.

## Out of Scope

- Skip implementation if no valid direct route exists; document decision instead.

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

- [x] No direct provider SDK leaks into domain.

A generic direct route exists: `ModelAvailability.route_type` already carries an
explicit `provider` route kind (R7-04), so the direct model/API route is a real
product route rather than a speculative one. `DirectModelExecutor` implements it
behind the R8-01 Executor contract; provider transport stays behind the injected
`DirectModelTransport` port and never reaches domain or application code.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: no Workbench boundary owned a direct model/API execution. The only
executor implementation was `CodexHarnessExecutor`, which owns the `runtime`
route kind; a `provider` (direct API) route had no executor, so any direct call
would have to live as provider-specific call code outside the execution
runtime.

After: `workbench/direct_model/` owns the generic direct route.
`DirectModelExecutor` resolves its route from the separate `ModelAvailability`
(route kind, enabled flag, status, capabilities) and `ProviderConnection`
(provider id, sanitized config, opaque `credential_ref`) records, submits one
`DirectModelCall` through the injected `DirectModelTransport` port, maps
provider-shaped `DirectModelRawEvent` values into typed `ExecutionEvent`/
`ExecutionOutput` values, and enforces the configured timeout/cancel budget.
Runtime routes are rejected instead of being silently rerouted.

Duplicate owner removed: none. The transport adapter keeps endpoint selection,
wire format, authentication and credential resolution; `ModelAvailability`,
`ProviderConnection` and `ExecutionProfile` keep their own identity; the
Codex bridge keeps protocol transport and `runtime` routes. No provider SDK,
HTTP client, or secret material is imported by `workbench/domain`,
`workbench/application`, or `workbench/direct_model` (pinned by a focused
source-scan test).

## Developer Verification

- Focused: `22` tests covering provider-route resolution through
  ModelAvailability/ProviderConnection, runtime-route rejection, unknown/disabled
  route rejection, event and output normalization, named outputs, stream-end
  completion, failed/transport-failure/timeout results, submit failure,
  repeatable and explicit cancellation, cancellation of a waiting stream,
  unaccepted cancellation, prepare/start/handle boundaries, profile authority,
  credential rejection at the call boundary, ExecutorRegistry resolution without
  route substitution, the no-provider-SDK source scan, and generic Task
  execution plus active-handle cancellation through `ExecutionService`.
- Full: `./scripts/agent-verify.sh` PASS — `878` tests, `194` Python AST files,
  `135` JavaScript files, `4` architecture guards, and clean diff check.
- Developer Git Review: PASS; the only reviewed changes are the new
  `workbench/direct_model/` package, the new
  `tests/test_direct_model_executor.py` suite, and this card plus the status
  document update. No existing module was modified and no executor wiring,
  model selection, or fallback path was added.
- Independent Review: PASS on 2026-09-12. The review re-ran the focused suite
  (22 tests) and the full gate (878 tests, 194 Python AST files, 135 JavaScript
  files, 4 architecture guards, clean diff check), confirmed the new package
  imports only stdlib, pydantic and `workbench.domain.*`, and mutation-tested
  three guarded behaviours (provider-route rejection, named output
  normalization, timeout-is-failed) — each mutation was caught, and the source
  file was restored byte-identical. No duplicate owner existed to remove, and
  no existing module was touched. R8-12 is archived in `docs/tasks/done/`;
  R8-13 is now the sole ACTIVE task and was not started.

## Next Recommended Card

`R8-13`

Do not execute the next card in the same Agent run.
