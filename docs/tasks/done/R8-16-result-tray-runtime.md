# CARD R8-16 — Result Tray Runtime

- Round: R8
- Priority: P0
- Status: DONE — independent Review PASS; archived 2026-09-12
- Depends on: R8-15 (DONE, independent Review PASS)

## Goal

Make execution outputs land in a non-Canvas result staging area by default.

## Before Owner

outputs auto/legacy materialization

## After Owner

Result Tray

## In Scope

- Define tray session/items linked to run/attempt outputs.
- Render generic result cards.
- Keep outputs non-materialized by default.

## Out of Scope

- No automatic Node creation.

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

- [x] Run outputs appear in tray without polluting Canvas.

Proven by `tests/test_result_tray_runtime.py`, which drives the seam in a vm
sandbox: one attempt's outputs become tray items carrying their
`run_id`/`attempt_id`/`output_name`/`ordinal` linkage and their normalized kind,
re-ingesting the same attempt is a no-op, generic card descriptors are produced
for text/image/video/file/json values with previews gated to media kinds, and
`mount` renders those cards into a host. Both halves of the DoD are pinned: the
outputs are staged (`materialized` stays `false` on the session and on every
item), and there is no path from the tray to Canvas — the controller exposes no
materialization entry point, a source scan rejects every node-creation and
graph-mutation marker, and the same scan rejects `fetch(`/`localStorage`/
`require(` so the seam owns no transport or client persistence. A second scan
pins the host integration itself: `task-rich-node.js` and `node-shell.js` mount
the tray and destroy it, without referencing any materialization dependency.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: execution results had no home other than the Canvas node that produced
them. `static/js/workbench/canvas/execution-host.js` declares
`writePromptResult` / `writeOutputText` / `setRunStatus` as the required Canvas
operations for a run, `classic-executor-runtime.js` calls
`executionHost.writeOutputText(node, text)` and
`executionHost.setRunStatus(node, …)` at every terminal branch, and
`canvas-app-execution.js` binds those straight onto node fields
(`writeOutputText: (node, text) => { if(node) node.outputText = text; }`).
A result therefore existed only as node state, with no non-Canvas staging area
where a user could look at it before deciding what to do with it.

After: `static/js/workbench/canvas/result-tray-runtime.js` owns a non-Canvas
staging area. `createSession` opens a tray session keyed by project/task/run;
`ingest` stages one attempt's outputs as items linked to their
`run_id`/`attempt_id`/`output_name`/`ordinal`, classifies each value into a
generic kind, and is idempotent for a replayed attempt; `cardFor`/`cards`
produce host-agnostic card descriptors (title, kind, subtitle, preview URL,
previewability, source linkage) and `mount` renders them into a host element.
Nothing is materialized: the session and every item carry
`materialized: false`, and the module exposes no promotion or node-creation
entry point at all. The tray is wired into the real Task node surface the same
way the R8-06 input preview was: `task-rich-node.js` exposes
`mountResultTray(host, options)` and `node-shell.js` mounts it (and destroys it)
when `resultTrayOptions` is supplied.

Duplicate owner removed: none — and none existed. This card adds the staging
owner that was missing; it does not remove or rewire the existing node write-back
path, because that path is still the only way a result reaches a Canvas node and
materialization is explicitly out of scope here (R8-22 owns result to Canvas
materialization, R8-21 owns result to Collection). No duplicate classifier or
node factory was introduced: the tray derives a kind from the output value the
executor already declared, so it re-implements neither `media-kind.js` nor the
executor-side output naming.

## Developer Verification

- Focused: `10` tests covering run/attempt-linked staging with non-materialized
  items and session summary, idempotent re-ingestion of an attempt (including a
  second attempt producing distinct item ids), generic card descriptors with
  declared kinds, preview gating and source linkage, host rendering plus the
  absence of a materialization entry point, snapshot isolation from tray state,
  the no-Canvas-mutation/no-transport source scan, `canvas.html` registration
  before the app bootstrap, `task-rich-node` mounting the tray and staging
  through it, the bounded error when the tray global is missing, and the
  node-shell mount/destroy wiring scan.
- Full: `./scripts/agent-verify.sh` PASS — `968` tests, `204` Python AST files,
  `136` JavaScript files, `4` architecture guards, and clean diff check.
- Developer Git Review: PASS; the reviewed changes are the new
  `result-tray-runtime.js` module, the new `tests/test_result_tray_runtime.py`
  suite, the `task-rich-node.js` / `node-shell.js` mount wiring, the
  `static/canvas.html` script registration, and this card plus the status
  document update. `main.py` is untouched and no backend module was modified.
