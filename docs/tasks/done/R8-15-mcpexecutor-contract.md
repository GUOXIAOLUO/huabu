# CARD R8-15 — MCPExecutor Contract

- Round: R8
- Priority: P2
- Status: DONE — independent Review PASS (after CHANGES_REQUIRED remediation); archived 2026-09-12
- Depends on: R8-14 (DONE, independent Review PASS)

## Goal

Define a generic MCP execution adapter boundary without WholeHouse coupling.

## Before Owner

future/adhoc MCP calls

## After Owner

MCPExecutor adapter contract

## In Scope

- Define connection/capability/action invocation mapping.
- Normalize tool result/events/errors.
- Use Integration references where available later.

## Out of Scope

- No specific Kujiale/GuiGui MCP integration.

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

- [x] Generic contract is testable with a fake MCP server/client.

Proven by `tests/test_mcp_executor.py`, which drives the seam through an
in-process `FakeMCPServer` / `FakeMCPClient` pair that speaks MCP semantics
rather than acting as a bare transport stub: it holds a capability catalog,
enforces one action per capability kind, returns JSON-RPC error codes
(`-32601` capability not found, `-32602` action mismatch / invalid params), and
reports a failed capability call as `isError` inside an otherwise successful
response. The DoD-named test
`test_generic_contract_is_testable_with_a_fake_mcp_server` runs one
`tool:search` capability end-to-end through `MCPExecutor` against that fake
peer and asserts the normalized result, the event sequence, and the arguments
the server actually received. A source-scan test additionally pins that
`workbench/mcp` imports no provider SDK, no MCP client library and no
Canvas/legacy module.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: the product had no Workbench owner for MCP execution at all. Searching
`workbench/`, `main.py`, `static/js` and `static/*.html` for MCP found only two
non-owners: an allow-listed CLI sub-command name in the Codex / Antigravity
pass-through in `main.py` (`allowed = {..., "mcp", ...}`) and a
`<option value="mcp">` CLI-type selector in `static/api-settings.html`. Neither
executes an MCP capability, so an MCP call could only ever be an ad-hoc call
owned by whichever surface issued it — with no shared contract, no
normalization, and no executor route.

After: `workbench/mcp/` owns the Workbench side of one MCP capability
invocation. `MCPExecutor` resolves an explicit capability reference
(`tool:<name>`, `prompt:<name>` or `resource:<name>`; a missing or unknown kind
is rejected, and a resolver-returned capability with a different kind or name
is rejected rather than substituted) and the single deterministic
capability-kind to MCP-action mapping (`tool → call_tool`, `prompt →
get_prompt`, `resource → read_resource`; `MCPCall` refuses to carry an action
that disagrees with its kind). It maps Workbench input roles onto MCP action
arguments through the capability's binding table (unknown roles, missing
required roles, duplicate roles and duplicate arguments are bounded errors),
submits one `MCPCall` through the injected `MCPTransport` port, and normalizes
MCP results, progress and errors into typed
`ExecutionEvent`/`ExecutionOutput` values with deterministic output names —
including MCP's `isError`-inside-a-successful-response semantics, which
normalize to a failed execution, while MCP / JSON-RPC codes stay in event
metadata only.

The connection is resolved from the **execution configuration only**: an
explicit call setting first, then the execution profile's
`runtime_connection_ref`. This matches the reviewed ComfyUI and RunningHub
seams, and it keeps AGENTS.md §13 intact — catalog metadata never silently
overrides a configured connection. A capability declaration may still carry a
`connection_ref`, but it only *fills* a connection the configuration left
unspecified, and `PreparedExecution.metadata` records both the requested
connection (`requested_connection_ref`) and the resolution source
(`connection_source`: `request` or `capability`), so a fill-in is never
invisible. Integration references are carried as opaque values: the seam
forwards the reference it is given and never invents, resolves or replaces one,
leaving the Integration boundary that will own definitions and live connections
to a later round.

Duplicate owner removed: none — and none existed. No MCP execution owner, MCP
client library, MCP SDK import, transport implementation, credential or
vendor-specific integration was introduced or duplicated. `workbench/mcp`
imports only stdlib, pydantic and `workbench.domain.*`, and a source-scan test
pins that no provider SDK, no MCP client library and no Canvas/legacy module
can enter the seam. MCP transport (server process or HTTP/stdio setup, the
initialize handshake, JSON-RPC framing, capability listing, credential
resolution) is deliberately left to the injected adapter, so this card adds the
contract and the normalization seam, not a second MCP runtime.

## Developer Verification

- Focused: `33` tests covering strict capability reference rules (kind, name,
  mapping form), the single capability-kind to action mapping, the refusal to
  forge a mismatched action, duplicate role/argument rejection, credential
  scanning of the profile/config passthrough alongside a permitted
  tool-declared argument name, capability/action resolution, missing and
  unknown capability rejection, capability reference mismatch without
  substitution, connection resolution and provenance (explicit call setting
  outranks profile and capability; profile outranks a capability declaration;
  a capability declaration only fills an unspecified request and is recorded as
  `connection_source="capability"` with an empty
  `requested_connection_ref`), unknown and missing-required-role errors,
  declared `input_roles` mapping, prompt/resource capability actions, opaque
  Integration reference carry-over, accepted/progress/completed normalization
  with deterministic output names and values,
  `isError`-inside-a-successful-response normalization, failed-event
  normalization, partial output and stream-end completion, transport failure,
  timeout, invoke failure before any execution state, repeatable and explicit
  cancellation, cancellation of a waiting stream, unaccepted cancellation,
  prepare/start/handle boundaries, profile authority, the
  no-Canvas/no-provider-SDK/no-MCP-client source scan, `ExecutorRegistry`
  resolution of the `mcp` runtime route without substitution, generic Task
  execution plus active-handle cancellation through `ExecutionService`, and the
  DoD test against the fake MCP peer.
