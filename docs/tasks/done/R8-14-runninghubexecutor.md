# CARD R8-14 — RunningHubExecutor

- Round: R8
- Priority: P2
- Status: DONE — independent Review PASS; archived 2026-09-12
- Depends on: R8-13 (DONE, independent Review PASS)

## Goal

Wrap retained RunningHub execution behind the generic Executor contract.

## Before Owner

legacy RunningHub card/runtime

## After Owner

RunningHubExecutor

## In Scope

- Migrate retained route.
- Normalize events/results.
- Remove legacy execution ownership where possible.

## Out of Scope

- No provider-specific Core NodeKind.

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

- [x] RunningHub works as executor route, not Canvas runtime owner.

Proven by `tests/test_runninghub_executor.py`: `RunningHubExecutor` satisfies the
generic `Executor` protocol, `ExecutorRegistry` resolves it for the `runninghub`
runtime route (and refuses to hand it another route), and a generic
`ExecutionRun` executes end-to-end through `ExecutionService` — persisting
`started → progress → progress → completed` and normalized outputs — while
touching no Canvas node, Canvas repository, or provider-shaped Canvas payload.
A source-scan test pins that `workbench/runninghub` imports neither
Canvas/legacy modules nor any provider SDK.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: RunningHub owned its own Canvas runtime. `/api/runninghub/submit`,
`/api/runninghub/workflow-submit` and `/api/runninghub/query` carried the whole
task lifecycle inside request handlers — submit, poll, interpret status codes
(0/804/813/805), extract outputs — next to provider configuration, wallet keys
and the workflow catalog. A Workbench Task had no way to run through that
behavior without the Canvas-shaped RunningHub card and runtime.

After: `workbench/runninghub/` owns the Workbench side of one RunningHub run.
`RunningHubExecutor` resolves an explicit versioned retained route
(`ai_app:route_id@version` or `workflow:route_id@version`; an implicit latest,
an unknown kind, and a resolver-returned other version are all rejected rather
than substituted) plus the configured `ExecutionProfile`, maps Workbench input
roles onto RunningHub `nodeInfoList` fields through the route's binding table
(unknown roles and missing required roles are bounded errors), submits one
`RunningHubCall` through the injected `RunningHubTransport` port, and normalizes
RunningHub task status and outputs into typed `ExecutionEvent`/`ExecutionOutput`
values with output kinds and deterministic names. Endpoint URLs, API key/wallet
resolution, HTTP polling, status-code semantics and output extraction stay with
the transport adapter.

Duplicate owner removed: none yet, and none added. The legacy RunningHub HTTP
endpoints are still called by the Canvas UI (7 call sites in
`static/js/workbench/canvas/classic-executor-runtime.js` and
`static/js/api-settings.js`), so deleting or rewiring them is not "possible"
under this card's compatibility rule — they now survive only as bounded
compatibility adapters for that UI, while Workbench task execution has moved to
the executor route. The seam deliberately does not re-implement the legacy
status-code table or output extractor (the transport declares normalized kinds
and output items), so no second RunningHub execution owner was introduced.
Follow-up: migrate those UI call sites onto the execution API, then retire the
legacy endpoints in their own card.

## Developer Verification

- Focused: `23` tests covering route/profile reference resolution, strict route
  reference rules (explicit version, known kind), version-mismatch and unknown
  route rejection, role to `nodeInfoList` field mapping (including declared
  `input_roles`), unknown and missing-required-role errors, queued/running/
  completed normalization with provider codes, failed normalization, partial
  outputs and stream-end completion, transport failure, timeout, submit
  failure, repeatable and explicit cancellation, cancellation of a waiting
  stream, unaccepted cancellation, prepare/start/handle boundaries, profile
  authority, duplicate-role and credential-parameter rejection, the
  no-Canvas/no-provider-SDK source scan, `ExecutorRegistry` resolution of the
  `runninghub` runtime route without substitution, and generic Task execution
  plus active-handle cancellation through `ExecutionService`.
- Full: `./scripts/agent-verify.sh` PASS — `925` tests, `200` Python AST files,
  `135` JavaScript files, `4` architecture guards, and clean diff check.
- Developer Git Review: PASS; the only reviewed changes are the new
  `workbench/runninghub/` package, the new `tests/test_runninghub_executor.py`
  suite, and this card plus the status document update. No existing module was
  modified; the legacy RunningHub HTTP endpoints and their helpers are
  untouched.
- Independent Review: PASS on 2026-09-12. The review re-ran the focused suite
  (23 tests) and the full gate (925 tests, 200 Python AST files, 135 JavaScript
  files, 4 architecture guards, clean diff check) and independently
  mutation-tested two further guarded behaviours the developer had not covered:
  the `ExecutionProfile` executor-identity check (removing it lets a
  non-`runninghub` profile be accepted — an architecture §13 silent-substitution
  hole) and the required-input-role check; each mutation was caught by
  `test_profile_is_the_timeout_and_executor_identity_authority` and
  `test_unknown_role_and_missing_required_role_are_rejected` respectively, and
  the source file was restored byte-identical (sha256 `d4ad2ce4…`). The review
  also probed the DoD source-scan guard itself by temporarily adding a module
  under `workbench/runninghub/` that imports `legacy_definitions` and
  `requests`; `test_seam_has_no_canvas_or_provider_sdk_dependency` failed as
  required, proving the guard is not toothless, and the probe was removed. It
  re-grepped the 7 legacy RunningHub UI call sites, confirmed `main.py` is
  untouched (mtime 2026-09-12 13:53, before this card's work) with
  `/api/runninghub/submit` and `/api/runninghub/query` intact, and confirmed
  structurally that `workbench/runninghub` imports only `asyncio`,
  `dataclasses`, `pydantic`, `typing` and `workbench.domain.*` — so no
  unauthorized migration and no duplicate RunningHub execution owner were
  introduced. R8-14 is archived in `docs/tasks/done/`; R8-15 is now the sole
  ACTIVE task and was not started.

## Next Recommended Card

`R8-15`

Do not execute the next card in the same Agent run.