- Mutation verification: five guarded behaviours were mutated and each was
  caught by the intended test — removing the ingest idempotency guard, flipping
  staged items to `materialized: true`, dropping the per-batch attempt linkage,
  making every card previewable, and stubbing out the node-shell
  `mountResultTray` call. The sources were restored byte-identical after each
  (`result-tray-runtime.js` sha256 `a298b6f7…`, `node-shell.js` sha256
  `df2ddc7a…`). The DoD source-scan guard was separately probed by injecting a
  `createNode` helper that calls `WorkbenchNodeCreationService` into the tray
  module; the scan failed as required and the probe was removed.
- Independent Review: PASS on 2026-09-12. The review re-ran the focused suite
  (`10` tests) and the full gate (`968` tests, `204` Python AST files, `136`
  JavaScript files, `4` architecture guards, clean diff check) and reproduced
  the developer's numbers exactly. It then mutation-tested seven further guarded
  behaviours, all of which were caught by the intended test and restored
  byte-identical (`result-tray-runtime.js` sha256 `a298b6f7…`, `node-shell.js`
  sha256 `df2ddc7a…` — matching the developer's recorded hashes): dropping the
  ingest idempotency guard (caught by the idempotency test), flipping a staged
  item to `materialized: true` (caught by three tests), making every card
  previewable (caught by the card-descriptor test), adding a `createNode` key to
  the controller surface (caught by the mount test plus the seam scan), dropping
  the node-shell tray destroy call (caught by the shell scan), and two DoD
  source-scan probes — injecting a node factory and injecting `fetch(` (both
  caught by `test_seam_has_no_canvas_mutation_or_transport_dependency`), which
  re-proves the guard is not toothless. An independent end-to-end probe fed the
  real executor output vocabulary through `ingest` (Codex/DirectModel raw text,
  RunningHub `{kind, url}`, ComfyUI `{kind, filename, subfolder, item_type}`,
  MCP `{kind, uri, mime_type}`): all five outputs staged with the right kinds, a
  replayed attempt was a no-op, the controller exposed exactly six keys with no
  materialization entry point, and the probe's Canvas-graph object was
  byte-identical afterwards — so both DoD halves hold independently of the
  card's own tests. The review also confirmed the `{name, value}` batch shape is
  exactly `ExecutionOutput`, that `kindOf`/`urlOf` read the vocabulary the
  executors actually emit, that `WorkbenchCanvasResultTray` has exactly one
  consumer (`task-rich-node.js` `mountResultTray`, gated on explicit
  `resultTrayOptions`), that no duplicate result-tray owner exists anywhere in
  the repository, and that R8-16 is the sole ACTIVE card with R8-17 disjoint and
  dependent on it. No Core or backend module is part of this card's change set.
  Three non-blocking notes are recorded: (a) no producer routes executor results
  into the tray yet, so the Goal's "by default" wiring is still owed by a later
  card even though the DoD itself is met; (b) ComfyUI outputs carrying only
  `filename`/`subfolder` stage but do not preview, which is precisely R8-17's
  declared "unavailable/failed output refs" scope; (c) the Developer
  Verification phrase "`main.py` is untouched" means "not part of this card's
  change set" — `main.py` does differ from HEAD by 56 insertions from earlier
  R6-12/R8-07/R8-08/R8-09 work. R8-16 remains the sole ACTIVE card; R8-17 was not
  started.
- Independent Review, second round: PASS on 2026-09-12, re-confirmed against the
  unchanged sources (`result-tray-runtime.js` sha256 `a298b6f7…`, `node-shell.js`
  sha256 `df2ddc7a…`), with the focused suite (`10` tests) and the full gate
  (`968` tests, `204` Python AST files, `136` JavaScript files, `4` architecture
  guards, clean diff check) reproduced again. Eight further mutations were run
  on targets neither the developer nor the first round had covered — session-id
  joining, object classification, the `urlOf` `uri` fallback, `escapeHtml`,
  `summaryOf`'s materialized flag, previewability without a URL, the per-name
  ordinal counter, and `clone` — of which seven were caught by the intended test
  and restored byte-identical. The eighth, replacing `escapeHtml` with a
  pass-through, was **not** caught: no test pins the escaping. A hostile-input
  probe (output names and URLs containing `<script>`, `<img … onerror=>`, quotes
  and ampersands) shows the implementation escapes correctly — no raw tag reaches
  the host and `onerror` survives only as inert escaped text — so this is a
  test-coverage gap rather than a defect, and it does not touch the DoD. A
  one-line test asserting that a hostile output name cannot break out of
  `data-result-item` would close it. mtime inspection also confirms no backend
  module is in this card's change set (`main.py` 13:53, `authorization.py` 09:53,
  `codex/bridge.py` and `node_creation.py` 2026-09-11 — all before this card's
  18:45–19:17 window), and a re-run of the DoD probe reproduced five staged
  items with correct kinds, a no-op replay, exactly six controller keys with no
  materialization entry point, and a byte-identical Canvas graph.

## Next Recommended Card

`R8-17`

Do not execute the next card in the same Agent run.