- Full: `./scripts/agent-verify.sh` PASS — `958` tests, `203` Python AST files,
  `135` JavaScript files, `4` architecture guards, and clean diff check.
- Developer Git Review: PASS; the only reviewed changes are the new
  `workbench/mcp/` package, the new `tests/test_mcp_executor.py` suite, and
  this card. No existing module was modified; `main.py` is untouched
  (mtime 2026-09-12 13:53) and no MCP execution owner was removed or rewired.
- Mutation verification: seven guarded behaviours were mutated and each was
  caught by the intended test — the capability reference mismatch guard
  (`test_capability_reference_mismatch_is_not_substituted`), the
  capability-kind/action agreement validator
  (`test_call_cannot_carry_an_action_that_disagrees_with_its_kind`), the
  `isError` normalization
  (`test_tool_error_inside_a_successful_response_becomes_failed`), the
  required-input-role guard
  (`test_unknown_role_and_missing_required_role_are_rejected`), the nested
  `config["parameters"]` projection lookup (both `ExecutionService` tests), the
  declared output name
  (`test_progress_and_result_events_are_normalized`), and the raw-text output
  value (three tests). The source file was restored byte-identical after each
  mutation. The DoD source-scan guard was separately probed with a temporary
  module under `workbench/mcp/` importing `mcp` and `legacy_definitions`; the
  scan failed as required and the probe was removed.

### Independent Review remediation (2026-09-12)

The first independent Review returned CHANGES_REQUIRED on one blocking finding:
the connection was resolved as config → **capability declaration** → profile, so
a capability declaration silently outranked the profile's
`runtime_connection_ref` while `PreparedExecution.metadata` recorded only the
actual value — an AGENTS.md §13 provenance gap, and inconsistent with the
reviewed ComfyUI/RunningHub seams (both config → profile). The reviewer also
showed the branch had zero test coverage: deleting it left all 30 tests green.

Remediation (option b, agreed with the Owner): `_resolve_connection` now reads
the execution configuration first (explicit call setting, then the profile) and
only lets a capability declaration fill a connection the configuration left
unspecified; `PreparedExecution.metadata` records `requested_connection_ref`
and `connection_source` (`request` or `capability`) alongside the actual
`connection_ref`. Three tests were added, and the three regression mutations
that previously slipped through are now caught: reverting to the old
capability-first order fails
`test_the_execution_profile_connection_outranks_a_capability_declaration` and
`test_an_explicit_call_connection_outranks_the_profile_and_the_capability`;
removing the capability fill-in fails
`test_a_capability_declared_connection_only_fills_an_unspecified_request`; and
blanking the requested-connection provenance fails three tests. Source restored
byte-identical after each (sha256 `8eefae52…`). Focused tests now pass (33);
the full gate passes with 958 tests.

### Independent Review — final verdict PASS (2026-09-12)

The re-review reproduced the focused suite (33 tests) and the full gate (958
tests, 203 Python AST files, 135 JavaScript files, 4 architecture guards, clean
diff check), then re-ran the original blocking scenario directly: with the
profile requesting `profile-configured-server` and the capability declaring
`capability-declared-server`, the call now carries
`profile-configured-server` and `PreparedExecution.metadata` records
`requested_connection_ref=profile-configured-server` and
`connection_source=request`. No silent override remains, so AGENTS.md §13 is
satisfied and the seam matches the reviewed ComfyUI/RunningHub resolution
order.

Five mutations were run independently and all were caught: reverting to
capability-first ordering (2 test failures), removing the capability fill-in
(1), blanking the requested-connection provenance (3), mislabelling a
capability fill-in as `connection_source="request"` (1), and dropping the
explicit call setting's precedence over the profile (2). The source file was
restored byte-identical after each (sha256 `8eefae52…`). The DoD source-scan
guard was probed again with a temporary module importing `mcp`; it failed as
required and the probe was removed. The review also confirmed that no stale
old-order text remains in the code, card or status document, that `main.py` is
untouched (mtime 2026-09-12 13:53) with its two `"mcp"` mentions intact, and
that `workbench/mcp` still imports only stdlib, pydantic and
`workbench.domain.*` — so no duplicate owner and no unauthorized migration were
introduced.

Non-blocking follow-up (recorded, not required for this card): in the
degenerate case where no connection is supplied by the call setting, the
profile or the capability, `connection_source` is `""`; changing that label to
`"request"` is not caught by any test. Both `connection_ref` and
`requested_connection_ref` are empty in that case, so it is a cosmetic label
rather than a §13 override, but a one-line assertion in
`test_integration_reference_is_carried_opaquely` would close it.

## Next Recommended Card

`R8-16`

Do not execute the next card in the same Agent run.
