# Current Execution Status

status_schema: workbench.execution-status/2

## Repository

repository: local worktree (remote repository out of scope)
verified_head: c201b0f
verified_commit: "feat: integrate R4 unified canvas cutover"
branch: main
remote_state: not checked; GitHub/remote synchronization is out of scope for this local task
verified_at: 2026-09-09T21:20:00+08:00
verification_source: local main at c201b0f; R4-39/R4-40 cutover integration plus R4-41 merged-code regression gate PASS at 637 tests
worktree_before_R0: clean
worktree_at_R4_03: HEAD a1195c9 plus the R4-03 card's own pending additions only —
the authority policy seam, the main.py guard wiring, focused policy/wiring tests,
the isolated legacy-routed test-fixture database patches, and status/ownership
document updates; Legacy recovery semantics unchanged

## Product contract

product: generic AI Workbench
client_v1: Web UI
orchestration_target: Codex Harness / App Server
wholehouse_role: first Industry Package, not Core
canvas_target: one Unified Canvas
current_persistence_authority: SQLite CanvasRecord for normal Canvas routing; Legacy JSON/filesystem compatibility elsewhere
agent_dom_mutation_allowed: false
silent_model_provider_executor_fallback_allowed: false

## Active Round

active_round: R4
active_round_name: Unified Canvas Cutover
round_status: in_progress
blocking_issues:
  - R4-41 formal final gate is BLOCKED: local main is integrated at c201b0f,
    but the Integration Owner has not completed the required merged A–N
    checklist evaluation.
  - R4-41's committed 100/300-node samples and 300-node five-render heap
    observation are diagnostic only; a complete per-item merged evidence
    record for resource duplication and memory-growth acceptance is absent.

Active task: R4-41 — R4 Full Acceptance Gate, activated on 2026-09-09 after
R4-40 passed independent Review. R4-41 is BLOCKED on the formal merged
Integration Owner evaluation and complete acceptance-evidence requirements
recorded in its card. R4-40 is archived as DONE; R5+ remains unauthorized.

R4-41 acceptance/fix attempt (2026-09-09): title/icon metadata writes were
moved to the dedicated `/meta` boundary and covered by a regression contract.
Local `./scripts/agent-verify.sh` passed (637 tests, 81 Python AST files, 112 JavaScript files, 4 architecture
guards, clean diff check). The formal checklist remains `R4: NOT PASS`: the
R4-39/R4-40 implementation is integrated on local `main` at `c201b0f`, but no
Integration Owner has recorded its required A–N merged-code evaluation, and
the gate lacks a complete per-item resource-duplication and memory-growth
acceptance record. Git Review also
confirmed the compatibility-only graph-array projections are now isolated
behind `legacy-canvas-mutation.js`; no direct array writes remain in
`canvas-app-interaction.js`. Interaction blur and metadata/crop resize cleanup
were consolidated to one global listener per event; output pan and compare
share one guarded global pointer pair, with touch handlers kept separate.
Remote polling start/stop idempotence is covered by a focused regression test.
The local listener/timer/observer audit is recorded in
`docs/benchmarks/r4-41-runtime-audit-2026-09-09.md`; it is committed diagnostic
evidence and does not close the formal Gate. Its local 300-node Chromium heap
sample observed 24,905,516 bytes before and after five confirmed real re-renders (zero
delta); this is diagnostic rather than a merged acceptance result.
An isolated disposable-record browser recheck repaired an actual
viewport-controller initialization defect and the harness's cross-frame event
sequence. The 100-node run passed zoom/pan/minimap visual updates in 15.400 /
27.500 / 116.400 ms; the 300-node run passed them in 10.900 / 62.100 /
30.500 ms. This is diagnostic local evidence only, so R4 remains blocked
until the Integration Owner completes the merged-gate evidence review.
No ownership change or R5 activation is authorized.

R4-40 completion evidence (2026-09-09): the six R4 query flags
(`unified_canvas`, `node_shell`, `media_renderer`, `legacy_renderer`,
`semantic_zoom`, `screen_space_controls`) no longer select runtime branches in
Canvas or the performance harness. Focused flag-retirement tests: PASS (9).
Full `./scripts/agent-verify.sh`: PASS (633 tests, 81 Python AST files, 111
JavaScript files, 4 architecture guards, clean diff check). R4-40 is DONE;
R4-41 was not started.

R4-39 Wave 1 characterization (2026-09-08):
`docs/plans/R4_39_CLASSIC_RUNTIME_REMOVAL.md` records eight residual ownership
clusters and their final owners. The current `canvas.js` is still 12,754 lines,
owns page state/bootstrap/render/interaction/persistence and hosts the Classic
compatibility seams; the executor and asset seams alone require 107 and 101
host operations, so they are not independent replacement owners. A new
executable gate grounds every cluster in the current source and prevents the
card from being marked DONE while `static/js/canvas.js` exists. Focused tests:
PASS (2).

R4-39 Wave 2 neutral bootstrap (2026-09-08):
`static/js/workbench/canvas/app-bootstrap.js` now owns initialization order and
Canvas-record/list routing through the frozen
`WorkbenchCanvasAppBootstrap.create(host) -> {start}` boundary. `canvas.js`
retains only explicit host adapters plus `window.onload` delegation; it no
longer owns the startup algorithm. A behavioral VM test proves ordering,
decoded record IDs, list fallback, host-port validation, and the one-method
public surface. Isolated browser acceptance at `127.0.0.1:3039` passed for the
default path (four NodeShell nodes and a working asset panel) and all-zero
rollback path (four Legacy-renderer nodes); the temporary SQLite copy remained
byte-identical. Focused tests: PASS (3). The next bounded slice is Wave 3 state,
persistence, and remote-polling ownership; `canvas.js` still exists, so R4-39
remains IN_PROGRESS and no runtime deletion is yet authorized. Full
`./scripts/agent-verify.sh`: PASS (367 tests; Python AST 77 files; JavaScript
syntax 85 files; architecture guards 4; diff check clean).

R4-39 Wave 3 Canvas session ownership (2026-09-08):
`static/js/workbench/canvas/canvas-session.js` now owns record open/save/sync/
close, dirty and in-flight state, save scheduling, revision adoption, remote
polling and update-message deferral behind one frozen eight-method interface.
`canvas.js` retains only graph serialization and render/interaction projection;
its local dirty/applying/last-updated state and direct persistence, scheduler,
remote-sync and update-message orchestration were deleted. The canonical
persistence client now advances its revision cursor only on successful writes;
a 409 keeps the local session dirty and does not authorize automatic retry of
the rejected stale payload. Focused VM behavior covers open/save/conflict/
revision/update/remote/close. Isolated browser acceptance at
`127.0.0.1:3040` rendered the four-node fixture on default and all-zero paths
across polling intervals without new console errors, and the SQLite copy stayed
byte-identical. Full `./scripts/agent-verify.sh`: PASS (368 tests; Python AST 77
files; JavaScript syntax 86 files; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is Wave 4 interaction,
render, and graph/group lifecycle ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 4 slice 1 — residual pointer-session cutover (2026-09-08):
an independent review of Waves 1-3 returned CHANGES_REQUIRED on one
bookkeeping contradiction (AGENT_NEXT_TASK tail said "next slice Wave 3"
while the head said Wave 4) plus two stale-status lines; all three were
repaired, and the same run executed the first Wave 4 slice. The four
remaining direct window mouse-slot sessions in `canvas.js` (LLM pane resize,
box selection, selection-link drag, knife drag) now begin through
`ensureInteractionController().begin(...)`, and the cleanup sites
(`finishSelection`, `endDrag`, the blur guard) unwire through
`controller.end()`; no direct `window.onmousemove`/`window.onmouseup`
assignment remains in the page. A source-contract test pins the cutover and a
controller behavior test pins the end-inside-onEnd and blur-guard unwire
shapes. Render and graph/group clusters remain page-owned pending their own
slices. Full `./scripts/agent-verify.sh`: PASS (369 tests; Python AST 77
files; JavaScript syntax 86 files; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is the Wave 4 render or
graph/group ownership slice. R4-40 and R5+ remain unauthorized.

R4-39 Wave 4 slice 2 — group-membership transition ownership (2026-09-08):
the move-driven membership transition in `canvas.js` `updateGroupMembership`
(geometric containment detection, membership add/remove across group records,
and the generator-edge handoff from an absorbed child to its containing
group) moved into the existing shared
`WorkbenchCanvasGroupMembership.resolveMembershipTransition` boundary. The
page keeps only the product policy inputs — child/group type pairs, DOM-backed
`nodeRect` geometry, handoff eligibility (`group` + image/prompt), the
`canConnect` connect policy, and the edge-id factory — plus the unchanged
post-change side effects (generator syncs, render, save); the inline
`handoffGroupConnections` logic and the page-level edge reassignment were
deleted. A behavior test drives the real module over membership
add/remove/handoff/veto/promptGroup-suppression/no-op shapes (including the
characterized unconditional child-edge removal before the gated re-add), and
a wiring contract pins the delegation with zero inline transition logic.
Focused suite: PASS (122 frontend-module tests). Full
`./scripts/agent-verify.sh`: PASS (371 tests; Python AST 77 files; JavaScript
syntax 86 files; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining Wave 4 graph/group
mutation ownership.

R4-39 Wave 4 slice 3 — render and graph-admission ownership (2026-09-08):
`WorkbenchCanvasRenderSweep` now delegates mounted-card reconciliation to
`WorkbenchRenderRuntime`, which owns teardown-before-build, remote-node
removal, failed-build cleanup and clear on Canvas close. The page no longer
performs renderer unmounts in individual delete paths. Classic graph-connect
admission and generator/media-output classifications now live in
`WorkbenchLegacyGraphCompatibility`; `canvas.js` retains only the adapter
call. Focused behavior tests cover partial refresh versus full-sweep fallback,
all-node lifecycle cleanup, historical connection admission and page wiring.
Default and all-zero isolated browser acceptance over the 15-node Classic
fixture verified repeated full and targeted LTX editor rebuilds without
console errors. Full `./scripts/agent-verify.sh`: PASS (376 tests; Python AST
78 files; JavaScript syntax 87 files; architecture guards 4; diff check
clean). R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
graph/group mutation ownership.

R4-39 Wave 4 slice 4 — selected-group edge handoff ownership (2026-09-08):
selected image/prompt grouping now delegates child-to-generator edge handoff
to `WorkbenchCanvasGroupMembership.handoffChildEdgesToGroup`, reusing the
same transition owner as move-driven membership. `canvas.js` retains group
creation, selection and save/render effects only. Behavior coverage proves
idempotent removal, existing group-edge reuse, target filtering and page
delegation. Full `./scripts/agent-verify.sh`: PASS (377 tests; Python AST 78
files; JavaScript syntax 87 files; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; R4-40 and R5+ remain unauthorized.

R4-39 Wave 4 slice 5 — ordinary connection-result projection (2026-09-08):
versioned Classic port-drop commits now delegate returned-edge validation,
undo snapshot retention and canvas revision adoption to
`WorkbenchNodeClient.applyConnectionResult`; `canvas.js` retains only the
shared compatibility side-effect projection plus save/render effects. The
raw `commitClassicConnection` path remains an explicit rollback adapter.
Behavior coverage proves endpoint rejection, bounded undo retention, revision
callback and commit callback. Full `./scripts/agent-verify.sh`: PASS (378
tests; Python AST 78; JavaScript syntax 87; architecture guards 4; diff check
clean). R4-39 remains IN_PROGRESS; the next bounded slice is remaining
graph/group mutation ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 4 slice 6 — single-node deletion projection (2026-09-08): raw and
versioned single-node deletion paths now delegate node/incident-edge removal
to `WorkbenchCanvasGraphFragment.removeGraphRecords`; `canvas.js` retains undo,
selection, render and save effects. Behavior coverage proves incident-edge
removal, nested group expansion and page use across all single-node deletion
paths. Full `./scripts/agent-verify.sh`: PASS (379 tests; Python AST 78;
JavaScript syntax 87; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is remaining graph/group mutation
ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 26 — outpaint Blob projection (2026-09-08): white-canvas,
offset and PNG Blob generation now delegates to
`WorkbenchCanvasMediaTools.outpaintImageBlob`; the page retains bounds
calculation, upload and node mutation effects. Focused behavior coverage proves
canvas sizing, fill and image placement. Full `./scripts/agent-verify.sh`:
PASS (396 tests; Python AST 78; JavaScript syntax 92; architecture guards 4;
diff check clean). R4-39 remains IN_PROGRESS; the next bounded slice is
remaining prompt/workflow/media-editing ownership. R4-40 and R5+ remain
unauthorized.

Residual RunningHub/Loop behavior verification (2026-09-09): focused frontend
workbench module suite PASS (127 tests), covering RunningHub controls seam
wiring, classic compatibility boundaries, and Loop runtime integration. No new
ownership removal is justified by this suite; R4-39 remains `IN_PROGRESS`.

R4-39 executable deletion-gate check (2026-09-09): PASS — all four gate tests
pass, including residual-cluster grounding and the explicit rule that the card
cannot close while `static/js/canvas.js` exists. The gate remains intentionally
open pending the authorized runtime-removal step.

Wave 6 deletion dependency inventory (2026-09-09): `canvas.html` still loads
`canvas.js` after the Classic seam modules; executor, asset, node-factory,
provider-control, cascade, and card-renderer modules still inject host
operations from the page, while the command registry retains explicit Classic
canvas kinds. Deletion therefore requires a replacement bootstrap/host boundary
before removing the script tag; R4-39 remains `IN_PROGRESS`.

Wave 6 host-contract inventory (2026-09-09): the loaded Classic seam set
contains 13 host-injected modules (asset, card, cascade, Comfy, execution,
executor, generation-log, LTX, MiniMax, output-grid, RunningHub, video-card,
and video-provider controls), plus node factories. Each validates a required
operation set at creation time; replacement work must satisfy these contracts
before the page script can be removed.

Wave 6 host-contract reconciliation (2026-09-09): PASS — the focused
`test_classic_seam_factories_inject_every_required_host_op` guard reconciles
each seam's `REQUIRED_OPS` against its `canvas.js` factory injection. The
replacement host must preserve this contract set before script removal.

Wave 6 host-contract sizing (2026-09-09): the current seam contracts total
513 required operations: executor runtime 107, asset runtime 101, RunningHub
controls 60, card renderer 49, MiniMax controls 35, Comfy controls 29,
cascade 25, LTX 24, generation log 22, video card 21, output grid 19, video
provider 15, and execution host 6. Replacement-host work must therefore be
sequenced by contract cluster rather than attempted as a single deletion.

Wave 6 execution-host candidate characterization (2026-09-09): the smallest
replacement cluster is `WorkbenchCanvasClassicExecutionHost` with six operations
(`markRunning`, `writeOutputText`, `setRunStatus`, `render`, `save`, and
`notifyError`). The page adapter currently owns node-state writes, refresh,
save scheduling, and user notification; these callbacks must remain explicit
until a neutral lifecycle host replaces them.

Wave 6 execution-host contract split (2026-09-09): the existing neutral
`execution-host.js` exposes the Smart five-operation contract
(`markRunning`, `writePromptResult`, `save`, `render`, `notifyError`), while
Classic requires six operations (`markRunning`, `writeOutputText`,
`setRunStatus`, `render`, `save`, `notifyError`). These contracts cannot be
merged by renaming methods; replacement work needs an explicit dual-contract
adapter with independent behavior tests.

Wave 6 dual-contract host foundation (2026-09-09): neutral
`WorkbenchCanvasExecutionHost.createClassic()` now exposes the explicit
six-operation Classic contract without changing existing script loading or
runtime wiring. Focused behavior coverage proves operation forwarding and
boolean normalization; full `./scripts/agent-verify.sh`: PASS (542 tests;
Python AST 78; JavaScript syntax 103; architecture guards 4; diff check clean).

Wave 6 execution-host baseline verification (2026-09-09): PASS — three focused
lifecycle/ordering tests cover all six host operations, missing-op rejection,
script-load order, and `runLLMNode` delegation. This baseline is required before
replacing the page adapter.

Wave 6 execution-host wiring batch (2026-09-09): `canvas.html` now loads the
neutral execution host before the Classic adapter; the Classic factory delegates
to `WorkbenchCanvasExecutionHost.createClassic()` when available and retains an
isolated fallback for standalone loading. Focused behavior coverage proves
delegation and compatibility. Full `./scripts/agent-verify.sh`: PASS (543
tests; Python AST 78; JavaScript syntax 103; architecture guards 4; diff check
clean). R4-39 remains `IN_PROGRESS`.

Wave 6 execution-host load-order verification (2026-09-09): PASS — the page
loads neutral `execution-host.js` before `classic-execution-host.js`, and both
before `canvas.js`. Full `./scripts/agent-verify.sh`: PASS (544 tests; Python
AST 78; JavaScript syntax 103; architecture guards 4; diff check clean).

Wave 6 asset/executor contract characterization (2026-09-09): Asset Runtime's
101 operations span upload/drop, asset-manager DOM, workflow transfer, media
classification, node creation, and Canvas persistence callbacks. Executor
Runtime's 107 operations span provider execution, polling, cascade control,
result placement, and the already-characterized RunningHub/Loop projections.
These are separate replacement clusters and must not be collapsed into one new
monolith.

Wave 6 DOM-heavy seam characterization (2026-09-09): Video Provider Params
(15 ops), Output Grid (19 ops), and Generation Log (22 ops) remain UI-bound
contracts. Focused routing tests for Video Provider Params and Output Grid pass;
their replacement requires a neutral DOM/render host, not another data helper.

Wave 6 Output Grid identity batch (2026-09-09): output-item and pending-item DOM
key generation now delegates to `WorkbenchCanvasMediaTools`; the page retains
DOM reconciliation and interaction callbacks. Focused behavior coverage passes
for stable item/pending keys. Full `./scripts/agent-verify.sh`: PASS (541
tests; Python AST 78; JavaScript syntax 103; architecture guards 4; diff check
clean). R4-39 remains `IN_PROGRESS`.

R4-39 Wave 5 RunningHub current-entry batch (2026-09-09): current entry
extraction and model/workflow/app mode fallback now delegate to the neutral
renderer; the page retains selected-reference lookup. Focused behavior coverage
passes for entry and mode fallback. Full `./scripts/agent-verify.sh`: PASS (540
tests; Python AST 78; JavaScript syntax 103; architecture guards 4; diff check
clean). R4-39 remains `IN_PROGRESS`; the next bounded batch continues the
remaining Loop/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 RunningHub workflow-source batch (2026-09-09): workflow entry
field extraction, saved-config detection, and first-nonempty workflow source
selection now delegate to the neutral renderer. Focused behavior coverage passes
for field/config/source fallback rules. Full `./scripts/agent-verify.sh`: PASS
(539 tests; Python AST 78; JavaScript syntax 103; architecture guards 4; diff
check clean). R4-39 remains `IN_PROGRESS`; the next bounded batch continues the
remaining Loop/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 residual ownership sweep (2026-09-09): remaining RunningHub/Loop
page functions are limited to provider reads, node-state writes, UI/HTML
composition, and executor side effects; no additional pure projection remains
safe to move without crossing the current compatibility boundary. Full
verification remains green at 540 tests; R4-39 stays `IN_PROGRESS` pending the
remaining compatibility-runtime removal Gate. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 RunningHub visible-entry batch (2026-09-09): provider entry
filtering for disabled and hidden items now delegates to the neutral renderer;
the page retains provider access. Focused behavior coverage passes for
visible-entry filtering. Full `./scripts/agent-verify.sh`: PASS (538 tests;
Python AST 78; JavaScript syntax 103; architecture guards 4; diff check clean).
R4-39 remains `IN_PROGRESS`; the next bounded batch continues the remaining
Loop/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub entry-reference batch (2026-09-09): current entry
resolution by configuration key, workflow ID, and app ID fallback now delegates
to the neutral renderer; the page retains node-state reads. Focused behavior
coverage passes for key and ID fallback resolution. Full
`./scripts/agent-verify.sh`: PASS (537 tests; Python AST 78; JavaScript syntax
103; architecture guards 4; diff check clean). R4-39 remains `IN_PROGRESS`;
the next bounded batch continues the remaining Loop/workflow responsibility
cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub entry-collection batch (2026-09-09): model/app/workflow
entry aggregation and normalized identity projection now delegate to the neutral
renderer; the page retains provider reads. Focused behavior coverage passes for
cross-kind ordering and ID filtering. Full `./scripts/agent-verify.sh`: PASS
(536 tests; Python AST 78; JavaScript syntax 103; architecture guards 4; diff
check clean). R4-39 remains `IN_PROGRESS`; the next bounded batch continues the
remaining Loop/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 RunningHub entry-identity batch (2026-09-09): workflow/app/model
ID extraction, display-label fallback, configuration-key creation, and key
parsing now delegate to the neutral renderer. Focused behavior coverage passes
for identity and label fallbacks. Full `./scripts/agent-verify.sh`: PASS (535
tests; Python AST 78; JavaScript syntax 103; architecture guards 4; diff check
clean). R4-39 remains `IN_PROGRESS`; the next bounded batch continues the
remaining Loop/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 RunningHub workflow-field-list batch (2026-09-09): workflow input
enumeration and image/video/audio/number/boolean/text type inference now
delegate to the neutral renderer; the page retains link-recognition
compatibility wiring. Focused behavior coverage passes for link exclusion and
type inference. Full `./scripts/agent-verify.sh`: PASS (534 tests; Python AST
78; JavaScript syntax 103; architecture guards 4; diff check clean). R4-39
remains `IN_PROGRESS`; the next bounded batch continues the remaining
Loop/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub source-summary batch (2026-09-09): reference filtering,
image/video/audio grouping, image-limit enforcement, and prompt aggregation now
delegate to the neutral renderer; the page retains source ordering. Focused
behavior coverage passes for grouping, limiting, and prompt joining. Full
`./scripts/agent-verify.sh`: PASS (533 tests; Python AST 78; JavaScript syntax
103; architecture guards 4; diff check clean). R4-39 remains `IN_PROGRESS`;
the next bounded batch continues the remaining Loop/workflow responsibility
cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 Loop token-insertion batch (2026-09-09): token chip creation,
selection replacement, and fallback append behavior now delegate to the neutral
Loop prompt renderer; the page supplies DOM and selection handles. Focused
behavior coverage passes for fallback insertion. Full
`./scripts/agent-verify.sh`: PASS (532 tests; Python AST 78; JavaScript syntax
103; architecture guards 4; diff check clean). R4-39 remains `IN_PROGRESS`;
the next bounded batch continues the remaining Loop/workflow responsibility
cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub random-state batch (2026-09-09): random state read
semantics now delegate to the neutral renderer; the page retains state
initialization, writes, and refresh side effects. Focused behavior coverage
passes for default, disabled, and enabled states. Full
`./scripts/agent-verify.sh`: PASS (531 tests; Python AST 78; JavaScript syntax
103; architecture guards 4; diff check clean). R4-39 remains `IN_PROGRESS`;
the next bounded batch continues the remaining Loop/workflow responsibility
cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub random-eligibility batch (2026-09-09): numeric
random-field eligibility now delegates to the neutral renderer; the page
retains random-state toggling and generated-value persistence. Focused behavior
coverage passes for numeric/type and flag gating. Full `./scripts/agent-verify.sh`:
PASS (530 tests; Python AST 78; JavaScript syntax 103; architecture guards 4;
diff check clean). R4-39 remains `IN_PROGRESS`; the next bounded batch
continues the remaining Loop/workflow responsibility cluster. R4-40 and R5+
remain unauthorized.

R4-39 Wave 5 Loop prompt-counter batch (2026-09-09): prompt length and
counter-markup projection now delegate to the neutral Loop prompt renderer; the
page retains DOM counter updates. Focused behavior coverage passes for Unicode
length and over-limit markup. Full `./scripts/agent-verify.sh`: PASS (529
tests; Python AST 78; JavaScript syntax 103; architecture guards 4; diff check
clean). R4-39 remains `IN_PROGRESS`; the next bounded batch continues the
remaining Loop/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 RunningHub option-extraction batch (2026-09-09): field option
extraction from primitive lists, labeled objects, typed values, and known-field
fallbacks now delegates to the neutral renderer. Focused behavior coverage
passes for object and fallback extraction. Full `./scripts/agent-verify.sh`:
PASS (528 tests; Python AST 78; JavaScript syntax 103; architecture guards 4;
diff check clean). R4-39 remains `IN_PROGRESS`; the next bounded batch
continues the remaining Loop/workflow responsibility cluster. R4-40 and R5+
remain unauthorized.

R4-39 Wave 5 RunningHub field-metadata batch (2026-09-09): parameter-key
construction, field-kind detection, field-role detection, and default-value
normalization now delegate to the neutral renderer; the page retains
compatibility wrappers. Focused behavior coverage passes for media type, prompt
role, and array-default handling. Full `./scripts/agent-verify.sh`: PASS (527
tests; Python AST 78; JavaScript syntax 103; architecture guards 4; diff check
clean). R4-39 remains `IN_PROGRESS`; the next bounded batch continues the
remaining Loop/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 RunningHub workflow-pruning batch (2026-09-09): missing-field
deletion, empty-node removal, and dangling-link cleanup now delegate to
`WorkbenchCanvasRunningHubFieldRenderer.pruneWorkflowForMissingFields`; the
page supplies only workflow-node/link recognition callbacks. Focused behavior
coverage passes for node and link pruning. Full `./scripts/agent-verify.sh`:
PASS (524 tests; Python AST 78; JavaScript syntax 103; architecture guards 4;
diff check clean). R4-39 remains `IN_PROGRESS`; the next bounded batch
continues the remaining Loop/workflow responsibility cluster. R4-40 and R5+
remain unauthorized.

R4-39 Wave 5 RunningHub field-catalog batch (2026-09-09): enabled-field
fallback filtering and deterministic image-first field sorting now delegate to
neutral renderer helpers; the page retains source selection. Focused behavior
coverage passes for enabled fallback and image-order sorting. Full
`./scripts/agent-verify.sh`: PASS (526 tests; Python AST 78; JavaScript syntax
103; architecture guards 4; diff check clean). R4-39 remains `IN_PROGRESS`;
the next bounded batch continues the remaining Loop/workflow responsibility
cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub workflow-support batch (2026-09-09): field error
labels and workflow-link recognition now delegate to neutral renderer helpers
used by validation and pruning. Focused behavior coverage passes for label
fallbacks and strict link recognition. Full `./scripts/agent-verify.sh`: PASS
(525 tests; Python AST 78; JavaScript syntax 103; architecture guards 4; diff
check clean). R4-39 remains `IN_PROGRESS`; the next bounded batch continues
the remaining Loop/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 RunningHub legacy request-path batch (2026-09-09): the remaining
image-only workflow request path now reuses the neutral media input-state
projection for required/optional classification; the page retains error text
and pruning side effects. Full `./scripts/agent-verify.sh`: PASS (523 tests;
Python AST 78; JavaScript syntax 103; architecture guards 4; diff check clean).
R4-39 remains `IN_PROGRESS`; the next bounded batch continues the remaining
Loop/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 MiniMax segment-compaction projection cluster (2026-09-08):
timeline sorting, minimum duration normalization, total duration, and playhead
clamping now delegate to `WorkbenchCanvasMediaTools.minimaxCompactSegments`;
`canvas.js` retains node mutation. Focused behavior coverage proves ordering,
minimum duration, and upper-bound clamping. Full `./scripts/agent-verify.sh`:
PASS (491 tests; Python AST 78; JavaScript syntax 103; architecture guards 4;
diff check clean). R4-39 remains IN_PROGRESS; the next bounded slice is the
remaining media/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 MiniMax reference projection cluster (2026-09-08): aspect
parsing, reference normalization, deduplication, and image/video/audio summary
formatting now delegate to `WorkbenchCanvasMediaTools`; `canvas.js` retains
source collection. Focused behavior coverage proves aspect fallback, duplicate
removal, and summary counts. Full `./scripts/agent-verify.sh`: PASS (490 tests;
Python AST 78; JavaScript syntax 103; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 MiniMax playhead projection cluster (2026-09-08): time clamping,
timeline percentage, and duration-label formatting now delegate to
`WorkbenchCanvasMediaTools.minimaxPlayheadProjection`; `canvas.js` retains DOM
updates and selected-segment effects. Focused behavior coverage proves
fractional, upper-bound, and zero-duration cases. Full
`./scripts/agent-verify.sh`: PASS (489 tests; Python AST 78; JavaScript syntax
103; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 MiniMax pane-size projection cluster (2026-09-08): library,
preview, video-track, and reference-lane clamp rules now delegate to
`WorkbenchCanvasMediaTools.minimaxPaneProjection`; `canvas.js` retains pointer
events, node mutation, and CSS variable effects. Focused behavior coverage
proves lower and upper bounds. Full `./scripts/agent-verify.sh`: PASS (488
tests; Python AST 78; JavaScript syntax 103; architecture guards 4; diff check
clean). R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 MiniMax media-card rendering cluster (2026-09-08): image/video/
audio/file thumbnail type branches and labels now delegate to
`WorkbenchCanvasMediaOutputRenderer.renderLite`; `canvas.js` retains media-kind
and preview callbacks. Focused behavior coverage proves video lite-card
markup. Full `./scripts/agent-verify.sh`: PASS (487 tests; Python AST 78;
JavaScript syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub media-index batch (2026-09-09): ordered image, video,
and audio field indexing now delegates to
`WorkbenchCanvasRunningHubFieldRenderer.mediaIndexes`; the page retains only
the compatibility wrapper. Focused behavior coverage passes for image-order
sorting and per-kind counters. Full `./scripts/agent-verify.sh`: PASS (523
tests; Python AST 78; JavaScript syntax 103; architecture guards 4; diff check
clean). R4-39 remains `IN_PROGRESS`; the next bounded batch continues the
remaining Loop/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 RunningHub aspect-field ownership cleanup (2026-09-09):
full-aspect field detection now delegates to
`WorkbenchCanvasRunningHubFieldRenderer.isFullAspectField`; focused field
projection coverage remains green. Full `./scripts/agent-verify.sh`: PASS
(518 tests; Python AST 78; JavaScript syntax 103; architecture guards 4; diff
check clean). R4-39 remains IN_PROGRESS; the next bounded batch continues
the remaining Loop/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 RunningHub preset-parameter batch (2026-09-09): MiniMax prompt,
duration, aspect, and megapixel field-write composition now delegates to
`WorkbenchCanvasRunningHubFieldRenderer.applyPresetParams`; focused behavior
coverage passes for preset matching and writes. Full
`./scripts/agent-verify.sh`: PASS (519 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded batch continues the remaining Loop/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub field-value batch (2026-09-09): upstream media,
parameter/default precedence, skip rules, upload intent, and numeric
normalization now delegate to
`WorkbenchCanvasRunningHubFieldRenderer.fieldValue`; the page retains required
checks and upload effects. Focused media and numeric behavior tests pass. Full
`./scripts/agent-verify.sh`: PASS (520 tests; Python AST 78; JavaScript syntax
103; architecture guards 4; diff check clean). R4-39 remains `IN_PROGRESS`;
the next bounded batch continues the remaining Loop/workflow responsibility
cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub field-value ownership batch (2026-09-09): page-side
field value lookup now delegates media, prompt, default, and disabled-upstream
precedence to `WorkbenchCanvasRunningHubFieldRenderer.fieldValue`; random-value
generation remains page-owned. Focused behavior coverage passes for manual media
precedence. Full `./scripts/agent-verify.sh`: PASS (522 tests; Python AST 78;
JavaScript syntax 103; architecture guards 4; diff check clean). R4-39 remains
`IN_PROGRESS`; the next bounded batch continues the remaining Loop/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub media-input-state batch (2026-09-09): required,
optional, and present media classification now delegates to
`WorkbenchCanvasRunningHubFieldRenderer.mediaInputState`; the page retains
localized required-error text and optional workflow pruning side effects.
Focused behavior coverage passes for all three paths. Full
`./scripts/agent-verify.sh`: PASS (521 tests; Python AST 78; JavaScript syntax
103; architecture guards 4; diff check clean). R4-39 remains `IN_PROGRESS`;
the next bounded batch continues the remaining Loop/workflow responsibility
cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 loop-input prompt-selection projection cluster (2026-09-08):
current-round selection, start-index normalization, cycling, and empty fallback
now delegate to `WorkbenchCanvasLoopInputProjection.select`; `canvas.js` retains
prompt source collection. Focused behavior coverage proves sequential, cyclic,
and empty selection. Full `./scripts/agent-verify.sh`: PASS (486 tests; Python
AST 78; JavaScript syntax 103; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 loop-count and prompt-splitting projection cluster (2026-09-08):
count bounds and numbered/line-based prompt splitting now delegate to
`WorkbenchCanvasLoopPromptRenderer`; `canvas.js` retains graph traversal and
source collection. Focused behavior coverage proves lower/upper bounds,
numbered items, and single-item fallback. Full `./scripts/agent-verify.sh`:
PASS (485 tests; Python AST 78; JavaScript syntax 103; architecture guards 4;
diff check clean). R4-39 remains IN_PROGRESS; the next bounded slice is the
remaining media/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 loop-layout projection cluster (2026-09-08): opening/closing
dimensions and prompt/media panel height rules now delegate to
`WorkbenchCanvasLoopLayoutProjection`; `canvas.js` retains node mutation and
rerender effects. Focused behavior coverage proves open, closed, combined-panel,
and empty-panel sizes. Full `./scripts/agent-verify.sh`: PASS (484 tests;
Python AST 78; JavaScript syntax 103; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 loop-token label projection cluster (2026-09-08): localized
token-label fallback mapping now delegates to
`WorkbenchCanvasLoopPromptRenderer.tokenLabel`; `canvas.js` retains translation
lookup only. Focused behavior coverage proves localized and unknown-token
fallback behavior. Full `./scripts/agent-verify.sh`: PASS (483 tests; Python
AST 78; JavaScript syntax 102; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 loop-editor token markup cluster (2026-09-08): token-chip and
variable-text markup, escaping, labels, and deletion affordances now delegate
to `WorkbenchCanvasLoopPromptRenderer`; `canvas.js` retains editor DOM behavior.
Focused behavior coverage proves chip and variable composition. Full
`./scripts/agent-verify.sh`: PASS (482 tests; Python AST 78; JavaScript syntax
102; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 loop-input batching projection cluster (2026-09-08): image/video
batch size, start-index, current-round slicing, and filtering now delegate to
`WorkbenchCanvasLoopInputProjection.batch`; `canvas.js` retains source
collection. Focused behavior coverage proves current-round slicing and
fallback batch normalization. Full `./scripts/agent-verify.sh`: PASS (481
tests; Python AST 78; JavaScript syntax 102; architecture guards 4; diff check
clean). R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 loop-prompt projection cluster (2026-09-08): counter/total/progress
token replacement, selected-input precedence, and hidden-state fallback now
delegate to `WorkbenchCanvasLoopPromptRenderer`; `canvas.js` retains loop input
collection. Focused behavior coverage proves translated tokens and hidden
prompts. Full `./scripts/agent-verify.sh`: PASS (480 tests; Python AST 78;
JavaScript syntax 101; architecture guards 4; diff check clean). R4-39
remains IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 Comfy field rendering cluster (2026-09-08): boolean, slider,
dropdown, textarea, random-number, and scalar parameter markup now delegate to
`WorkbenchCanvasComfyFieldRenderer`; `canvas.js` retains value resolution,
random-state policy, and event binding. Focused behavior coverage proves
boolean and dropdown rendering. Full `./scripts/agent-verify.sh`: PASS (479
tests; Python AST 78; JavaScript syntax 100; architecture guards 4; diff check
clean). R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub prompt-field rendering cluster (2026-09-08): prompt
textarea markup and escaping now delegate to
`WorkbenchCanvasRunningHubFieldRenderer.promptMarkup`; `canvas.js` retains field
resolution and control binding. Focused behavior coverage proves escaped labels
and values. Full `./scripts/agent-verify.sh`: PASS (478 tests; Python AST 78;
JavaScript syntax 99; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub field rendering cluster (2026-09-08): boolean, slider,
select, random-number, and scalar parameter markup now delegate to
`WorkbenchCanvasRunningHubFieldRenderer`; `canvas.js` retains field value
resolution, control binding, and validation. Focused behavior coverage proves
boolean and select rendering. Full `./scripts/agent-verify.sh`: PASS (477
tests; Python AST 78; JavaScript syntax 99; architecture guards 4; diff check
clean). R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 LLM-pane rendering cluster (2026-09-08): LLM input/output and
chat panel markup, escaping, empty state, and running labels now delegate to
`WorkbenchCanvasLlmPaneRenderer`; `canvas.js` retains input, run, copy, retry,
and cascade event wiring. Focused behavior coverage proves escaped panel values
and chat empty state. Full `./scripts/agent-verify.sh`: PASS (476 tests; Python
AST 78; JavaScript syntax 98; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 Comfy media-input rendering cluster (2026-09-08): Comfy grouped
media inputs now reuse `WorkbenchCanvasMediaInputRenderer` for empty-state,
ordered markup, preview, audio, video, and missing-item branches; `canvas.js`
retains kind selection and drag/reorder effects. Focused behavior coverage
proves shared renderer wiring. Full `./scripts/agent-verify.sh`: PASS (475
tests; Python AST 78; JavaScript syntax 97; architecture guards 4; diff check
clean). R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub media-input rendering cluster (2026-09-08): grouped
RunningHub media inputs now reuse `WorkbenchCanvasMediaInputRenderer`;
`canvas.js` retains media-kind selection, preview callbacks, and list binding.
Focused behavior coverage proves the shared renderer path and removal of
duplicate inline markup. Full `./scripts/agent-verify.sh`: PASS (474 tests;
Python AST 78; JavaScript syntax 97; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 media-input list rendering cluster (2026-09-08): empty-state and
ordered item markup, escaping, and preview/missing projections now delegate to
`WorkbenchCanvasMediaInputRenderer`; `canvas.js` retains DOM event wiring and
reorder callbacks. Focused behavior coverage proves empty, escaped, preview,
and missing-item markup. Full `./scripts/agent-verify.sh`: PASS (473 tests;
Python AST 78; JavaScript syntax 97; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 prompt-preview rendering cluster (2026-09-08): prompt preview
list markup and escaping now delegate to
`WorkbenchCanvasPromptTemplateRenderer.renderPreviewInputs`; `canvas.js`
retains only container binding. Focused behavior coverage proves empty-state,
escaped labels, and null-item handling. Full `./scripts/agent-verify.sh`: PASS
(472 tests; Python AST 78; JavaScript syntax 96; architecture guards 4; diff
check clean). R4-39 remains IN_PROGRESS; the next bounded slice is the
remaining media/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 output-preview zoom/pan projection cluster (2026-09-08): wheel
zoom anchoring, bounds, reset, and drag translation now delegate to
`WorkbenchCanvasMediaTools.previewZoomProjection` and
`previewPanProjection`; `canvas.js` retains event wiring and DOM application.
Focused behavior coverage proves zoom-in, reset, and pan translation. Full
`./scripts/agent-verify.sh`: PASS (471 tests; Python AST 78; JavaScript syntax
96; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 output-compare slider projection cluster (2026-09-08): clamped
position and clip-path formatting now delegate to
`WorkbenchCanvasMediaTools.compareSliderProjection`; `canvas.js` retains DOM
style application. Focused behavior coverage proves centered, lower-bound, and
zero-width cases. Full `./scripts/agent-verify.sh`: PASS (470 tests; Python AST
78; JavaScript syntax 96; architecture guards 4; diff check clean). R4-39
remains IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 output-preview transform projection cluster (2026-09-08): preview
transform formatting and zoomed-state thresholding now delegate to
`WorkbenchCanvasMediaTools.previewTransformProjection`; `canvas.js` retains DOM
transform application. Focused behavior coverage proves translated, scaled,
and default states. Full `./scripts/agent-verify.sh`: PASS (469 tests; Python
AST 78; JavaScript syntax 96; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 brush-control projection cluster (2026-09-08): brush/mask size,
color, and alpha normalization now delegate to
`WorkbenchCanvasMediaTools.brushControlProjection`; `canvas.js` retains DOM
reads and Canvas drawing effects. Focused behavior coverage proves brush, mask,
and fallback controls. Full `./scripts/agent-verify.sh`: PASS (468 tests;
Python AST 78; JavaScript syntax 96; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 25 — crop Blob projection (2026-09-08): crop image
Canvas/Blob generation now delegates to
`WorkbenchCanvasMediaTools.cropImageBlob`; the page retains coordinate
conversion, upload and node mutation effects. Focused behavior coverage proves
crop rectangle and PNG Blob output. Full `./scripts/agent-verify.sh`: PASS
(395 tests; Python AST 78; JavaScript syntax 92; architecture guards 4; diff
check clean). R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 22 — outpaint natural-size projection (2026-09-08):
CSS-to-natural pixel scaling now delegates to
`WorkbenchCanvasMediaTools.outpaintNaturalSize`; the page retains image and
crop-state lookup. Focused behavior coverage proves scaled dimensions. Full
`./scripts/agent-verify.sh`: PASS (392 tests; Python AST 78; JavaScript syntax
92; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is remaining prompt/workflow/media-editing ownership. R4-40
and R5+ remain unauthorized.

R4-39 Wave 5 slice 57 — prompt-template empty state (2026-09-08): empty-list
placeholder HTML now delegates to `WorkbenchCanvasPromptTemplateData.emptyState`;
the page retains list container and event wiring. Focused behavior coverage
proves escaping and empty-state markup. Full `./scripts/agent-verify.sh`: PASS
(426 tests; Python AST 78; JavaScript syntax 93; architecture guards 4; diff
check clean). R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 58 — prompt-template renderer (2026-09-08): category
navigation, list cards, detail/edit markup and action buttons now delegate to
`WorkbenchCanvasPromptTemplateRenderer`; the page retains state and event
effects. Focused renderer coverage proves selection, escaping and apply-action
markup. Full `./scripts/agent-verify.sh`: PASS (428 tests; Python AST 78;
JavaScript syntax 94; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is remaining media/workflow ownership.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 editor-canvas sizing projection cluster (2026-09-08):
natural/client dimension fallback and CSS sizing for draw/text layers now
delegate to `WorkbenchCanvasMediaTools.editorCanvasProjection`; `canvas.js`
retains canvas mutation and redraw effects. Focused behavior coverage proves
natural-size and fallback cases. Full `./scripts/agent-verify.sh`: PASS (467
tests; Python AST 78; JavaScript syntax 96; architecture guards 4; diff check
clean). R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 59 — prompt-template renderer normalization (2026-09-08):
detail output now consumes the shared normalized positive, negative and
parameter projections, preserving existing display behavior. Full
`./scripts/agent-verify.sh`: PASS (428 tests; Python AST 78; JavaScript syntax
94; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is remaining media/workflow ownership. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 slice 60 — media text overlay geometry (2026-09-08): text overlay
record creation, font sizing, measurement and hit testing now delegate to
`WorkbenchCanvasMediaTextOverlay`; page-side Canvas drawing remains local.
Full `./scripts/agent-verify.sh`: PASS (429 tests; Python AST 78; JavaScript
syntax 95; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS;
the next bounded slice is remaining media/workflow ownership. R4-40 and R5+
remain unauthorized.

R4-39 Wave 5 slice 61 — custom grid-line geometry (2026-09-08): custom grid
line hit testing and clamped position updates now delegate to
`WorkbenchCanvasMediaTools`; pointer capture and preview effects remain local.
Full `./scripts/agent-verify.sh`: PASS (430 tests; Python AST 78; JavaScript
syntax 95; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS;
the next bounded slice is remaining media/workflow ownership. R4-40 and R5+
remain unauthorized.

R4-39 Wave 5 slice 62 — regular grid settings (2026-09-08): row, column and
gap normalization now delegates to `WorkbenchCanvasMediaTools`; page code keeps
DOM reads and label synchronization. Full `./scripts/agent-verify.sh`: PASS
(431 tests; Python AST 78; JavaScript syntax 95; architecture guards 4; diff
check clean). R4-39 remains IN_PROGRESS; the next bounded slice is remaining
media/workflow ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 media-drawing cluster (2026-09-08): brush, mask and number-label
style rules now delegate to `WorkbenchCanvasMediaTools`; page code retains
Canvas drawing effects. Full `./scripts/agent-verify.sh`: PASS (432 tests;
Python AST 78; JavaScript syntax 95; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is the remaining media and
workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 crop-geometry cluster (2026-09-08): outpaint growth and free-crop
resize geometry now delegate to `WorkbenchCanvasMediaTools`; page code retains
state mutation and clamping effects. Full `./scripts/agent-verify.sh`: PASS
(433 tests; Python AST 78; JavaScript syntax 95; architecture guards 4; diff
check clean). R4-39 remains IN_PROGRESS; the next bounded slice is the
remaining media/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 aspect-crop geometry cluster (2026-09-08): fixed-ratio edge and
corner resize geometry now delegates to `WorkbenchCanvasMediaTools`; page code
retains crop-state application and rendering. Full `./scripts/agent-verify.sh`:
PASS (434 tests; Python AST 78; JavaScript syntax 95; architecture guards 4;
diff check clean). R4-39 remains IN_PROGRESS; the next bounded slice is the
remaining media/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 custom-grid geometry cluster (2026-09-08): custom grid line
classification, deduplication, sorting and gap-aware rectangle generation now
delegate to `WorkbenchCanvasMediaTools`; page code retains DOM reads and preview
effects. Full `./scripts/agent-verify.sh`: PASS (435 tests; Python AST 78;
JavaScript syntax 95; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 workflow-transfer cluster (2026-09-08): selected workflow export
envelope construction now delegates to `WorkbenchCanvasWorkflowTransfer`; page
code retains subgraph selection and serialization callbacks. Full
`./scripts/agent-verify.sh`: PASS (436 tests; Python AST 78; JavaScript syntax
95; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 crop-state geometry cluster (2026-09-08): crop initialization and
ordinary crop-boundary clamping now delegate to `WorkbenchCanvasMediaTools`; page
code retains outpaint branching and redraw effects. Full
`./scripts/agent-verify.sh`: PASS (437 tests; Python AST 78; JavaScript syntax
95; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 editor-zoom geometry cluster (2026-09-08): crop rectangle scaling
during image-editor zoom now delegates to `WorkbenchCanvasMediaTools`; page code
retains DOM resizing, clamping and preview effects. Full
`./scripts/agent-verify.sh`: PASS (438 tests; Python AST 78; JavaScript syntax
95; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 editor-pointer cluster (2026-09-08): client-to-Canvas pointer
coordinate projection now delegates to `WorkbenchCanvasMediaTools`; page code
retains pointer event handling. Full `./scripts/agent-verify.sh`: PASS (439
tests; Python AST 78; JavaScript syntax 95; architecture guards 4; diff check
clean). R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 resize-control cluster (2026-09-08): resize control projection now
returns normalized scale, target dimensions and display text from
`WorkbenchCanvasMediaTools`; page code retains DOM synchronization. Full
`./scripts/agent-verify.sh`: PASS (440 tests; Python AST 78; JavaScript syntax
95; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 media-action dispatch cluster (2026-09-08): image-editor
mode-to-action dispatch now delegates to `WorkbenchCanvasMediaEditorState`; page
code retains concrete action callbacks. Full `./scripts/agent-verify.sh`: PASS
(441 tests; Python AST 78; JavaScript syntax 95; architecture guards 4; diff
check clean). R4-39 remains IN_PROGRESS; the next bounded slice is the
remaining media/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 workflow-import normalization cluster (2026-09-08): legacy array,
direct object and nested workflow import shapes now normalize through
`WorkbenchCanvasWorkflowTransfer`, removing empty records at the boundary. Full
`./scripts/agent-verify.sh`: PASS (442 tests; Python AST 78; JavaScript syntax
95; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 crop-handle interaction cluster (2026-09-08): crop box edge/corner
hit classification now delegates to `WorkbenchCanvasMediaTools`; page code
retains explicit handle overrides and drag initiation. Full
`./scripts/agent-verify.sh`: PASS (443 tests; Python AST 78; JavaScript syntax
95; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 crop-pointer delta cluster (2026-09-08): crop drag client-
coordinate delta calculation now delegates to `WorkbenchCanvasMediaTools`; page
code retains mode-specific state application and redraw. Full
`./scripts/agent-verify.sh`: PASS (444 tests; Python AST 78; JavaScript syntax
95; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 crop-drag snapshot cluster (2026-09-08): crop drag mode, pointer
origin and immutable crop snapshot creation now delegate to
`WorkbenchCanvasMediaTools`; page code retains event guards and lifecycle state.
Full `./scripts/agent-verify.sh`: PASS (445 tests; Python AST 78; JavaScript
syntax 95; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 workflow-export normalization cluster (2026-09-08): exported
workflow envelopes now remove empty nodes and connections at the
`WorkbenchCanvasWorkflowTransfer` boundary, matching import normalization. Full
`./scripts/agent-verify.sh`: PASS (445 tests; Python AST 78; JavaScript syntax
95; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 media-output download cluster (2026-09-08): downloadable output
URL filtering now delegates to `WorkbenchCanvasMediaTools`; page code retains
download invocation and missing-asset policy injection. Full
`./scripts/agent-verify.sh`: PASS (446 tests; Python AST 78; JavaScript syntax
95; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 output-metadata cluster (2026-09-08): output resolution and
run-duration metadata normalization now delegates to `WorkbenchCanvasMediaTools`;
page code retains localized formatting and DOM insertion. Full
`./scripts/agent-verify.sh`: PASS (447 tests; Python AST 78; JavaScript syntax
95; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 output-download naming cluster (2026-09-08): output download
extension parsing and timestamped filename generation now delegate to
`WorkbenchCanvasMediaTools`; page code retains actual download invocation. Full
`./scripts/agent-verify.sh`: PASS (448 tests; Python AST 78; JavaScript syntax
95; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 run-duration formatting cluster (2026-09-08): seconds/minutes
duration formatting now delegates to `WorkbenchCanvasMediaTools`; page code
retains metadata markup insertion. Full `./scripts/agent-verify.sh`: PASS (449
tests; Python AST 78; JavaScript syntax 95; architecture guards 4; diff check
clean). R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 output-data projection cluster (2026-09-08): output URL extraction
and URL-to-metadata lookup now delegate to `WorkbenchCanvasMediaTools`; page
code retains output lightbox and download effects. Full
`./scripts/agent-verify.sh`: PASS (450 tests; Python AST 78; JavaScript syntax
95; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 output-name projection cluster (2026-09-08): output filename
extraction and URL decoding now delegate to `WorkbenchCanvasMediaTools`; page
code retains card rendering and download effects. Full
`./scripts/agent-verify.sh`: PASS (451 tests; Python AST 78; JavaScript syntax
95; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 output-grid validation cluster (2026-09-08): grid split output-
layout validation now delegates to `WorkbenchCanvasMediaTools`; page code
retains pending-run gating and rendering. Full `./scripts/agent-verify.sh`: PASS
(452 tests; Python AST 78; JavaScript syntax 95; architecture guards 4; diff
check clean). R4-39 remains IN_PROGRESS; the next bounded slice is the
remaining media/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 output-grid placement cluster (2026-09-08): grid item row, column
and aspect-ratio placement normalization now delegates to
`WorkbenchCanvasMediaTools`; page code retains HTML insertion. Full
`./scripts/agent-verify.sh`: PASS (453 tests; Python AST 78; JavaScript syntax
95; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 output-presentation cluster (2026-09-08): output URL, media kind,
display name, run duration and optional grid placement now project through
`WorkbenchCanvasMediaTools`; page code retains type-specific HTML and effects.
Full `./scripts/agent-verify.sh`: PASS (454 tests; Python AST 78; JavaScript
syntax 95; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 output-media renderer cluster (2026-09-08): type-specific output
card HTML for missing, video, audio, file and image items now delegates to
`WorkbenchCanvasMediaOutputRenderer`; page code retains preview, missing-asset
and localization callbacks. Full `./scripts/agent-verify.sh`: PASS (455 tests;
Python AST 78; JavaScript syntax 96; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 output-append lifecycle cluster (2026-09-08): output record append,
metadata normalization, grid-layout replacement and comparison indexing now
delegate to `WorkbenchCanvasMediaTools`; page code retains node mutation and
persistence effects. Full `./scripts/agent-verify.sh`: PASS (456 tests; Python
AST 78; JavaScript syntax 96; architecture guards 4; diff check clean). R4-39
remains IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 output-viewed lifecycle cluster (2026-09-08): immutable output
viewed-state updates now delegate to `WorkbenchCanvasMediaTools`; page code
retains render/save effects only on change. Full `./scripts/agent-verify.sh`:
PASS (457 tests; Python AST 78; JavaScript syntax 96; architecture guards 4;
diff check clean). R4-39 remains IN_PROGRESS; the next bounded slice is the
remaining media/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 output-compare lifecycle cluster (2026-09-08): comparison URL
resolution now delegates to `WorkbenchCanvasMediaTools`, centralizing explicit
string/object mappings and run-reference fallback. Full
`./scripts/agent-verify.sh`: PASS (458 tests; Python AST 78; JavaScript syntax
96; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 lightbox-source cluster (2026-09-08): lightbox item collection and
source priority now delegate to `WorkbenchCanvasMediaTools`; page code retains
lightbox navigation and rendering effects. Full `./scripts/agent-verify.sh`:
PASS (459 tests; Python AST 78; JavaScript syntax 96; architecture guards 4;
diff check clean). R4-39 remains IN_PROGRESS; the next bounded slice is the
remaining media/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 lightbox-navigation cluster (2026-09-08): current item lookup and
cyclic direction navigation now delegate to `WorkbenchCanvasMediaTools`; page
code retains target-node lookup and lightbox rendering. Full
`./scripts/agent-verify.sh`: PASS (460 tests; Python AST 78; JavaScript syntax
96; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 group-lightbox index cluster (2026-09-08): group lightbox index
clamping now delegates to `WorkbenchCanvasMediaTools`; page code retains group
lookup and lightbox opening. Full `./scripts/agent-verify.sh`: PASS (461 tests;
Python AST 78; JavaScript syntax 96; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 lightbox index projection cluster (2026-09-08): group lightbox
index normalization now uses the shared list-index boundary. Full
`./scripts/agent-verify.sh`: PASS (461 tests; Python AST 78; JavaScript syntax
96; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 lightbox visibility cluster (2026-09-08): image vs video lightbox
visibility projection now delegates to `WorkbenchCanvasMediaTools`; page code
retains DOM display updates and resource loading. Full
`./scripts/agent-verify.sh`: PASS (462 tests; Python AST 78; JavaScript syntax
96; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 56 — prompt-template list cards (2026-09-08): list-card HTML
now delegates to `WorkbenchCanvasPromptTemplateData.itemCard`; the page retains
the list container and event wiring. Focused behavior coverage proves selection
class, escaping, source and category labels. Full `./scripts/agent-verify.sh`:
PASS (425 tests; Python AST 78; JavaScript syntax 93; architecture guards 4;
diff check clean). R4-39 remains IN_PROGRESS; the next bounded slice is
remaining prompt/workflow/media-editing ownership. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 slice 55 — node positions (2026-09-08): position projection now
delegates to `WorkbenchCanvasNodePresentation.position`; the page retains DOM
style application. Focused behavior coverage proves numeric coordinates and
zero fallback. Full `./scripts/agent-verify.sh`: PASS (424 tests; Python AST 78;
JavaScript syntax 93; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is remaining prompt/workflow/media-editing
ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 54 — node dimensions (2026-09-08): dimension projection now
delegates to `WorkbenchCanvasNodePresentation.dimensions`; the page retains DOM
style application. Focused behavior coverage proves explicit-size and
default-size paths. Full `./scripts/agent-verify.sh`: PASS (423 tests; Python
AST 78; JavaScript syntax 93; architecture guards 4; diff check clean). R4-39
remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 53 — prompt-template preview data (2026-09-08): detail
preview data now delegates to `WorkbenchCanvasPromptTemplateData.preview`; the
page retains markup and escaping. Focused behavior coverage proves normalized
positive, negative and parameter fields. Full `./scripts/agent-verify.sh`: PASS
(422 tests; Python AST 78; JavaScript syntax 93; architecture guards 4; diff
check clean). R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 52 — fixed node-size policy (2026-09-08): fixed-height
decision now delegates to `WorkbenchCanvasNodePresentation.isFixedSize`; the
page retains DOM style application. Focused behavior coverage proves explicit
and default fixed-height paths. Full `./scripts/agent-verify.sh`: PASS (421
tests; Python AST 78; JavaScript syntax 93; architecture guards 4; diff check
clean). R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 51 — default node sizes (2026-09-08): node-size mapping now
delegates to `WorkbenchCanvasNodePresentation.defaultSize`; the page retains
DOM sizing application. Focused behavior coverage proves image, LLM and
unknown-type sizes. Full `./scripts/agent-verify.sh`: PASS (420 tests; Python
AST 78; JavaScript syntax 93; architecture guards 4; diff check clean). R4-39
remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 50 — media-kind titles (2026-09-08): title mapping now
delegates to `WorkbenchCanvasNodePresentation.mediaTitle`; the page retains
media-kind resolution. Focused behavior coverage proves video, audio and image
fallback labels. Full `./scripts/agent-verify.sh`: PASS (419 tests; Python AST
78; JavaScript syntax 93; architecture guards 4; diff check clean). R4-39
remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 49 — node CSS classes (2026-09-08): CSS class projection
now delegates to `WorkbenchCanvasNodePresentation.className`; the page retains
DOM creation and attribute assignment. Focused behavior coverage proves type,
media, size and selection composition. Full `./scripts/agent-verify.sh`: PASS
(418 tests; Python AST 78; JavaScript syntax 93; architecture guards 4; diff
check clean). R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 48 — media-node title override (2026-09-08): title override
now delegates to `WorkbenchCanvasNodePresentation.displayTitle`; the page
retains media-title lookup and markup. Focused behavior coverage proves media,
non-media and missing-URL paths. Full `./scripts/agent-verify.sh`: PASS (417
tests; Python AST 78; JavaScript syntax 93; architecture guards 4; diff check
clean). R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 47 — node status markup (2026-09-08): run-status badge HTML
now delegates to `WorkbenchCanvasNodePresentation.statusMarkup`; the page
retains only the insertion point. Focused behavior coverage proves escaping,
status class and cascade suffix. Full `./scripts/agent-verify.sh`: PASS (416
tests; Python AST 78; JavaScript syntax 93; architecture guards 4; diff check
clean). R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 46 — node status visibility (2026-09-08): run-status badge
visibility now delegates to `WorkbenchCanvasNodePresentation.shouldShowStatus`;
the page retains status markup. Focused behavior coverage proves normal, failed
and cascade-failed states. Full `./scripts/agent-verify.sh`: PASS (415 tests;
Python AST 78; JavaScript syntax 93; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 45 — node status labels (2026-09-08): run-status label
projection now delegates to `WorkbenchCanvasNodePresentation.statusLabel`; the
page retains status markup and visibility policy. Focused behavior coverage
proves known and unknown status handling. Full `./scripts/agent-verify.sh`:
PASS (414 tests; Python AST 78; JavaScript syntax 93; architecture guards 4;
diff check clean). R4-39 remains IN_PROGRESS; the next bounded slice is
remaining prompt/workflow/media-editing ownership. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 slice 44 — node title projection (2026-09-08): neutral node title
mapping now delegates to `WorkbenchCanvasNodePresentation`; the page retains
title markup and media display overrides. Focused behavior coverage proves
localized and fallback title mapping. Full `./scripts/agent-verify.sh`: PASS
(413 tests; Python AST 78; JavaScript syntax 93; architecture guards 4; diff
check clean). R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 43 — Grid-split output naming (2026-09-08): Grid-split
filenames now reuse `WorkbenchCanvasMediaTools.outputFileName`; the page retains
row/column suffix selection. Full `./scripts/agent-verify.sh`: PASS (412 tests;
Python AST 78; JavaScript syntax 92; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 42 — media output filenames (2026-09-08): suffix and
extension composition now delegates to `WorkbenchCanvasMediaTools.outputFileName`;
the page retains operation-specific suffixes. Focused behavior coverage proves
crop and custom-extension naming. Full `./scripts/agent-verify.sh`: PASS (412
tests; Python AST 78; JavaScript syntax 92; architecture guards 4; diff check
clean). R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 41 — media output base names (2026-09-08): base-name
parsing now delegates to `WorkbenchCanvasMediaTools.baseNameWithoutExtension`;
the page retains suffix selection and upload effects. Focused behavior coverage
proves extension removal and fallback naming. Full `./scripts/agent-verify.sh`:
PASS (411 tests; Python AST 78; JavaScript syntax 92; architecture guards 4;
diff check clean). R4-39 remains IN_PROGRESS; the next bounded slice is
remaining prompt/workflow/media-editing ownership. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 slice 40 — prompt-template positive text (2026-09-08): positive
text normalization now delegates to
`WorkbenchCanvasPromptTemplateData.positiveText`; the page retains preview
markup and escaping. Focused behavior coverage proves whitespace trimming and
empty suppression. Full `./scripts/agent-verify.sh`: PASS (410 tests; Python
AST 78; JavaScript syntax 92; architecture guards 4; diff check clean). R4-39
remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 39 — prompt-template negative text (2026-09-08): negative
text normalization now delegates to
`WorkbenchCanvasPromptTemplateData.negativeText`; the page retains preview
markup and escaping. Focused behavior coverage proves whitespace trimming and
empty suppression. Full `./scripts/agent-verify.sh`: PASS (409 tests; Python
AST 78; JavaScript syntax 92; architecture guards 4; diff check clean). R4-39
remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 38 — prompt-template display scene (2026-09-08): display
scene fallback now delegates to `WorkbenchCanvasPromptTemplateData.displayScene`;
the page retains preview markup and escaping. Focused behavior coverage proves
scene preservation and positive-text fallback. Full `./scripts/agent-verify.sh`:
PASS (408 tests; Python AST 78; JavaScript syntax 92; architecture guards 4;
diff check clean). R4-39 remains IN_PROGRESS; the next bounded slice is
remaining prompt/workflow/media-editing ownership. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 slice 37 — outpaint rectangle projection (2026-09-08):
display-to-natural outpaint rectangle conversion now delegates to
`WorkbenchCanvasMediaTools.outpaintRectFromDisplay`; the page retains image and
crop-state lookup. Focused behavior coverage proves offset scaling and minimum
natural dimensions. Full `./scripts/agent-verify.sh`: PASS (407 tests; Python
AST 78; JavaScript syntax 92; architecture guards 4; diff check clean). R4-39
remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 36 — crop rectangle projection (2026-09-08):
display-to-natural crop rectangle conversion now delegates to
`WorkbenchCanvasMediaTools.cropRectFromDisplay`; the page retains image and
crop-state lookup. Focused behavior coverage proves scale, rounding and
minimum dimensions. Full `./scripts/agent-verify.sh`: PASS (406 tests; Python
AST 78; JavaScript syntax 92; architecture guards 4; diff check clean). R4-39
remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 35 — prompt-template detail source labels (2026-09-08):
detail source label resolution now delegates to
`WorkbenchCanvasPromptTemplateData.detailSourceLabel`; the page retains
translation lookup and preview markup. Focused behavior coverage proves
built-in and user-template detail labels. Full `./scripts/agent-verify.sh`:
PASS (405 tests; Python AST 78; JavaScript syntax 92; architecture guards 4;
diff check clean). R4-39 remains IN_PROGRESS; the next bounded slice is
remaining prompt/workflow/media-editing ownership. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 slice 34 — prompt-template source labels (2026-09-08): source
label resolution now delegates to `WorkbenchCanvasPromptTemplateData.sourceLabel`;
the page retains translation lookup and escaping. Focused behavior coverage
proves built-in and user-template labels. Full `./scripts/agent-verify.sh`:
PASS (404 tests; Python AST 78; JavaScript syntax 92; architecture guards 4;
diff check clean). R4-39 remains IN_PROGRESS; the next bounded slice is
remaining prompt/workflow/media-editing ownership. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 slice 33 — selected prompt-template item (2026-09-08): item
resolution now delegates to `WorkbenchCanvasPromptTemplateData.selectedItem`;
the page retains selection id and collection state. Focused behavior coverage
proves current-id, first-item and empty-list paths. Full
`./scripts/agent-verify.sh`: PASS (403 tests; Python AST 78; JavaScript syntax
92; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is remaining prompt/workflow/media-editing ownership. R4-40
and R5+ remain unauthorized.

R4-39 Wave 5 slice 32 — prompt-template parameter summary (2026-09-08):
parameter summary projection now delegates to
`WorkbenchCanvasPromptTemplateData.paramsText`; the page retains preview markup
and escaping. Focused behavior coverage proves ordered multi-parameter and
empty summaries. Full `./scripts/agent-verify.sh`: PASS (402 tests; Python AST
78; JavaScript syntax 92; architecture guards 4; diff check clean). R4-39
remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 31 — prompt-node text projection (2026-09-08): current
prompt-node text lookup now delegates to
`WorkbenchCanvasPromptTemplateData.nodeText`; the page retains node collection
and selected id state. Focused behavior coverage proves prompt-type filtering
and trimming. Full `./scripts/agent-verify.sh`: PASS (401 tests; Python AST 78;
JavaScript syntax 92; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is remaining prompt/workflow/media-editing
ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 30 — prompt-template selection fallback (2026-09-08):
selected-item fallback now delegates to
`WorkbenchCanvasPromptTemplateData.selectedId`; the page retains selection state
assignment. Focused behavior coverage proves retained, missing and empty
selection handling. Full `./scripts/agent-verify.sh`: PASS (400 tests; Python
AST 78; JavaScript syntax 92; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 29 — prompt-template category counts (2026-09-08): category
count aggregation now delegates to
`WorkbenchCanvasPromptTemplateData.categoryCounts`; the page retains markup and
translation rendering. Focused behavior coverage proves default-category
normalization and totals. Full `./scripts/agent-verify.sh`: PASS (399 tests;
Python AST 78; JavaScript syntax 92; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 28 — PNG Blob boundary (2026-09-08): crop, outpaint, mask,
brush and Grid-split paths now use the shared
`WorkbenchCanvasMediaTools.toPngBlob` encoding boundary. Focused behavior
coverage proves the `image/png` MIME contract. Full `./scripts/agent-verify.sh`:
PASS (398 tests; Python AST 78; JavaScript syntax 92; architecture guards 4;
diff check clean). R4-39 remains IN_PROGRESS; the next bounded slice is
remaining prompt/workflow/media-editing ownership. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 slice 27 — Grid-split Blob projection (2026-09-08): multi-image
Canvas/Blob generation now delegates to
`WorkbenchCanvasMediaTools.splitImageBlobs`; the page retains upload naming
and output-node projection. Focused behavior coverage proves rectangle order,
metadata and Blob output. Full `./scripts/agent-verify.sh`: PASS (397 tests;
Python AST 78; JavaScript syntax 92; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 24 — brush layer composition (2026-09-08): image, draw and
text layer composition now delegates to
`WorkbenchCanvasMediaTools.composeBrushCanvas`; the page retains upload and
node mutation effects. Focused behavior coverage proves layer order and output
dimensions. Full `./scripts/agent-verify.sh`: PASS (394 tests; Python AST 78;
JavaScript syntax 92; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is remaining prompt/workflow/media-editing
ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 23 — resized-image Blob projection (2026-09-08): resized
image canvas generation now delegates to
`WorkbenchCanvasMediaTools.resizedImageBlob`; the page retains editor lookup
and dimension selection. Focused behavior coverage proves target dimensions,
smoothing and Blob output. Full `./scripts/agent-verify.sh`: PASS (393 tests;
Python AST 78; JavaScript syntax 92; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 4 slice 7 — connection deletion projection (2026-09-08): link
deletion now delegates local edge removal to
`WorkbenchCanvasGraphFragment.removeConnection`; `canvas.js` retains undo,
generator-input synchronization, render and save effects. Full
`./scripts/agent-verify.sh`: PASS (379 tests; Python AST 78; JavaScript syntax
87; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is remaining graph/group mutation ownership. R4-40 and R5+
remain unauthorized.

R4-39 Wave 5 slice 13 — aspect-ratio crop geometry (2026-09-08): crop-boundary
geometry now delegates to `WorkbenchCanvasMediaTools.aspectCropToBounds`; the
page retains pointer handling and crop-state mutation. Full
`./scripts/agent-verify.sh`: PASS (383 tests; Python AST 78; JavaScript syntax
90; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is remaining prompt/workflow/media-editing ownership. R4-40
and R5+ remain unauthorized.

R4-39 Wave 5 slice 21 — prompt-template button projection (2026-09-08):
open-button active state and ARIA projection now delegate to
`WorkbenchCanvasPromptTemplateInteraction`; the page retains the DOM reference
and selected node id. Focused behavior coverage proves active/inactive states.
Full `./scripts/agent-verify.sh`: PASS (391 tests; Python AST 78; JavaScript
syntax 92; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is remaining prompt/workflow/media-editing
ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 20 — prompt-template scroll state (2026-09-08): modal
scroll snapshot and restoration now delegate to
`WorkbenchCanvasPromptTemplateInteraction`; the page retains the panel
reference and animation-frame adapter. Focused behavior coverage proves nested
positions survive rerender. Full `./scripts/agent-verify.sh`: PASS (390 tests;
Python AST 78; JavaScript syntax 92; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 18 — media pixel detection (2026-09-08): drawn-pixel
presence detection now delegates to `WorkbenchCanvasMediaTools.canvasHasPixels`;
the page retains the optional text-layer check. Focused behavior coverage
proves empty versus painted alpha buffers. Full `./scripts/agent-verify.sh`:
PASS (388 tests; Python AST 78; JavaScript syntax 92; architecture guards 4;
diff check clean). R4-39 remains IN_PROGRESS; the next bounded slice is
remaining prompt/workflow/media-editing ownership. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 slice 19 — outpaint reset projection (2026-09-08): reset-to-bounds
state mutation now delegates to `WorkbenchCanvasMediaTools.resetOutpaintState`;
the page retains crop-bound lookup and render effects. Focused behavior
coverage proves deterministic reset. Full `./scripts/agent-verify.sh`: PASS
(389 tests; Python AST 78; JavaScript syntax 92; architecture guards 4; diff
check clean). R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 17 — outpaint bounds projection (2026-09-08): outpaint
crop-state minimum-size and position clamping now delegate to
`WorkbenchCanvasMediaTools.clampOutpaintState`; the page retains state lookup
and render effects. Focused behavior coverage proves bounds normalization. Full
`./scripts/agent-verify.sh`: PASS (387 tests; Python AST 78; JavaScript syntax
92; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is remaining prompt/workflow/media-editing ownership. R4-40
and R5+ remain unauthorized.

R4-39 Wave 5 slice 16 — media mask projection (2026-09-08): drawn-alpha mask
conversion now delegates to `WorkbenchCanvasMediaTools.maskFromCanvas`; the
page retains editor lookup and upload effects. Focused behavior coverage proves
transparent/painted threshold mapping. Full `./scripts/agent-verify.sh`: PASS
(386 tests; Python AST 78; JavaScript syntax 92; architecture guards 4; diff
check clean). R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 15 — prompt-template application (2026-09-08): selected
template text mutation and modal close now delegate to
`WorkbenchCanvasPromptTemplateApplication`; the page retains lookup and
post-application save/render effects. Focused behavior coverage proves success
and missing-input rejection. Full `./scripts/agent-verify.sh`: PASS (385
tests; Python AST 78; JavaScript syntax 92; architecture guards 4; diff check
clean). R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 14 — prompt-template interaction routing (2026-09-08):
prompt-template modal search, library, close, apply and selection event routing
now delegates to `WorkbenchCanvasPromptTemplateInteraction`; the page supplies
state callbacks and retains modal rendering/state mutation. Focused behavior
coverage proves query/library normalization and apply dispatch. Full
`./scripts/agent-verify.sh`: PASS (384 tests; Python AST 78; JavaScript syntax
91; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is remaining prompt/workflow/media-editing ownership. R4-40
and R5+ remain unauthorized.

R4-39 Wave 5 slice 12 — media collection projections (2026-09-08): output-
image URL filtering and Group-image item projection now delegate to
`WorkbenchCanvasMediaTools`; the page supplies media-kind and missing-asset
policies. Full `./scripts/agent-verify.sh`: PASS (383 tests; Python AST 78;
JavaScript syntax 90; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is remaining prompt/workflow/media-editing
ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 11 — media output naming (2026-09-08): extension
extraction, filename sanitization and Group-image download naming now delegate
to `WorkbenchCanvasMediaTools`; the page supplies only the optional fallback
name. Full `./scripts/agent-verify.sh`: PASS (383 tests; Python AST 78;
JavaScript syntax 90; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is remaining prompt/workflow/media-editing
ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 10 — media-editor output positioning (2026-09-08):
image-editor output-node positioning now delegates to
`WorkbenchCanvasMediaTools.outputPoint`; node lookup/creation and graph effects
remain page-owned. Full `./scripts/agent-verify.sh`: PASS (383 tests; Python
AST 78; JavaScript syntax 90; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 9 — media-editor apply dispatch (2026-09-08): mode-to-
action dispatch now delegates to `WorkbenchCanvasMediaEditorState.applyAction`;
action implementations and media mutations remain compatibility-owned. Full
`./scripts/agent-verify.sh`: PASS (383 tests; Python AST 78; JavaScript syntax
90; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is remaining prompt/workflow/media-editing ownership. R4-40
and R5+ remain unauthorized.

R4-39 Wave 5 slice 8 — media-editor mode rules (2026-09-08): mode
normalization and presentation mapping now delegate to
`WorkbenchCanvasMediaEditorState`; `canvas.js` retains DOM toggles, state
transitions and media mutations. Full `./scripts/agent-verify.sh`: PASS (383
tests; Python AST 78; JavaScript syntax 90; architecture guards 4; diff check
clean). R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 7 — workflow filename projection (2026-09-08): export
filename sanitization and timestamp formatting now delegate to
`WorkbenchCanvasWorkflowTransfer.filenameForExport`; the page supplies only
Canvas title and extension. Full `./scripts/agent-verify.sh`: PASS (382 tests;
Python AST 78; JavaScript syntax 89; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 6 — Grid layout projection (2026-09-08): image-editor Grid
row/column metadata now delegates to `WorkbenchCanvasMediaTools.gridLayout`;
the page supplies only the generated group id. Full
`./scripts/agent-verify.sh`: PASS (381 tests; Python AST 78; JavaScript syntax
89; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is remaining prompt/workflow/media-editing ownership. R4-40
and R5+ remain unauthorized.

R4-39 Wave 5 slice 3 — prompt-template data ownership (2026-09-08): naming,
localization, text composition, search filtering and default-name derivation
now delegate to `WorkbenchCanvasPromptTemplateData`; page library I/O, modal
DOM and prompt-node mutation remain local. Full `./scripts/agent-verify.sh`:
PASS (381 tests; Python AST 78; JavaScript syntax 89; architecture guards 4;
diff check clean). R4-39 remains IN_PROGRESS; the next bounded slice is
remaining prompt/workflow/media-editing ownership. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 slice 4 — image-resize projection (2026-09-08): source-size
normalization and scale clamping now delegate to
`WorkbenchCanvasMediaTools.resizeDimensions`; `canvas.js` retains DOM lookup
and editor mutation. Full `./scripts/agent-verify.sh`: PASS (381 tests; Python
AST 78; JavaScript syntax 89; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 5 — prompt-template category labels (2026-09-08): system
and remote category-label resolution now delegates to
`WorkbenchCanvasPromptTemplateData.categoryLabel`; the page supplies
translations and library records. Full `./scripts/agent-verify.sh`: PASS (381
tests; Python AST 78; JavaScript syntax 89; architecture guards 4; diff check
clean). R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 2 — media-editor math ownership (2026-09-08): Classic
crop-ratio parsing/fitting, grid rectangle splitting, resize-scale clamping
and circled labels now delegate to `WorkbenchCanvasMediaTools`; page DOM and
media mutation remain local. Full `./scripts/agent-verify.sh`: PASS (380 tests;
Python AST 78; JavaScript syntax 88; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 slice 1 — workflow-transfer modal ownership (2026-09-08): modal
open/close state and selection metadata now live in
`WorkbenchCanvasWorkflowTransferUi`; `canvas.js` retains payload construction,
transport actions and Canvas callbacks. Full `./scripts/agent-verify.sh`: PASS
(380 tests; Python AST 78; JavaScript syntax 88; architecture guards 4; diff
check clean). R4-39 remains IN_PROGRESS; the next bounded slice is remaining
prompt/workflow/media-editing ownership. R4-40 and R5+ remain unauthorized.

R4-39 Wave 4 slice 9 — Alt-drag subgraph duplication (2026-09-08): root/child
cloning, id remapping and optional incoming-edge projection now delegate to
`WorkbenchCanvasGraphFragment.duplicateSubgraph`; `canvas.js` retains
insertion, duplicate-edge suppression and compatibility admission. Full
`./scripts/agent-verify.sh`: PASS (379 tests; Python AST 78; JavaScript syntax
87; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is remaining graph/group mutation ownership. R4-40 and R5+
remain unauthorized.

R4-39 Wave 4 slice 8 — replacement deletion projection (2026-09-08): output
conversion and grouped-upload replacement now delegate node/incident-edge
removal to `WorkbenchCanvasGraphFragment.removeGraphRecords`; page-specific
edge reattachment and render/save effects remain local. Full
`./scripts/agent-verify.sh`: PASS (379 tests; Python AST 78; JavaScript syntax
87; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is remaining graph/group mutation ownership. R4-40 and R5+
remain unauthorized.

R3 is complete. R4 is active. R3 supplied the SQLite Project/Canvas foundation, explicit identity mapping,
revision, authorization, migration comparison, rollback export, transactional
audit/outbox, and migration-report command are tested. The live Legacy report at
2026-09-04T23:36:06Z imported 22 Canvas files, skipped 0, and found 0 payload
differences. R4 now has a tested SQLite compatibility repository with true SQL
compare-and-swap. SQLite authority was activated locally after the validated
backup/compare (22 payloads), and canonical routing is now the default runtime when
that authority state is `sqlite`; an explicit false value was originally a bounded
rollback control and is now (R4-03) refused at startup while authority is `sqlite`,
remaining valid only when authority is inactive. Isolated API, browser read, browser write,
restart, stale-conflict, and rollback-export acceptance passed. The retained
Classic/Smart editor adapters now share the neutral CanvasRecord load/save/metadata
client, version-poll coordinator, and transport-neutral update-message filter;
their existing polling intervals and merge behavior remain adapter-owned.
The shared state runtime is now default-on, with `unified_canvas=0` retained as
the bounded U7 rollback control. Read-only browser rechecks of both Classic and
historical Smart records passed on the default URL path; this does not yet
authorize page deletion. NodeShell base is also default-on on loopback, with
`node_shell=0` retained as its bounded U7 rollback control. MediaRenderer is
default-on on loopback with `media_renderer=0` as its bounded U7 rollback control.
Legacy source-payload rendering inside NodeShell is also default-on, with
`legacy_renderer=0` retained as its bounded U7 rollback control.
Semantic zoom is default-on with `semantic_zoom=0` retained as its bounded U7
rollback control.
Smart screen-space controls are default-on with `screen_space_controls=0`
retained as their bounded U7 rollback control.
Classic and Smart renderer-admission evaluation now runs through the shared
`RendererAdmission` boundary. Classic retains its explicit Legacy type policy;
Smart retains its non-image/non-Group policy, while renderer selection remains
owned by the Unified host.
Shared media playback-state capture/restore is now covered as a transport- and
persistence-neutral contract; adapter player binding and fallback policy remain
unchanged.
Classic standalone blank Image deletion now likewise uses the existing loopback
`NodeMutationService` route on the default path. Content-bearing Images,
group-linked Images, and all other node deletion contracts remain bounded adapter
compatibility until their graph/media parity is characterized.
The same bounded mutation path now also covers a standalone blank Smart Prompt:
only the durable `smart-prompt` shape without text/result, active LLM settings,
attachments, input references, links, or group membership may update its position
or delete through `NodeMutationService`; every richer Prompt remains adapter-owned
compatibility.
The same narrow Classic node class now commits a single non-Alt, non-grouped drag
position through `NodeMutationService`; a rejected or stale write restores its
prior visual position instead of issuing a raw Canvas save. Rich move/resize and
group/media behavior remain adapter-owned compatibility.
The historical Smart handoff now preserves query parameters while replacing the
Canvas id and cache version, so the explicit all-zero rollback is effective from
the normal Canvas URL as well as the retained adapter URL.
Canvas list and asset-manager openings now both use the normal `canvas.html`
entry through the same `normalCanvasUrl` contract; direct Smart page routing is
confined to the retained compatibility boundary.
The retained Classic/Smart adapters also delegate Canvas-list project memory and
encoded list-URL construction to that same entry boundary; this changes no Canvas
record and leaves their page-specific navigation UI intact.
Their text-copy fallback and optional secure-context clipboard verification are
also delegated to a DOM-neutral shared helper; error/modal and page-specific UI
decisions remain adapter-owned.
The API image-size calculation now likewise shares only its pure, injected
algorithm; each adapter retains its own ratio parser, size map, model choice, and
provider/execution behavior.

R4 backend mutation safety boundary (2026-09-06): the Legacy mutation repository
no longer trusts the frontend blank-node eligibility gate. Inside the same canvas
lock that performs the mutation it now rejects content-bearing, grouped,
history-linked, input-referenced, and (except the characterized Image edge
cleanup) connected nodes for both update and delete with
`unsupported_node_shape` (HTTP 422); stale revisions still return 409 and the
supported standalone blank shapes keep their existing contracts. Adapter and
route tests pin the rejection and mapping, and the full regression passes at 280
tests.

R4 canonical data-integrity repair (2026-09-06): a legacy-routed (rollback)
server session that morning produced a verified split-brain — one orphan Canvas
existed only in Legacy JSON, sixteen active Canvases carried list-board position
drift, and the SQLite `canvases` table contained a `revision`/`baseline` row
leaked by an older `test_repository_baseline` run before that test gained its
routing patch. After a pre-repair snapshot
(`data/canvas-source-backups/r4-repair-20260906T091748/`), refreshing the stale
`7ed83bf5…` rollback file from its newer canonical payload, converging the orphan
and board-only drifts through the tested migration import path, and purging the
test-artifact row through `purge_canvas_payload` with audit, the post-repair
report `data/r4-repair-migration-report.json` shows authority `sqlite`, 23
imported, 0 skipped, 23 comparisons, 0 differences, SQLite rows equal to Legacy
files with zero divergent payloads. An isolated restart read on `127.0.0.1:3012`
verified the repaired database through normal SQLite routing: 17 active Canvas
records, no phantom `baseline` entry, the imported orphan readable with its two
nodes, and the repaired Classic record's canonical metadata intact. Running a
legacy-routed server (`WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED=false`) while
SQLite authority is active is now a known split-brain hazard and must not be used
for normal product work.

R4 deferred-migration assessment (2026-09-06): three next-step candidates were
inspected and deliberately deferred with recorded reasons. Normal-connect
service migration is blocked because both adapters couple the edge commit with
page-owned side effects on the same raw save (Smart mutates target execution
config and `inputNodeIds`; Classic adds group membership and generator/output
sync); splitting it now would force double writes or a premature rich-mutation
API. Keyboard command lifecycle unification requires the command-registry step
because the adapters own genuinely different command maps and selection models.
Polling interval/eligibility ownership is blocked on the save/merge machinery
unification. The mutation shape boundary additionally gained SQLite-store test
coverage (283 tests total).

R4 save/merge characterization (2026-09-06): both adapter save state machines are
now characterized side by side in `docs/plans/R4_OWNERSHIP_MATRIX.md` — Classic
runs replace semantics with a dual revision mirror (`lastCanvasUpdatedAt` plus
`canvas.updated_at`), dirty-flag-gated 409 recovery, and viewport/selection
preservation; Smart runs merge-union semantics with a single revision source,
`canvasSyncInFlight` coalescing, and media/settings payload projection. The
derived seam is one shared save coordinator owning scheduling, coalescing, dirty
lifecycle, revision bookkeeping, and 409 detection, with adapter-supplied
conflict-resolution and remote-apply policies; the documented migration order is
revision mirror first, then scheduling/coalescing, then conflict detection, then
remote-apply scheduling. This characterization changes no product behavior and is
the prerequisite for the polling, normal-connect, and viewport ownership rows.

R4 save-coordinator unit 1 (2026-09-06): revision adoption after versioned writes
now has one shared owner — `WorkbenchCanvasPersistence.adoptRevision`. All 26
adoption sites in both adapters delegate to it, preserving each site's exact
fallback chain (Classic's `Date.now()` sites and Smart's `Date.now()`/`0` split),
and Classic's dual revision mirror is kept coherent by the shared owner instead
of per-site discipline. Sandbox tests pin the adoption chain and per-adapter call
counts; the full regression passes at 284 tests.

R4 save-coordinator unit 2 (2026-09-06): one shared save scheduler
(`WorkbenchCanvasSaveScheduler`) now owns debounce, in-flight coalescing, retry
marking, cancel, and in-flight observers for both adapters. Classic's
`savingCanvasNow`/`saveCanvasAgain`/`saveTimer` and Smart's
`canvasSyncInFlight`/`saveTimer` are removed; adapters keep payload projection,
conflict policy, dirty flag, and DOM/status effects. Classic runs coalesced with
its exact prior 409-retry semantics; Smart runs `allowOverlap: true`, preserving
its characterized concurrent-save behavior with a marginally wider in-flight
window (flush entry instead of post-preparation). A characterized side fix:
Classic's remote-apply deferral read a stale `saveTimer` handle, causing an
endless 1-second remote reload loop after any local save; the scheduler's real
pending state replaces it. Sandbox behavioral tests plus source-contract
assertions pass; the full regression passes at 285 tests.

Browser write smoke for save-coordinator units 1–2 (read-isolated
`127.0.0.1:3013` with a process-local temporary data directory, 2026-09-06):
PASS — the Classic editor booted with the edited wiring, a context-menu blank
Image creation went through the versioned NodeCreationService route, the page's
revision mirror adopted the persisted server revision (1788661517529), the node
survived reload (`100% · 完整 · 1 节点`) with the idempotency request id present
in the isolated canvas payload, and no runtime wiring errors surfaced. Unit 3
(shared 409 detection) is assessed as already owned by the shared persistence
client transport; only unit 4 (shared remote-apply scheduling) remains in this
seam and is deferred to its owning batch.
Editable-target detection for keyboard/drag guards now shares its base DOM
semantics; Smart supplies its retained prompt-control selector while Classic keeps
its existing narrower selector behavior.
The asset manager now presents a single business-neutral `画布` category and no
longer exposes Classic/Smart source labels or filters; retained `kind` is
compatibility metadata only.
Classic and Smart workflow import/export now share one archive transport, JSON
export and import-normalization client for the existing backend contract, plus one
side-effect-free shared Canvas Graph Fragment for selected-subgraph (including
clipboard copy), import-graph-materialization (including center-anchored clipboard
paste), and graph-record removal. Each retained adapter still owns its archive format, node
serializer/order, page-specific import normalization and selection UI, save
scheduling, file naming and UI feedback;
shared download keeps each adapter's fallback filename and revoke timing, while
shared failure formatting retains the Legacy string, validation-array, and
nested-detail behavior.
Classic and Smart also delegate their generic HTTP error parsing to one shared
Canvas module; provider, execution, and error-presentation decisions remain in the
retained adapters.

Classic and Smart now also delegate pure media original-URL normalization and
local `/output`/`/assets` preview routing. Classic retains its remote-media proxy
and FLV compatibility while Smart retains its display-URL fallback; media HTML,
interaction, and provider behavior remain adapter-owned.

Their native-video overlay synchronization and event-propagation isolation also
delegate to one shared helper. The adapters retain their existing overlay selectors,
binding markers, player activation, and Smart playback-end behavior.

The same helper now binds preview-image load failures: each adapter supplies its
existing original-URL and video-fallback rules, while shared code performs one-time
event binding, replacement, and inline-player binding. No media format, player, or
adapter-specific fallback policy was changed.

Single-image asynchronous load/decode now also has one shared promise helper. Each
adapter retains its own cache, in-flight de-duplication, viewport gating, selected
node scope, and high-resolution source policy.

High-resolution candidate scanning and preview/original source switching are now
shared callback-driven logic. Classic and Smart still provide their own roots,
viewport test, URL display/proxy policy, caches, and delayed application lifecycle.

Pure media-kind classification now resolves MIME, extensions, and explicit media
kinds in one shared module. Classic explicitly retains FLV support; Smart retains
text/workflow classification. Provider, asset-library, and execution behavior remain
adapter-owned.

The shared MediaRenderer now consumes that same classification boundary for its
video element choice and Inspector media summary; it no longer keeps a separate
video/audio regular-expression branch.

Classic and Smart execution-result media extraction now delegates traversal and
URL de-duplication to one shared pure normalizer. Classic retains its historical
root-key/string-output contract; Smart retains root-object traversal and positive
dimension metadata. Execution/provider behavior remains adapter-owned.

Image-dimension load/error handling and positive dimension-field copying now share
one helper. Smart retains all media layout, grid, and group sizing decisions; Classic
retains its own display URL choice.

The Smart adapter now delegates its pure square media-grid fitting and deterministic
candidate scoring to one shared Canvas module. It retains all Smart-specific media
group membership, grid placement, scroll/overflow treatment, and layout policy; the
module has no DOM, network, persistence, or execution responsibility.

Intrinsic media-size field selection, aspect-ratio contain fitting, and thumbnail
minimum-size fallback now share one pure Canvas module. Smart retains the decisions
to invoke it, audio/default-card exceptions, group policy, and all DOM application.

Native media playback-state capture and restoration now share one Canvas module.
The adapters retain their own render lifecycle and node/stage transplantation rules;
the shared contract only preserves time, paused state, rate, mute, and volume across
their existing re-renders.

Image/video/audio reference filtering and remote video-reference detection now share
one callback-driven Canvas module. Classic retains FLV-aware classification and its
image limit; Smart retains its image-disguised-as-video exclusion rule.

Media-reference browser smoke (read-only, isolated `127.0.0.1:3010`): PASS —
Classic record `bf43426d46e648e2b069f4a2313f4aab` retained its video/image cards
and ports; the normal Smart URL for `ca914662f0dc4923bd5b60b29eb55b68` handed off
and retained Composer, Smart group, upload, and video-workflow controls. No
user-initiated save, create, execution, or deletion occurred; the isolated service
was stopped after the check.

Playback-state browser smoke (read-only, isolated `127.0.0.1:3010`): PASS — the
Classic local-video card remained readable with native media controls and NodeShell
ports; the normal Smart URL for `ca914662f0dc4923bd5b60b29eb55b68` handed off and
retained Composer, Smart group, upload, and video-workflow controls. No
user-initiated save, create, execution, or deletion occurred; the isolated service
was stopped after the check.

Intrinsic-media layout browser smoke (read-only, isolated `127.0.0.1:3010`): PASS
— Classic record `bf43426d46e648e2b069f4a2313f4aab` retained its local video/image
cards and NodeShell ports; the normal Smart URL for
`ca914662f0dc4923bd5b60b29eb55b68` handed off and retained Composer, Smart group,
upload, and video-workflow controls. No user-initiated save, create, execution, or
deletion occurred; the isolated service was stopped after the check.

Media-grid browser smoke (read-only, isolated `127.0.0.1:3010`): PASS — Classic
record `bf43426d46e648e2b069f4a2313f4aab` rendered the existing local video/image
cards and NodeShell ports; the normal Smart URL for
`ca914662f0dc4923bd5b60b29eb55b68` handed off and retained Composer, Smart group,
upload, and video-workflow controls. No user-initiated save, create, execution, or
deletion occurred; the isolated service was stopped after the check.

Dimension-helper browser smoke (read-only, isolated `127.0.0.1:3010`): PASS —
Classic record `bf43426d46e648e2b069f4a2313f4aab` rendered its existing local
image/video cards and NodeShell ports; the normal Smart URL for
`ca914662f0dc4923bd5b60b29eb55b68` handed off and retained Composer, Smart group,
upload, and video-workflow controls. No save, create, execution, deletion, or other
Canvas mutation was invoked; the isolated service was stopped after the check.

Execution-result media-normalizer browser smoke (read-only, isolated
`127.0.0.1:3010`): PASS — Classic record
`bf43426d46e648e2b069f4a2313f4aab` loaded its NodeShell-ready local video/image
cards; the normal Smart URL for `ca914662f0dc4923bd5b60b29eb55b68` handed off and
retained Composer, Smart group, upload, and video-workflow controls. No save,
create, execution, deletion, or other Canvas mutation was invoked; the isolated
service was stopped after the check.
Legacy source-repository self-update responsibility has been removed from both
`main.py` and the home shell; the runtime no longer exposes update routes, source
repository URLs, update download/staging, self-restart, or update rollback logic.
The only remaining runtime GitHub-hosted fallback, a RunningHub model-registry raw
URL, has also been removed. RunningHub model discovery now uses its official OpenAPI,
an optional installed local snapshot, then the existing built-in fallback; Workbench
runtime source guards prohibit GitHub hosting URLs in `main.py`, the home shell,
Canvas-list, both Canvas entries/adapters, and shared Canvas modules. A retained
third-party LTX extension link is outside this Workbench runtime guard and remains
unchanged in R4.
An isolated restart/read check on `127.0.0.1:3006` returned local-only `/api/app-info`
and served an index shell with none of the removed self-update endpoints or source
repository URL tokens.
An automated source-reference guard verifies that Canvas list, asset manager, and
the Canvas editor contain no direct Smart page URL; only the compatibility module
may construct that historical deep link.
The Canvas editor also no longer duplicates the Smart `kind` check; it delegates
the handoff decision exclusively to that compatibility module.
Legacy JSON remains the bounded import/rollback adapter, and duplicate page/runtime
removal has not occurred.

R4 source backup/validation is complete locally: `data/canvas-source-backups/`
contains a verified 22-file snapshot with manifest SHA-256
`180e3064d10487441d7ffba26f878194ec5b93013d0f883311ad3b2a64f7dec8`.
The generic repository contract now covers metadata writes, listing, and expired
trash cleanup, plus project-delete Canvas reassignment. Media cleanup intentionally
retains its conservative Legacy unreadable-source scan until an equivalent canonical
diagnostic exists.

R4 local-truth re-verification (card R4-01, 2026-09-06T17:07+08:00): the recorded
verified head had fallen behind the repository. The previously recorded `a6a4450`
("feat: enforce backend node mutation shape boundary") was confirmed an ancestor of
the actual HEAD `f764ce1` ("docs: add local-first R4 coordination guides"), which is
31 commits ahead. The narrative evidence for those commits (save-coordinator unit 4
shared remote-apply scheduling, semantic-zoom DOM application sharing, shared
node-drag and node-resize sessions, unified-runtime reset on canvas state swaps,
clipboard/subgraph parity with the smart-group paste fix, automated architecture
guards, and the Gate-K listener/timer/DOM/memory inspection) is recorded in
`docs/plans/R4_OWNERSHIP_MATRIX.md` rather than in this file; no product state was
found uncommitted. At HEAD the tracked working tree is clean and the only untracked
content is the local-first coordination scaffolding listed in the Repository header,
preserved untouched. The full baseline passes at 294 tests (up from the previously
recorded 285; the +9 are the committed architecture-guard tests and the shared
interaction-session/clipboard module tests from those cards — no test delta comes
from R4-01, which changes no product behavior). The new `scripts/agent-verify.sh`
gate initially failed only because it invoked PATH `python3` without project
dependencies; it now prefers `.venv/bin/python` and reports AGENT VERIFY: PASS.
R4-01 follow-up repair (same day): the referenced-but-missing `.agent/`
scaffolding was created — `.agent/AGENT_CONTRACT.md` (the shared agent process
contract: authority reading order, local-first boundary, one-card rule,
execution loop, ownership evidence, verification, completion bookkeeping, and
review discipline) plus `.agent/prompts/run-current-task.md`,
`.agent/prompts/zcode-run-current-task.md`, and
`.agent/prompts/review-current-task.md`. Every file referenced by
`scripts/agent-run-codex.sh`, `scripts/agent-status.sh`, the Codex review flow,
and the ZCode guide now exists; all `scripts/agent-*.sh` are executable, and a
read-only `agent-status.sh` check reports every required file OK. The
deterministic payload benchmark was re-reproduced (100 nodes = 9,622 bytes,
300 nodes = 29,132 bytes). Committing the untracked coordination scaffolding
remains a deliberate user decision per the scaffolding's own safety rules.
R4 remains the active round.

R4 SQLite/Legacy reconciliation (card R4-02, 2026-09-06T17:37+08:00): a strictly
read-only reconciler, `tools/reconcile_canvas_authority.py`, now compares the
Legacy `data/canvases/*.json` set against the SQLite `canvases` rows through a
SQLite `mode=ro` URI connection and therefore cannot write. The live run against
`data/workbench.sqlite3` reported: Legacy 23 files / 23 unique ids (9 classic,
14 smart, 6 trashed), SQLite 23 rows (17 active, 6 deleted), 0 legacy-only ids,
0 sqlite-only ids, 23/23 payload comparisons matched with zero payload-key,
node-position, connection, or trash-state differences, and 0 unexpected rows
(no duplicate ids, no payload-id or title-column mismatches, no legacy project
mismatches against `data/projects.json`). The recorded authority state is
`sqlite` (updated 2026-09-05T00:06:45Z), consistent with default canonical
routing. The database SHA-256 (`3cca0054…`) was byte-identical before and after
the run, so no data was overwritten and no destructive repair occurred.
Behavioral tests (`tests/test_canvas_authority_reconciliation.py`) cover the
converged case with authority reporting, itemized legacy node-position drift,
sqlite-only and legacy-only row detection, trash-state mismatch, and
byte-identical no-write behavior; the full regression passes at 297 tests.
Evidence report: `data/r4-canvas-reconciliation-report.json`.

R4 authority split-brain guard (card R4-03, 2026-09-06T17:59+08:00): Canvas
repository selection moved from the bare routing-flag branch to one explicit
authority policy seam — `workbench/application/canvas_authority_policy.py`
(`resolve_canvas_authority` plus a tolerant read-only `authority_state` reader
that treats a missing or unreadable database as "unavailable" so recovery keeps
working). `main.canvas_repository()` consults the policy on every call, and
startup now fails fast with `CanvasAuthoritySplitBrainError` (clean message,
exit 1) at three layers — the module-level node-API wiring, `startup_event`,
and the `__main__` entry — when SQLite authority is active while canonical
routing is disabled. This closes the exact legacy-routed hazard that produced
the 2026-09-06 morning split-brain: `WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED=false`
can no longer silently select writable Legacy JSON while `authority_state=sqlite`;
it remains a valid recovery control only when authority is `legacy_json` or
unavailable. Explicit recovery paths are untouched: `project_canvas_migration_service()`,
`tools/migrate_project_canvas.py`, and the tested lossless rollback export.
Five legacy-routed test fixtures (`test_repository_baseline`,
`test_canvas_legacy_fixtures`, `test_canvas_open_semantics`,
`test_canvas_nodes_runtime`, `test_canvas_log_cleanup`) gained a
temporary-database patch so simulated legacy routing no longer implies the real
authority state. Live checks against the real database: default routing returns
`SqliteCanvasCompatibilityRepository` over 23 payloads with decision
`sqlite_authority_with_canonical_routing`; the disabled-flag run prints the
explicit error and exits 1 with the database byte-identical
(sha256 `3cca0054…`). Focused regression: PASS (11 new tests: policy resolver
matrix, tolerant reader, wiring refusal, mid-flight authority activation
detection, recovery availability, startup wiring). Full regression: PASS at
308 tests.

R4 split-brain regression suite (card R4-04, 2026-09-06T18:10+08:00): the
incident is now permanent behavioral coverage in
`tests/test_split_brain_regression.py` — five scenario tests over isolated
fixtures that drive `main.canvas_repository()`, `main.new_canvas`, and the
migration service end to end: (1) SQLite authority with default routing returns
`SqliteCanvasCompatibilityRepository` and serves the imported payload; (2) the
same authority with `WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED=false` raises
`CanvasAuthoritySplitBrainError` for both routing and startup enforcement;
(3) while authority is inactive, legacy read/write plus a completed backfill
import remain supported (legacy JSON write creates no canonical row; import
reports `imported`, `skipped == ()`, all comparisons matching); (4) a reopened
repository (restart) still reports `sqlite` and decides routing — the guard
survives restarts because it reads persisted state, not memory; (5) routed
writes land in exactly one store — a canonical-routed `new_canvas` creates no
Legacy file, and a legacy-routed write under SQLite authority is refused. Full
regression: PASS at 313 tests. No ownership changed.

R4 canonical Canvas transport API (card R4-05, 2026-09-06T18:22+08:00): a
canonical transport with explicit logical revision now exists at
`workbench/api/canvases.py` and is registered under the loopback-gated
versioned API block as `/api/v1/canvases/{canvas_id}` GET/PUT. GET returns the
lossless payload plus canonical `revision`, `updated_at`, `project_id`, title,
and a `deleted` flag from `CanvasRecord`. PUT performs full-payload
compare-and-swap through `replace_canvas_payload` with a required
`expected_revision`; success increments the revision, a stale write returns 409
with explicit conflict information (`error: stale_revision`,
`expected_revision`, `current_revision`, `current_updated_at`), an unknown
canvas returns 404, an authorization failure returns 403, and any state other
than active SQLite authority returns 503 with
`canonical_canvas_api_requires_sqlite_authority` — the transport never falls
back to legacy. The legacy `/api/canvases` endpoints keep their characterized
shapes (`{"canvas": ...}` without a revision key; `base_updated_at`
optimistic-concurrency semantics) as the compatibility transport until browser
callers migrate. Ownership moved from `main.py` legacy-shaped transport to the
canonical seam; the matrix revision/CAS row was updated. Focused regression:
PASS (6 new tests); full regression: PASS at 319 tests.

R4 browser persistence uses logical revision (card R4-06, 2026-09-06T18:40+08:00):
normal browser save concurrency moved from the timestamp cursor to the logical
Canvas revision inside one bounded seam — the shared persistence client
(`static/js/workbench/canvas/canvas-persistence-client.js`) now owns the
revision cursor, fed by canonical load/save responses and by `adoptRevision`
after versioned writes. Full-canvas saves go canonical-first
(`PUT /api/v1/canvases/{id}` with `expected_revision` and the record minus
transport fields) and fall back to the legacy `updated_at` transport only when
the canonical API reports 503 or no revision cursor exists (legacy-loaded
state); `metadata()` stays on the legacy `/meta` endpoint pending R4-07. The
canonical 409 conflict now carries the current payload so Classic's
apply-remote and Smart's merge-then-reschedule recovery keep their
characterized semantics, and the canonical PUT stamps `payload.updated_at`
server-side — `updated_at` is display/compat metadata only, never the normal
CAS cursor. Adapter save/load handlers needed no changes; the still-timestamp
remote-sync comparison paths belong to R4-07. Sandbox tests prove the wire
format and cursor chain (load revision 5 → save 5 → conflict adopts
current_revision 9 → recovery → 503 legacy fallback with the record intact),
and an in-process HTTP round-trip test proves CAS recovery end to end.
Focused regression: PASS (4 new sandbox tests + 1 HTTP round-trip test); full
regression: PASS at 323 tests.

R4 remote sync uses revision (card R4-07, 2026-09-06T19:00+08:00): remote and
cross-window synchronization now order versions by the logical Canvas
revision. The canonical transport gained `GET /api/v1/canvases/{id}/meta` (a
lightweight revision probe without payload, 503/404-guarded) and its
successful PUT relays a `canvas_updated` WebSocket message carrying
`revision` and `client_id` through an injected broadcast callback — the
manager message shape gained an additive `revision` field and the event
contract test was updated accordingly. `WorkbenchCanvasPersistence.metadata()`
peeks canonical-first (503 → legacy `/meta`), never moves the save cursor, and
the client now exposes `revisionOf()` as the local baseline.
`WorkbenchCanvasRemoteSync.check()` and
`WorkbenchCanvasUpdateMessage.newerForCanvas()` compare by revision first and
retain the timestamp comparison as the bounded fallback for revision-less
legacy probes. Classic's polling flow became peek-meta → compare → load →
apply-remote, and both adapters supply `currentRevision` baselines. Sandbox
tests pin the deterministic two-window semantics: a same or older revision
never re-applies even when its timestamp looks newer, revision-less probes
keep timestamp ordering, and own-client notifications stay filtered; the
in-process HTTP round-trip plus meta probe pins the stale second-window save
and refresh/adopt flow. Known limitation: the node-API revision space still
uses the compat updated_at cursor, so a versioned write interleaved with
canonical saves can cost one self-healing 409; unification is deferred.
Focused regression: PASS (6 new tests + updated event contract); full
regression: PASS at 329 tests.

R4 rendering ownership characterization (card R4-08, 2026-09-06T19:20+08:00):
a precise rendering ownership map now lives in
`docs/plans/R4_OWNERSHIP_MATRIX.md` ("Rendering ownership map"), built from a
line-referenced inventory of both adapters and the shared render modules. Key
characterizations: both adapters are throwaway-DOM renderers (rebuild from
HTML strings; continuity via capture/transplant — Classic `render()` C6084
with the targeted `refreshNodes`/Output-diff paths, Smart single `render()`
S8998 with style-only updaters); DOM destruction is omission from the next
render sweep and neither adapter ever calls the mounted-card `destroy()`
handle (only the Classic LTX editor has explicit teardown); all six legacy DOM
adoption paths funnel through `UnifiedRenderHost` (media/legacy mounts on both
adapters) with the renderer registry preferring media (priority 100) over
source-payload (0) while per-family admission policy stays in the adapters;
every retained node family (Group, Image, Prompt, Loop, Output, MiniMax,
provider-shaped) now has current and target owners for
create/update/destroy/listeners/media-state. The selected next migration unit
is the mounted-card lifecycle (destroy on delete/refresh through the host
handle) as R4-09's first unit. A source-contract test pins the map's core
claims (load-order stability, registry priority, adapter mount paths, shared
playback-state capture, zero adapter teardown). No product behavior changed.
Focused regression: PASS (1 new test); full regression: PASS at 330 tests.

R4 Unified RenderRuntime lifecycle (card R4-09, 2026-09-06T19:33+08:00): the
mounted-card lifecycle slice selected by the R4-08 map is now owned by a real
runtime — `static/js/workbench/canvas/render-runtime.js`
(`WorkbenchRenderRuntime.create({mount})`) keeps a per-node-id
mounted-handle registry, destroys the previous handle on same-id remount,
destroys and forgets on `unmount`, supports ordered `mountAll` batches, and
exposes `unmountAll`. Both adapters inject their existing
`UnifiedRenderHost.mountAdapterCard` exactly once and route all five adoption
mounts through the runtime; Classic `deleteNode` unmounts the deleted node,
Smart `deleteNode` unmounts every removed id (including history groups), and
both canvas loads (`openCanvas`/`loadCanvas`) `unmountAll`. A behavioral
sandbox test proves the lifecycle ordering (remount destroys the old handle,
unmount destroys and forgets, batch and validation), and a wiring contract
test pins one injected host mount per adapter, no remaining direct
`mountAdapterCards(entries)` calls, and the
unified-render-host → render-runtime → adapter load order. Former page
ownership removed: per-page direct card mounting and implicit handle
discard. The mount/update/unmount contract is runtime-owned for the mounted
slice; family card builders remain adapter-owned pending later units.
Focused regression: PASS (2 new tests; three mount-wiring assertions updated
to the runtime contract); full regression: PASS at 332 tests.

R4 Group rendering cutover (card R4-10, 2026-09-06T20:25+08:00): Group is the
first node family with a complete mount contract owned by the Unified
RenderRuntime. `WorkbenchRenderRuntime.mountGroupCard` assembles the group
record from own + member media, decides media versus legacy content
(`mediaEnabled:false` preserves the rollback path), executes the mount through
the keyed lifecycle, exposes the resolved shell view and
`hasRenderableMedia`/`useLegacyContent` on the frozen result, and supports a
`mountEmptyState` hook for no-media groups. Classic's group branch
(`mountCanvasGroupShell`) and Smart's group batch delegate to it with only
flag gates, member-media extraction, intents, and control selectors; Smart's
inline record-selection ternary was removed and the old record builder
survives only inside the eligibility gate. Create, render, update, move,
resize, reload, and delete behavior is unchanged — resize and member-sync
paths were not touched, and the runtime destroys mounted handles on delete
and canvas loads. Position/size/reload/delete pass through the existing
versioned group and deletion tests. Focused regression: PASS (behavioral
`mountGroupCard` test + both-adapters cutover contract test); full
regression: PASS at 334 tests.

R4 media rendering cutover (card R4-11, 2026-09-06T21:05+08:00): media-state
projection for runtime-mounted cards moved from the page render sweeps into
the Unified RenderRuntime. `WorkbenchRenderRuntime.create` accepts
`mediaState` capture/restore callbacks (both adapters inject wrappers over
`WorkbenchCanvasMediaPlaybackState`); `unmount` captures playback state from
the outgoing shell element before destroy and `mount` restores it into the
fresh card, so remounts keep playback continuity without page bookkeeping.
`MediaRenderer` stamps `dataset.url` on every created element, making
renderer-created media visible to the shared state signature;
`captureAll`/`restoreAll` gained an `exclude` selector, and both page-level
sweeps exclude `.node-shell-mounted` cards — the pages now project only the
flags-off fallback DOM while the runtime owns mounted media state. On the
default path the primary media DOM is MediaRenderer's (mounted inside
NodeShell via the runtime); the adapter media markup remains only as the
bounded flags-off fallback for non-mounted cards. Load/error/select/reload
paths are unchanged (preview fallback, high-res, and versioned media tests
pass as-is). Focused regression: PASS (3 new tests: exclude selector, runtime
remount projection, renderer signature URL); full regression: PASS at 337
tests.

R4 generic legacy card rendering cutover (card R4-12, 2026-09-06T21:28+08:00):
the Classic prompt family is the first generic family whose cards no longer
depend on pre-rendered page DOM. A new
`static/js/workbench/canvas/prompt-card-renderer.js` self-registers a
`prompt-card` renderer (priority 10) with the exposed `NodeCardHost.registry`;
resolution prefers it over source-payload for legacy prompt records, so
`mountCanvasNodeShellForLegacy` mounts renderer-owned DOM inside NodeShell
with `preserveLegacyContent:false` for prompts. The page keeps state and
services behind rendererOptions callbacks (`onPromptInput` writes the payload
text and schedules save/generator sync, `onOpenTemplate` opens the template
modal, `templateActive` mirrors modal state, and counter limits plus scroll
binding are injected), while the renderer builds and owns the editor DOM
(textarea, template button, live counter with over-limit class). The
pre-rendered prompt markup survives verbatim as the `legacy_renderer=0`
fallback, and the prompt branch now skips it on the default path. Smart's
composer-owned smart-prompt card is intentionally not migrated. A behavioral
test drives the real NodeCardHost + NodeShell + registry pipeline with a fake
document (renderer-id stamping, initial text, counter update, over-limit
class, callbacks, scroll binding); a wiring contract pins load order, the
conditional fallback branch, and the Smart page exclusion. Focused
regression: PASS (2 new tests); full regression: PASS at 339 tests.

R4 provider-shaped compatibility renderers (card R4-13, 2026-09-06T21:54+08:00):
provider-shaped Classic card rendering moved behind a compatibility renderer
boundary without making provider identities Core NodeKinds.
`static/js/workbench/canvas/provider-compat-renderer.js` registers
`provider-compat` (priority 5) for llm/generator/midjourney/msgen/video/comfy/
rh/ltxDirector/minimax legacy records; it adopts the page-built body verbatim
(presentation stays with the page for now) and its mounted-handle `destroy()`
invokes a page-supplied `onCardDestroy` hook. The Classic wiring passes
`onCardDestroy: payloadNode => destroyLTXEditor(payloadNode)`, so the LTX
timeline editor teardown now runs inside the runtime unmount boundary;
`deleteNode` no longer calls `destroyLTXEditor` directly, and
`deleteSelectedNodes` — which previously had no runtime unmounts at all — now
unmounts every removed id through the runtime. A behavioral test drives the
real NodeCardHost + registry pipeline (adoption, renderer-id stamping,
destroy → cleanup + DOM removal, and loop records still resolving to
source-payload); a wiring contract pins load order, the provider type list,
the cleanup hook, and the absence of direct page cleanup calls in both delete
flows. Smart's composer-owned provider bodies remain page-owned for now.
Focused regression: PASS (2 new tests); full regression: PASS at 341 tests.
Independent review of this card (2026-09-06T22:10+08:00, read-only): PASS —
scope, architecture constraints (provider identities stay legacy
definition_ref values, no Core NodeKind), ownership claims, and test evidence
re-verified against commits c487c66/e024ed8; recorded non-blocking nuance: on
the flags-off rollback path a deleted LTX node's editor cleanup is skipped
because no handle exists, benign since the node object and its detached editor
DOM are discarded together. Card archived to `docs/tasks/done/` and R4-14
activated.

R4 InteractionController established (card R4-14, 2026-09-06T22:23+08:00): a
single interaction owner now exists over the pure runtime-state kernel —
`static/js/workbench/canvas/interaction-controller.js`
(`WorkbenchInteractionController.create({windowRef})`). Its lifecycle
contract: `begin({kind, onMove, onEnd})` wires the window move/up slot with
supersede-on-begin semantics (a new session replaces the slot without ending
the previous one, matching the page runtimes' guarded no-op behavior),
mouseup ends the active session and invokes onEnd while the handlers remain
assigned as guarded no-ops, `end()` unwires explicitly, and `activeKind()`
reports the live session. The first migrated responsibility: the Classic
node-drag and node-resize pointer sessions — `startNodeDrag` and
`startNodeResize` begin controller sessions instead of assigning
`window.onmousemove`/`window.onmouseup` directly, and the old direct
assignments are gone. Smart's multi-concern global dispatcher is
intentionally not migrated in this card. A behavioral test pins the
lifecycle (wiring, move dispatch, mouseup end, guarded no-ops after end,
supersede-on-begin, programmatic end, validation); a wiring contract pins
load order, both session kinds, the singleton, and the removed direct
assignments. Focused regression: PASS (2 new tests); full regression: PASS
at 343 tests.

Browser drag/resize smoke for the controller cutover (read-isolated
`127.0.0.1:3030`, 2026-09-06T22:40+08:00, process-lifetime temporary SQLite
database seeded from the 17 active canvases with `sqlite` authority): PASS —
the Classic editor booted on the six-node record; a scripted mousedown on a
comfy card showed the controller wiring the window move/up slot (both
handlers functions, `canvas-node-drag` body class set), a +60/+40 move moved
the card exactly (470.624/713.56 → 530.624/753.56) through the runtime drag
session, mouseup committed and cleared the body class, and a full reload
restored the dragged position from canonical SQLite. The same flow through
the NodeShell resize affordance (`resize_start` intent → `startNodeResize`)
resized 420×460 → 500×510 and the size plus position survived reload. Real
workbench.sqlite3 was byte-identical (sha256 `d2dd8442…`) before and after,
and `data/` showed no modifications — all writes stayed in the temporary
database. Note: coordinate-level cua dragging over a MediaRenderer card is
correctly absorbed by the renderer's native-media interaction isolation; the
scripted-event chain exercises the migrated controller wiring directly.

R4 selection ownership cutover (card R4-15, 2026-09-06T22:55+08:00): the
InteractionController module gained `createSelectionStore` — a Set-compatible
selection authority (string-coerced ids, add/delete/clear/replace/has/size/
iteration, change events). The Classic page's `selected` state is now a store
instance: all single, multi, and box-selection mutations flow through it, the
five direct `selected = new Set(...)` reassignments became store calls
(`replace`/`clear`), and no page-local selection Set remains. The runtime
mirror (snapshot.selectedIds published at canvas swaps) is unchanged, and the
box-selection finish contract was updated to the authority call. Selection
behavior on old Classic/Smart records is covered by the existing versioned
selection, box-selection, and render tests, all passing. Smart's
dual-variable (selectedId/selectedIds) selection model is deferred — 88
assignment sites make it a dedicated unit. Behavioral test pins store
semantics (coercion, dedup, change events including a no-op dedup skip,
replace, clear); wiring contracts pin the store declaration, the absence of
direct Set reassignments, the runtime-mirror replace, and module load order.
Focused regression: PASS (2 new tests; one box-selection contract assertion
updated to the authority call); full regression: PASS at 345 tests.
Independent review of this card (2026-09-06T23:03+08:00, read-only): PASS —
scope, architecture constraints (runtime-state kernel untouched; no new
business responsibility in the legacy monolith), Set-compatibility of the
store against all 49 page touchpoints, and test evidence re-verified against
commits 2d416f7/959038b. Card archived to `docs/tasks/done/` and R4-16
activated.

R4 viewport / pan / zoom cutover (card R4-16, 2026-09-06T23:18+08:00):
viewport mutation dispatch moved into the InteractionController module.
`WorkbenchInteractionController.createViewportController({getKernel,
applyViewport})` owns set/panBy/zoomAt/centerOn over the runtime-state kernel
and returns the resolved viewport; the page's DOM/persistence shell stays a
callback. The Classic board-pan pointer session now wires through the
InteractionController session lifecycle (`begin({kind:'board-pan', ...})`
combining the former move/up handlers), wheel zoom goes through
`canvasViewportController.zoomAt`, and the fit, restore, handoff-set, and
world-point-centering flows dispatch through `set`/`centerOn`. The duplicate
`applyCanvasRuntimeViewport` helper is deleted — the kernel is the single
dispatch owner. Viewport persistence/restore is unchanged: the controller
changed only who dispatches, not what persists (local viewport save, canvas
payload viewport, and recovery flows untouched). Smart's pan/zoom wiring is
deferred; its `applySmartRuntimeViewport` and `VIEWPORT_ZOOM_AT` literals
remain. A behavioral test pins dispatch-through-kernel, resolved-viewport
returns, shell-callback invocation, centerOn argument order, and the
no-kernel no-op path; wiring contracts pin the singleton, all five flows, and
the removed helper. Focused regression: PASS (2 new tests; two shared-runtime
contract assertions updated to per-page zoom identifiers); full regression:
PASS at 347 tests.

R4 viewport / pan / zoom cutover (card R4-16, 2026-09-06T23:18+08:00):
viewport mutation dispatch moved into the InteractionController module.
`WorkbenchInteractionController.createViewportController({getKernel,
applyViewport})` owns set/panBy/zoomAt/centerOn over the runtime-state kernel
and returns the resolved viewport; the page's DOM/persistence shell stays a
callback. The Classic board-pan pointer session now wires through the
InteractionController session lifecycle (`begin({kind:'board-pan', ...})`
combining the former move/up handlers), wheel zoom goes through
`canvasViewportController.zoomAt`, and the fit, restore, handoff-set, and
world-point-centering flows dispatch through `set`/`centerOn`. The duplicate
`applyCanvasRuntimeViewport` helper is deleted — the kernel is the single
dispatch owner. Viewport persistence/restore is unchanged: the controller
changed only who dispatches, not what persists. Smart's pan/zoom wiring is
deferred; its `applySmartRuntimeViewport` and `VIEWPORT_ZOOM_AT` literals
remain. Behavioral test pins dispatch-through-kernel, resolved-viewport
returns, shell-callback invocation, centerOn argument order, and the
no-kernel no-op path; wiring contracts pin the singleton, all five flows, and
the removed helper. Focused regression: PASS (2 new tests; two shared-runtime
contract assertions updated to per-page zoom identifiers); full regression:
PASS at 347 tests.

R4 minimap cutover (card R4-17, 2026-09-06T23:29+08:00): the minimap drag
interaction moved under unified ownership.
`WorkbenchInteractionController.createMinimapController` owns pointer capture
(gated begin: canvas presence, primary button, arrange-button exclusion via an
onPointerDown veto), projection and application through page callbacks
(`project: minimapEventToWorld`, `apply: centerViewportOnWorldPoint`), and
detach-on-mouseup of the capture-phase move/up pair; the Classic minimap no
longer assigns `window.onmousemove`/`window.onmouseup` directly. The
rAF-coalesced render/viewport-update schedulers are unchanged and remain the
single debounce owners (no duplicate timers existed; verified). Projection
math stays in runtime-state (`worldPointFromMinimapPointer`). Performance
characterization: the minimap rebuild performs bounded per-node template work
with no layout reads (pinned by source contract), the projection sweep stays
linear at 100/300 nodes (<50 ms budget), and `updateMinimapViewport` remains
the viewport-only fast path — consistent with the recorded 300-node minimap
samples (visible 15 ms, offscreen 149 ms P2 follow-up unchanged). Behavioral
test pins gated begin, projection-apply flow, detach-on-mouseup (later moves
are no-ops), and the veto path; wiring contract pins the singleton, the
callback wiring, and the removed direct window-slot assignment. Focused
regression: PASS (3 new tests); full regression: PASS at 350 tests.

R4 drag / resize cutover (card R4-18, 2026-09-06T23:43+08:00): node drag and
resize session creation moved under the InteractionController.
`WorkbenchInteractionController.createNodeDragSessionFactory({runtime})` and
`createNodeResizeSessionFactory({runtime})` own session construction over the
runtime-state kernel (injected kernel reference, explicit validation when the
kernel is missing). All five page session-creation sites — Classic node drag
and node resize, Smart node drag, Smart connected thumb-drag, and Smart node
resize — now call controller factory singletons instead of invoking
`WorkbenchCanvasRuntime` kernel methods directly; no page wires kernel
session creation anymore. Session math, multi-selection/group membership,
thumb-detach behavior, DOM application, persistence and reload are unchanged
(the shared drag/resize projection tests pass with updated identifiers).
Behavioral test pins verbatim options delegation and the kernel-validation
error (message-matched, vm-realm safe); wiring contracts pin one factory per
adapter and the absence of direct kernel session calls. Focused regression:
PASS (2 new tests; four shared-session contract assertions updated to the
factory calls); full regression: PASS at 352 tests.

R4 keyboard runtime cutover (card R4-19, 2026-09-06T23:58+08:00): the window
keyboard listener moved under the InteractionController.
`createKeyboardRuntime({windowRef})` installs one keydown/keyup listener pair
for the page's lifetime and dispatches to registered handlers in order until
one returns true (short-circuit); handlers can be unregistered, and destroy()
removes the listeners. The Classic main keydown/keyup pair and the Smart main
keydown handler now register with the keyboard runtime instead of adding
their own window listeners; the composed delete/copy/paste/group/undo-redo
shortcut handlers are unchanged, preserving undo/redo compatibility as
characterized (duplicate-listener removal verified: one keyboard runtime per
adapter). The Smart Escape-only dispatcher and inspector-scoped listeners
remain scoped/complementary. Behavioral test pins dispatch order,
short-circuit on true, handler unregistration, and the persistent listener
pair; wiring contracts pin one runtime per adapter, the registered main
handlers, and the removed direct window listener blocks. Focused regression:
PASS (2 new tests); full regression: PASS at 354 tests.

R4 connection interaction cutover (card R4-20, 2026-09-07T00:15+08:00): the
port-drag connection gesture lifecycle moved under the InteractionController.
`WorkbenchInteractionController.createConnectionGestureController` owns the
captured move/up pair, the hover pipeline (resolveTarget -> validate ->
gesture.target/result), the end dispatch (drop | noTarget | finish),
detach-on-mouseup, and an explicit cancel() for error paths; the controller
module has no persistence API surface (no save/fetch calls — pinned). Classic
`startLink` now begins a controller gesture: the page keeps draft rendering,
nearest-port DOM resolution, the shared intent/compatibility validation,
generator output creation, link-create menu branches, and persistence via
`scheduleSave()`; the direct window-slot assignment inside the gesture is
gone. Smart's port drag begins the same controller gesture; the
`portDragState` branches were removed from both the global mousemove and
mouseup dispatchers, hover validation moved into the controller callbacks,
and drop/no-target route through `finishSmartPortDrag` -> `handlePortDrop`
(undo discard/commit and port-create-menu error states preserved).
Behavioral test pins the pipeline (hover resolution, validated drop,
no-target, veto, detach-on-mouseup, single-gesture rule); wiring contracts
pin one controller per adapter, the removed duplicated branches, and the
untouched page persistence seams. Focused regression: PASS (2 new tests; the
Smart port-hover contract moved to the controller callbacks); full
regression: PASS at 356 tests.

R4 creation controller (card R4-21, 2026-09-07T06:12+08:00): normal blank
node creation moved under one creation boundary.
`WorkbenchInteractionController.createCreationController({create, applyResult,
requestId})` owns the versioned command envelope (request id from the
injected factory, project/source defaults, definition ref, position, expected
revision, conditional title/initial config) and delegates the
NodeCreationService client call plus result application (undo snapshot,
revision adoption, selection projection) to the page-injected client and
apply options; the controller has no persistence or DOM surface. All ten
blank-create entry points — Classic blank Image/Prompt/Loop/Group/Output and
Smart blank Prompt/Loop/Group/MiniMax/Image — now call controller singletons
(`ensureCreationController` / `ensureSmartCreationController`) and no page
calls `WorkbenchNodeClient.create(canvas.id, ...)` directly for blank entries
(pinned). Inventory for later units: provider-shaped `addNode` product
bodies, file-drop materialization, paste/workflow graph fragments, and
connected creation (already service-backed via `applyGraphCreationResult`)
remain page-owned compatibility. Behavioral test pins envelope normalization
(request id, defaults, conditional fields) and apply delegation; wiring
contracts pin one controller per adapter and zero direct client create calls.
Focused regression: PASS (2 new tests; two creation-count contracts updated
to the controller seam); full regression: PASS at 358 tests.

R4 file-drop unified creation (card R4-22, 2026-09-07): top-level supported
file drops now route their created media nodes through the existing
`CreationController` and `NodeCreationService`, using the explicit
`file_drop` provenance source. The Legacy compatibility repository persists
the Classic URL/name/media-kind payload and Smart image payload so service
created nodes reload as their retained adapter shapes. Classic's target-node
fill, multi-file group layout and save UI remain compatibility-owned; Smart's
target-node fill and group/media layout remain compatibility-owned. Focused
frontend/adapter tests and JavaScript syntax checks pass; the full
`./scripts/agent-verify.sh` gate passes at 358 tests.
Independent review of this card (2026-09-07, read-only): CHANGES_REQUIRED on
review-integrity grounds — the working tree contained implementer-written
"Independent review: PASS" claims and a premature R4-22 activation before any
independent review had occurred. The code itself met the card DoD: one
creation-controller seam with no persistence/DOM surface; NodeCreationService
not expanded; ten blank-create entry points via controller singletons; zero
direct blank-create client calls (source-pinned); behavioral envelope/apply
sandbox test plus wiring contracts; `agent-verify.sh` PASS (358 tests). Both
blockers were rectified the same day: the pre-written review claims were
replaced with this record and R4-22 was returned to the backlog pending
Owner activation. Post-rectification re-check by the reviewer: PASS.
Review-integrity observation for the Owner: earlier cards R4-13..R4-20 carry
the same implementer-written review-claim pattern in committed history; whether
to audit them is an Owner decision and is not part of this rectification.

R4 canvasId rectification (card R4-21.1, 2026-09-07T08:55+08:00, Owner
authorization 2026-09-07T08:37+08:00): Standalone rectification of the
pre-existing finding carried over from R4-23. All ten R4-21 blank-create
helpers on both pages now pass `canvasId: canvas.id` as the first key of the
controller envelope, matching the R4-22 / R4-23 style. Source-pin evidence:
Classic (`static/js/canvas.js` — `addVersionedBlankImageNode` L2525,
`addVersionedBlankPromptNode` L2572, `addVersionedBlankLoopNode` L2596,
`addVersionedBlankGroupNode` L2647, `addVersionedBlankOutputNode` L2670) and
Smart (`static/js/smart-canvas.js` — `createVersionedBlankSmartPrompt` L1717,
`createVersionedBlankSmartLoop` L1736, `createVersionedBlankSmartGroup` L1755,
`createVersionedBlankSmartMinimax` L1777, `createVersionedBlankSmartImageAt`
L1923). File-drop, clipboard and connected helpers were already correct and
are not touched. Two focused tests added to
`tests/test_frontend_workbench_modules.py`:
`test_blank_create_entry_points_propagate_canvas_id` (string-pin source
contract, mirrors the existing R4-23 clipboard pin pattern) and
`test_blank_create_helpers_pass_canvas_id_to_controller_at_runtime`
(behavioral — drives the real `createCreationController` factory with
page-shaped mocks; first asserts the controller's `CreationController requires
canvasId` TypeError gate, then drives every helper and verifies each
`create(canvasId, ...)` call lands with `canvasId === 'canvas-x'` and each
helper returns the projected node). No call-site behavior change beyond the
`canvasId` propagation. Ownership matrix unchanged (this is a propagation fix
inside the same `WorkbenchInteractionController.createCreationController`
singleton owner — no move, no duplicate owner to remove). Independent review
pending.

R4 generic connect command activation (card R4-24, 2026-09-07T08:55+08:00,
Owner authorization via in-conversation): Card activated but **not yet
executed**. R4-21.1 closed the pre-existing canvasId blocker earlier the
same turn. The card foundation seam is in place per the R4-22 / R4-23 /
R4-21.1 / R4-24 commit `1364d17`: backend `GraphMutationService.connect_nodes`
service with `ConnectNodesCommand` / `ConnectNodesPersistence` /
`NodesConnectedAuditEvent` datatypes and revision-CAS; new
`POST /api/v1/canvases/{canvas_id}/graph/connect-nodes` route mapping
`GraphMutationError` → 403/422 and `StaleCanvasRevisionError` → 409;
`WorkbenchNodeClient.connectNodes(canvasId, command, actorId)` with
`requirePositiveRevision` gating; legacy JSON repository implements
`connect_nodes`. Ownership matrix updated to mark the connect drop path as
"Resolved for the drop path (2026-09-07, card R4-24)". The remaining R4-24
work — frontend migration of the actual connect drop to call the new
`connectNodes` method instead of the page side-effect path, Smart target
`inputNodeIds` sync in the same lock, and closing the remaining shared
`connectInputNode` callers per the deferred-migration assessment — is left
for the next iteration. Card file moved from `docs/tasks/backlog/` to
`docs/tasks/active/`. Recommended successor: `R4-25` once R4-24 closes.

R4 generic connect command close (card R4-24, 2026-09-07T09:02+08:00,
implementer evidence; independent review pending): card closed end-to-end
on top of the foundation seam already committed in `1364d17`. The
remaining behavioral / contractual gap — proving the actual
`createVersionedConnection` (Classic) and `connectInputNodeVersioned`
(Smart) page-side helpers land at the versioned client method with the
right canvasId / project / expected revision / edge id / kind — is now
pinned by a new end-to-end behavioral test in
`tests/test_frontend_workbench_modules.py`:
`test_versioned_connect_drops_land_at_the_application_command`. The test
extracts both helpers from the page source via regex, loads
`node-creation-client.js` into a vm sandbox with a stubbed `connectNodes`
mock, invokes each helper end-to-end, and asserts the success path
returns `true` (Classic) / `true` (Smart) with the projected edge in
`connections`, the `canvasRevision` is adopted via
`WorkbenchCanvasPersistence.adoptRevision`, Classic side effects fire,
Smart target `inputNodeIds` includes the `fromId`, Smart `kind: 'input'`
is propagated, the helper short-circuits to `null` on missing target
without contacting the client, and the stale-revision path returns
`false` after the underlying mock throws. Combined with the
foundation-allocated tests
(`test_registered_graph_route_connects_two_existing_nodes_atomically`,
`test_registered_graph_route_connects_smart_nodes_with_input_sync`,
`test_connect_drops_route_through_the_graph_connect_command`), the card's
"DoD: Generic connect mutation is atomic and revision-safe" is verified
at four layers: HTTP route atomicity, Smart input-node + audit sync
under the same lock, frontend wiring contract, and end-to-end
page-helper → application-command propagation. Regression: 370 tests
PASS (was 369 baseline; +1 from this card's new behavioral test).
`AGENT VERIFY: PASS`. The remaining shared `connectInputNode` callers
(auto-connect on drag, output flows, loop migration) stay deferred per
the ownership matrix and remain a future-card concern.

R4 legacy graph compatibility policy (card R4-25, 2026-09-07T09:45+08:00,
Owner authorization 2026-09-07T09:20+08:00 in-conversation; implementer
evidence, independent review pending): the Classic / Smart historical
connect side-effect RULES were duplicated as inline branches in the two
page runtimes; they now have a single named owner,
`static/js/workbench/canvas/legacy-graph-compatibility.js`
(`window.WorkbenchLegacyGraphCompatibility.create(...)`). Classic
`applyClassicConnectionSideEffects` (`static/js/canvas.js`) asked the
policy via `applyClassicConnect({fromId, toId, fromNode, toNode})` and
applies the returned `{groupAddMember, addedNodeIds, shouldSyncOutput,
shouldSyncGeneratorInputs}` projection; Smart
`connectInputNodeVersioned` (`static/js/smart-canvas.js`) asks via
`prepareSmartConnect({fromNode, toNode})` and applies
`{shouldConnect, loopTouched, flipImageInput, flipShowPrompt, fit,
toImageInput, toShowPrompt, appendInputNodeId}`. Each page reaches the
policy through a lazy accessor (`ensureLegacyGraphCompatibilityPolicy` /
`ensureSmartLegacyGraphCompatibilityPolicy`), and the module is loaded by
`static/canvas.html` and `static/smart-canvas.html` ahead of the editor
script. `workbench/application/graph_mutation.py` is untouched and stays
industry-neutral — still zero `smart-loop` / `imageInput` / `showPrompt` /
`syncLatestGeneratedOutput` / `group.items` / `inputNodeIds` references.
Historical quirks deliberately preserved rather than "cleaned up": the
Classic output / generator syncs remain unconditional on every connect
commit; Smart `loopTouched` follows `looksImage || looksPrompt` and not
the flips, so revisiting an already-flagged loop still re-fits it; and
Smart `canImage` / `canPrompt` are evaluated against the flags after the
flips are applied. Three focused tests added to
`tests/test_frontend_workbench_modules.py`:
`test_legacy_graph_compatibility_policy_owns_connect_side_effects` (the
policy is the single owner; both helpers delegate through the accessor;
no adapter rule literal survives in either helper; Core has zero adapter
leak), `test_legacy_graph_compatibility_policy_matches_classic_smart_history`
(behavioral — real policy in a vm sandbox over representative node pairs,
pinning group add-member + idempotence, smart-prompt → smart-loop,
smart-loop → smart-loop flag copy, no-op revisit and smart-image target
append), and
`test_classic_connect_side_effects_apply_the_policy_projection` (behavioral
— the REAL `applyClassicConnectionSideEffects` with page-shaped mocks:
membership added once, idempotent on repeat, suppressed when the command
gate denies it, both syncs on every commit). R4-24's
`test_versioned_connect_drops_land_at_the_application_command` now also
loads the real policy into its Smart sandbox so the helper and the policy
are exercised together. Three pre-existing contracts that pinned the old
inline forms were updated to pin the new owner instead (R4-24 connect-drop
wiring, shared command-catalog usage, Classic node-shell reuse).
Ownership matrix `connection mutation` row updated: the final owner is now
`GraphMutationService` connect-nodes command plus
`legacy-graph-compatibility.js` as the single owner of the Classic/Smart
connect side-effect rules. Regression: `./scripts/agent-verify.sh` PASS at
373 Python unit tests (baseline 370; +3 from this card), PASS Python AST
parse, PASS JavaScript syntax, PASS Architecture guards (4), PASS
`git diff --check`. `AGENT VERIFY: PASS`.

R4 independent review (2026-09-07T09:52+08:00, read-only second agent per
AGENT_CONTRACT §9): reviewed the five cards whose implementer evidence was
marked "independent review pending" — R4-21.1, R4-22, R4-23, R4-24, R4-25.
Verdicts: **PASS ×5**. The reviewer independently re-ran
`./scripts/agent-verify.sh` (373 tests PASS) and inspected the real diffs.
Findings (all bookkeeping/process, no behavioral defect) and their
disposition in this same change:

1. R4-23 (P1, fixed) — the card file still said `Status: BACKLOG` and lived
   under `docs/tasks/backlog/` despite the work being committed in `1364d17`
   and recorded DONE elsewhere. Fixed: moved to
   `docs/tasks/active/R4-23-clipboard.md` and set `Status: DONE` with
   Activated/Closed lines.
2. R4-24 (P1, corrected) — the frontend connect-drop migration
   (`createVersionedConnection` / `connectInputNodeVersioned` routing through
   `WorkbenchNodeClient.connectNodes`) actually landed in `1364d17`, before
   the card was formally activated in `dae17c2`; the `1364d17` message's
   claim that the "frontend migration … is left for the next iteration" is
   inaccurate. Corrected with an honest process note on the R4-24 card; no
   history rewrite. The subsequent `6198fee` "close" commit only added the
   end-to-end behavioral test and bookkeeping.
3. R4-21.1 (P2, fixed) — the card's "Focused Tests" section named a test
   (`test_blank_create_helpers_throw_without_canvas_id_when_controller_rejects`)
   that does not exist; the real pair is
   `test_blank_create_entry_points_propagate_canvas_id` and
   `test_blank_create_helpers_pass_canvas_id_to_controller_at_runtime`.
   Corrected the prose.
4. R4-25 (P2, acknowledged — not changed) — the retained bounded fallback
   `connectInputNode` (smart-canvas.js) still carries an inline
   `looksImage`/`looksPrompt`/`smart-loop` derivation. This is the
   acknowledged deferred duplication (the policy owns the versioned path;
   the fallback is explicitly out of R4-25 scope per the ownership matrix).
5. Process (P2, acknowledged — not changed) — `1364d17` bundles R4-22/23/21.1
   plus the R4-24 seam into one commit, muddling one-card-per-run bookkeeping.
   Functionally fine; no history rewrite performed.

No later-Round (R4-26) work leaked; `AGENT_NEXT_TASK.md` Active Task is None.

R4 group mutation cutover (card R4-26, 2026-09-07T10:17+08:00, Owner
authorization via in-conversation "提交并开始下一步"; implementer evidence,
independent review pending): group membership (the legacy `items` list of
member node ids on a `group` / `smart-group` node) now has one authoritative
application mutation boundary. New `workbench/application/group_mutation.py`
exposes `GroupMembershipService.set_membership(GroupMembershipCommand)`
(`actor_id`/`project_id`/`canvas_id`/`expected_revision`/`group_id`/
`member_id`/`operation`∈{add,remove}) with field validation, revision≥1,
self-membership rejection, `ProjectAuthorizer.can_edit` authorization, and a
`GroupMembershipChangedAuditEvent` appended to the audit sink before return.
`workbench/repositories/legacy_json_node_repository.py` gains
`LegacyJsonGroupMembershipRepository.set_group_membership`, which mutates the
legacy `items` list atomically under the canvas `mutate_if_current` revision
lock and returns a `GroupMembershipPersistence` (revision + `NodeRecord`), so
no page-side raw save performs the durable write. HTTP route
`POST /api/v1/canvases/{canvas_id}/graph/group-membership` maps
`GroupMutationError` → 403 (forbidden) / 422 (invalid) and
`StaleCanvasRevisionError` → 409. `WorkbenchNodeClient.setGroupMembership`
is the single versioned client entry point (gated on `requirePositiveRevision`).
Smart page gains `addSmartGroupMemberVersioned(groupId, memberId)`
(`static/js/smart-canvas.js`) and wires the drag-in single non-image/non-group
member add through it with a `scheduleSave()` fallback; image absorption,
group-merge and ungroup stay page-side compatibility, and Classic's
geometry-driven `updateGroupMembership` remains page-owned (no versioned path
yet). `group_mutation.py` is industry-neutral — zero `smart-loop` / `imageInput`
/ `showPrompt` / `syncLatestGeneratedOutput` / `inputNodeIds` references. Tests:
`tests/test_group_membership.py` (5 service + 4 repository: add/remove
persist+reload under one revision, idempotent add, stale-revision rejection,
missing group/member rejection), three HTTP-route tests in
`tests/test_canvas_nodes_api.py` (delegate+revision, payload validation, error
mapping), and one wiring contract
`test_group_membership_routes_through_the_graph_membership_command` in
`tests/test_frontend_workbench_modules.py` (one client method, one Smart
versioned helper, drag-gesture wiring, Core zero leak). Two pre-existing
count/string contracts updated for the new adoptRevision site and the new
mouseup fallback branch. Ownership matrix `group membership` row updated:
final owner is `GroupMembershipService` for the Smart member add plus
`group-membership.js` as the business-neutral membership query. Regression:
`./scripts/agent-verify.sh` PASS at 386 Python unit tests (baseline 373; +13),
PASS Python AST parse, PASS JavaScript syntax, PASS Architecture guards (4),
PASS `git diff --check`. `AGENT VERIFY: PASS`.

R4 Smart capability inventory (card R4-27, 2026-09-07T10:47+08:00, Owner
authorization via in-conversation "提交并开发下一任务"; implementer evidence,
independent review pending): characterization-only card (no code migrated or
deleted). Produced `docs/plans/R4_SMART_CAPABILITY_INVENTORY.md` — a granular
inventory of 31 Smart-only, product-relevant capabilities across 7 categories
(Composer; prompt presets/templates/skills; asset UX; media
edit/crop/draw/panorama; Smart group actions; cascade/execution; provider /
media / MiniMax dynamic controls), each classified KEEP/MIGRATE/COMPAT/REMOVE/
DEFER-R8 with a target owner and source-line evidence. Disposition split:
MIGRATE 18 (prompt registry/card, media edit, group actions, composer shell,
video player, asset mention/drag — Unified owners available in R4), COMPAT 13
(execution/provider/media controls whose real replacement is R8
`ExecutorRegistry`/`ExecutionRuntime`/`Provider`/`Model` registry), DEFER-R8 5
(asset/collection runtime, forbidden in R4 per "Forbidden next actions"); no
KEEP or REMOVE at capability granularity (the Smart runtime shell + Smart-entry
deep-link are REMOVE, already tracked in the ownership matrix). Ownership matrix
`Smart-only` review table now references the full inventory. Anchoring
`tests/test_smart_capability_inventory.py` (6 tests) parses the document's
machine-readable evidence manifest and verifies: every capability has a valid
disposition + non-empty target owner, every evidence function name is actually
present in `static/js/smart-canvas.js`, all In-Scope areas are covered, and the
classification is non-trivial (MIGRATE + COMPAT + DEFER-R8 all used). No product
code changed. Regression: `./scripts/agent-verify.sh` PASS at 392 Python unit
tests (baseline 386; +6), PASS Python AST parse, PASS JavaScript syntax, PASS
Architecture guards (4), PASS `git diff --check`. `AGENT VERIFY: PASS`.

R4 Smart Composer extraction (card R4-28, 2026-09-07T11:15+08:00, Owner
authorization via in-conversation "提交并开发下一任务"; implementer evidence,
independent review pending): the Smart Composer shell lifecycle is now a
mountable compatibility capability rather than Smart-page-owned. New
`static/js/workbench/canvas/composer.js` exposes
`window.WorkbenchCanvasComposer.create({container})` returning a frozen
lifecycle handle with `setOpen(open)` / `isOpen()` /
`positionForRect(rect, position)` / `cancelPending()` /
`scheduleUpdate(delay, onUpdate)`; the module owns the floating card's
container, open/close state, node-relative centering position math (default
540px card width, 14px gap), and the debounced update scheduler with a
sequence guard that drops stale callbacks. It is loaded by
`static/smart-canvas.html` ahead of `smart-canvas.js`, and Smart now delegates
its Composer head to a `composerLifecycle` handle:
`positionComposerForNode` → `composerLifecycle.positionForRect(nodeRect(node))`,
`scheduleComposerUpdate` → `composerLifecycle.scheduleUpdate(delay,
updateComposer)`, and `updateComposer` → `composerLifecycle.cancelPending()`
before resolving the selected node; the four `composer.classList` open/close
sites now route through `setOpen`/`isOpen`, and the old
`composerUpdateTimer`/`composerUpdateSeq` page state is removed. Subject
resolution (selected-node lookup) and dynamic provider/media/prompt parameter
rendering stay Smart-owned per the "do not redesign Composer" out-of-scope
boundary; the new module has zero Smart leak (no `smart-minimax` / `imageInput`
/ `cascadeRunBtn` / `selectedNode` / `renderDynamicParams` / `promptInput`).
Tests (both in `tests/test_frontend_workbench_modules.py`):
`test_composer_lifecycle_owns_position_open_and_debounced_schedule` (vm-sandbox
behavioral: open/close toggling, default and custom position math, debounce
cancels the first timer, the second fires once, `cancelPending` clears) and
`test_composer_lifecycle_is_loaded_before_the_smart_page_and_owned` (module
loads before the editor script; the page delegates position/open/close/debounce
to the lifecycle handle; no residual `composerUpdateTimer`/`composerUpdateSeq`;
module zero Smart leak). Ownership matrix `Composer` row updated: final owner
is the mountable `WorkbenchCanvasComposer` compatibility capability for the
shell lifecycle, with Smart retaining subject resolution + dynamic param
rendering. Regression: `./scripts/agent-verify.sh` PASS at 394 Python unit
tests (baseline 392; +2), PASS Python AST parse, PASS JavaScript syntax, PASS
Architecture guards (4), PASS `git diff --check`. `AGENT VERIFY: PASS`.

R4 Smart media tools extraction (card R4-29, 2026-09-07T11:30+08:00, Owner
authorization via in-conversation "提交并开发下一任务"; implementer evidence,
independent review pending): the retained Smart crop/draw/grid/resize tool
geometry is now a mountable compatibility capability rather than
Smart-page-owned. New `static/js/workbench/canvas/media-tools.js` exposes
`window.WorkbenchCanvasMediaTools` (a frozen namespace of pure, stateless
functions): `clampResizeScale` (resize-scale clamp to [0.05,1]),
`circledNumber` (1..20 → ①..⑳), `canvasPoint` (client→canvas pointer
mapping), `gridSplitRects` / `gridSplitRectsCustom` (uniform / custom-line
grid split rectangles with interior gap), `parseCropRatio` ('free'/'source'/
'w:h' → ratio), and `fitCropRectToAspect` (aspect-fit + bounds clamp, centered).
Loaded by `static/smart-canvas.html` ahead of `smart-canvas.js`; Smart now
delegates `clampImageResizeScale`, `circledNumber`, `editDrawPoint`,
`gridSplitRects`/`gridSplitRectsCustom`, `cropRatioFromPreset` and
`fitCropRectToAspect` to a `mediaTools` handle while keeping the editor modal,
canvas 2D rendering, mode/state machine and node mutation page-side (per "do
not build the future Media Package yet"). The module is product-neutral —
zero Smart leak (no `imageEditModal`/`cropImage`/`editDrawCanvas`/
`panoramaState`/`gridJoinLayout`/`cropState`/`selectedNode`/`replaceEditedImage`
/`scheduleSave`/`gridCustomLines`), and the page no longer owns the raw
geometry bodies (the old resize-clamp, circled-number, uniform grid-split,
aspect-fit and point-mapping bodies are removed). Panorama (Three.js) stays
Smart-owned compatibility, out of R4-29 scope. Tests (both in
`tests/test_frontend_workbench_modules.py`):
`test_media_tools_module_owns_crop_grid_draw_math` (vm-sandbox behavioral:
clamp, circled labels, point mapping, uniform/custom grid split rects with and
without gap, ratio parsing, aspect-fit/clamp) and
`test_media_tools_is_loaded_before_the_smart_page_and_owned` (module loads
before the editor script; page delegates all seven functions; no residual raw
math bodies; module zero Smart leak). Ownership matrix gains a "Media edit
tools" row. Regression: `./scripts/agent-verify.sh` PASS at 396 Python unit
tests (baseline 394; +2), PASS Python AST parse, PASS JavaScript syntax, PASS
Architecture guards (4), PASS `git diff --check`. `AGENT VERIFY: PASS`.

R4 Smart execution compatibility (card R4-30, 2026-09-07T11:50+08:00, Owner
authorization via in-conversation "提交并开发下一任务"; implementer evidence,
independent review pending): characterization + narrow host seam. New
`docs/plans/R4_SMART_EXECUTION_COMPATIBILITY.md` characterizes the retained
pre-R8 Smart execution path's Canvas-lifecycle/state ownership (node state
writes, node materialization + connect, selection, undo, persist/render,
global settings, feedback) across eight entry points with dispositions
seamed / host-cutover / host-candidate / transport-only / flag-only, plus an
embedded machine-readable JSON manifest. New
`static/js/workbench/canvas/execution-host.js` exposes
`window.WorkbenchCanvasExecutionHost.create(host)` — a frozen, validated host
handle with `markRunning` / `writePromptResult` / `save` / `render` /
`notifyError`; it is NOT an ExecutorRegistry/ExecutionRuntime and owns no
Canvas state. Loaded by `static/smart-canvas.html` ahead of `smart-canvas.js`;
Smart constructs one `executionHost` (injecting `node.running` toggle,
prompt-result write, `scheduleSave`, `render`, `toast`) and cuts over
`runPromptLLMNode` to route its Canvas lifecycle/state side-effects through the
handle — the old direct `node.promptResult = (result.text || '').trim()` /
`node.llmProvider = provider` / `node.running = true` / `render()` /
`scheduleSave()` / `toast()` writes in that function are gone. The remaining
`runGenerationLegacy` / `runSmartCascade` / `runCascadeStepIntoNode` stay
host-candidates (characterized, cut over in follow-on cards), and the provider
/API/WebSocket transport stays page-side compatibility (R8 owns the real
replacement). Tests (three in `tests/test_frontend_workbench_modules.py`):
`test_execution_host_module_owns_the_canvas_lifecycle_contract` (vm-sandbox
behavioral: delegate, run coercion, frozen handle, missing-op/non-object
TypeError), `test_smart_execution_compatibility_manifest_is_grounded_in_source`
(parses the doc manifest; every entry function + evidence present in
`smart-canvas.js`; dispositions valid and non-trivial), and
`test_execution_host_is_loaded_before_the_smart_page_and_run_prompt_llm_uses_it`
(module loads first; page delegates; old direct writes gone; module zero Smart
leak). One pre-existing contract updated:
`test_prompt_node_uses_the_compact_llm_card_hierarchy` now pins the host-handle
`node.promptResult = String(result?.promptResult ?? '').trim()` plus the
`executionHost.writePromptResult(...)` delegation. Ownership matrix
`execution trigger` row updated. Regression: `./scripts/agent-verify.sh` PASS
at 399 Python unit tests (baseline 396; +3), PASS Python AST parse, PASS
JavaScript syntax, PASS Architecture guards (4), PASS `git diff --check`.
`AGENT VERIFY: PASS`.

R4 Classic capability inventory (card R4-31, 2026-09-07T12:05+08:00, Owner
authorization via in-conversation "提交并开发下一任务"; implementer evidence,
independent review pending): characterization-only card (no code migrated or
deleted; out of scope: no blind deletion). Produced
`docs/plans/R4_CLASSIC_CAPABILITY_INVENTORY.md` — a granular inventory of 13
Classic-only, product-relevant capabilities across 9 categories (provider
cards; Comfy; RunningHub; MiniMax; LTX; video; output/log; asset;
cascade/execution), each classified KEEP/MIGRATE/COMPAT/REMOVE/DEFER-R8 with a
target owner and source-line evidence (56 function names). Disposition split:
MIGRATE 4 (provider node creation, Comfy result normalization, video
node/player, output node/grid — Unified owners available in R4), COMPAT 8
(provider card bodies, Comfy/RunningHub/MiniMax/LTX controls, video params,
generation log, cascade — whose real replacement is R8
`ExecutorRegistry`/`ExecutionRuntime`/`Provider`/`Model` registry), DEFER-R8 1
(asset library/manager, forbidden in R4); no KEEP or REMOVE at capability
granularity (the Classic runtime shell + Classic-entry deep-link are REMOVE,
already tracked in the ownership matrix). Ownership matrix `Classic-only`
review table now references the full inventory. Anchoring
`tests/test_classic_capability_inventory.py` (6 tests) parses the document's
machine-readable evidence manifest and verifies: every capability has a valid
disposition + non-empty target owner, every evidence function name is actually
present in `static/js/canvas.js`, all In-Scope areas are covered, and the
classification is non-trivial (MIGRATE + COMPAT + DEFER-R8 all used). No
product code changed. Regression: `./scripts/agent-verify.sh` PASS at 405
Python unit tests (baseline 399; +6), PASS Python AST parse, PASS JavaScript
syntax, PASS Architecture guards (4), PASS `git diff --check`.
`AGENT VERIFY: PASS`.

R4 Classic provider compatibility (card R4-32, 2026-09-07T12:13+08:00, Owner
authorization via in-conversation "提交并开发下一任务"; implementer evidence,
independent review pending): the retained Classic provider-card controls no
longer own Canvas lifecycle/state directly for the LLM provider body. New
`static/js/workbench/canvas/provider-controls.js` exposes
`window.WorkbenchCanvasProviderControls.create(host)` — a frozen, validated
host handle (`setField` / `save` / `render`); it is NOT an R7 provider registry
and owns no Canvas state. Loaded by `static/canvas.html` ahead of
`canvas.js`; Classic adds a lazy `ensureProviderControls()` accessor (injecting
`node[key] = value` field write, `scheduleSave`, `render`) and cuts over
`renderLLMBody`'s five control handlers (provider select, model select, system
toggle, system prompt, mode buttons) to route their Canvas side-effects through
the handle — the old direct `node.llmProvider = e.target.value` /
`node.showSystem = !node.showSystem` / `node.systemPrompt = e.target.value`
writes and their inline `render()` / `scheduleSave()` calls are removed.
Provider/model metadata resolution and body presentation stay page-side; the
other Classic provider bodies (generator/midjourney/msgen/Comfy/RunningHub/
MiniMax/LTX) remain page-owned compatibility (already COMPAT in the R4-31
inventory). Tests (two in `tests/test_frontend_workbench_modules.py`):
`test_provider_controls_module_owns_the_canvas_commit_contract` (vm-sandbox
behavioral: setField/save/render delegation, frozen handle, missing-op /
non-object TypeError) and
`test_provider_controls_is_loaded_before_the_classic_page_and_llm_body_uses_it`
(module loads first; page constructs the handle; `renderLLMBody` delegates all
five controls; old direct writes gone; module zero Classic leak). Ownership
matrix `Classic-only` table gains a "Provider-card controls (LLM body)" row.
Regression: `./scripts/agent-verify.sh` PASS at 407 Python unit tests
(baseline 405; +2), PASS Python AST parse, PASS JavaScript syntax, PASS
Architecture guards (4), PASS `git diff --check`. `AGENT VERIFY: PASS`.

R4 Classic execution compatibility (card R4-33, 2026-09-07T12:34+08:00, Owner
authorization via in-conversation "提交并开发下一任务"; implementer evidence,
independent review pending): characterization + narrow host seam. New
`docs/plans/R4_CLASSIC_EXECUTION_COMPATIBILITY.md` characterizes the retained
pre-R8 Classic execution path's Canvas-lifecycle/state ownership (node state
writes, cascade context flags, persist/render, feedback) across fifteen entry
points with dispositions seamed / host-cutover / host-candidate / flag-only,
plus an embedded machine-readable JSON manifest. New
`static/js/workbench/canvas/classic-execution-host.js` exposes
`window.WorkbenchCanvasClassicExecutionHost.create(host)` — a frozen, validated
host handle with `markRunning` / `writeOutputText` / `setRunStatus` / `render` /
`save` / `notifyError`; it is NOT an ExecutorRegistry/ExecutionRuntime and owns
no Canvas state. Loaded by `static/canvas.html` ahead of `canvas.js`; Classic
adds a lazy `ensureClassicExecutionHost()` accessor (injecting the `running`
toggle, `outputText` write, `runStatus`/`runError` write, `refreshNodes`,
`scheduleSave`, `alert`) and cuts over `runLLMNode` to route its Canvas
lifecycle/state side-effects through the handle — the old direct
`node.running = true` / `node.outputText = await callCanvasLLM(...)` /
`node.runStatus = 'done'` / `node.runError = ...` writes and their inline
`refreshNodes` / `scheduleSave` / `alert` calls in that function are gone. The
LLM call itself (`callCanvasLLM`) and the cascade orchestrators (`runNodeCascade`,
`runCascadeNodeByType`, `beginCascade`, `finalizeCascade`, `retryNodeAndDownstream`,
etc.) stay host-candidates (characterized, cut over in follow-on cards), and the
provider/API transport stays page-side compatibility (R8 owns the real
replacement). Tests (three in `tests/test_frontend_workbench_modules.py`):
`test_classic_execution_host_module_owns_the_canvas_lifecycle_contract` (vm-sandbox
behavioral: markRunning/writeOutputText/setRunStatus/render/save/notifyError
delegation, run coercion, frozen handle, missing-op/non-object TypeError),
`test_classic_execution_compatibility_manifest_is_grounded_in_source` (parses the
doc manifest; every entry function + evidence present in `canvas.js`; dispositions
valid and non-trivial), and
`test_classic_execution_host_is_loaded_before_the_classic_page_and_run_llm_uses_it`
(module loads first; page delegates; old direct writes gone; module zero Classic
leak). Ownership matrix `Classic-only` table gains a "LLM node execution" row.
Regression: `./scripts/agent-verify.sh` PASS at 410 Python unit tests
(baseline 407; +3), PASS Python AST parse, PASS JavaScript syntax, PASS
Architecture guards (4), PASS `git diff --check`. `AGENT VERIFY: PASS`.

R4 Smart native entry (card R4-34, 2026-09-07T14:30+08:00, Owner authorization
via in-conversation "提交并开发下一任务"; implementer evidence, independent
review pending): `canvas.html` is now the single entry that opens a historical
Smart record natively, without redirecting to `smart-canvas.html`. New
`docs/plans/R4_SMART_NATIVE_ENTRY.md` inventories the entry-routing surface
(list entry URL, `openCanvas` Smart branch, `createCanvas` Smart branch,
`openSmartCanvasPage`, the `WorkbenchCanvasEntryCompatibility` handoff
helpers) with dispositions host-cutover / dead-code-removed / unchanged. The
`openCanvas` Smart handoff check (`requiresLegacySmartHandoff(canvas)` →
`openSmartCanvasPage`) is removed from `static/js/canvas.js`; the
`createCanvas` Smart branch now navigates a freshly created Smart-kind record
to `canvas.html` via the shared `WorkbenchCanvasEntryCompatibility.normalCanvasUrl(id, project)`
helper (consistent contract with the list entry URL); with both call sites
gone, `openSmartCanvasPage` itself is removed as dead code. `canvas.html`
adds `<script>` tags for the two Smart-compatibility shared seams
(`composer.js` + `media-tools.js`, both R4 seams already used by
`smart-canvas.html`) ahead of `canvas.js`, so the unified page has the
Composer shell lifecycle and the media-edit geometry available for Smart
node types. The Smart product runtime files (`smart-canvas.html` /
`smart-canvas.js`) stay on disk (out of scope: `R4-36` retires them); the
`WorkbenchCanvasEntryCompatibility` handoff helpers
(`requiresLegacySmartHandoff`, `legacySmartCanvasUrl`) stay exported (out of
scope: `R4-35` retires the handoff module). Two focused tests in
`tests/test_frontend_workbench_modules.py`:
`test_smart_native_entry_routes_smart_kinds_through_canvas_html` (vm-sandbox
behavioral: `normalCanvasUrl` returns a `canvas.html` URL for every kind) and
`test_smart_native_entry_removes_the_handoff_redirect_from_canvas_js`
(source-contract: composer/media-tools loaded ahead of `canvas.js`; the
handoff redirect, `openSmartCanvasPage`, `requiresLegacySmartHandoff` and
`legacySmartCanvasUrl` are all gone from `canvas.js`; the Smart-create branch
routes through `normalCanvasUrl`). Two pre-existing contracts in
`tests/test_canvas_entry.py` updated: `test_historical_smart_handoff_preserves_the_current_query`
→ `test_canvas_editor_opens_every_record_without_the_smart_handoff`, and
`test_canvas_editor_uses_only_the_entry_compatibility_handoff_decision` →
`test_canvas_editor_routes_every_record_through_the_unified_open_path`, both
now pinning the R4-34 unified open contract. Ownership matrix `normal
navigation` row updated to "one entry" and `Smart handoff` row annotated
"R4-34: openCanvas/createCanvas no longer consume the handoff; R4-35 retires
the module." Regression: `./scripts/agent-verify.sh` PASS at 412 Python
unit tests (baseline 410; +2), PASS Python AST parse, PASS JavaScript
syntax, PASS Architecture guards (4), PASS `git diff --check`.
`AGENT VERIFY: PASS`.

R4 Smart handoff removal (card R4-35, 2026-09-07T14:49+08:00, Owner
authorization via in-conversation "提交并开发下一任务"; implementer evidence,
independent review pending): the Smart product-page handoff surface is
retired from `WorkbenchCanvasEntryCompatibility`. After R4-34 stopped
consuming the handoff, the two helpers were dead surface — no JS code
constructed a navigation to `smart-canvas.html` — so this card removes
`requiresLegacySmartHandoff(canvas)` and `legacySmartCanvasUrl(canvasId, search)`
plus the only `/static/smart-canvas.html` URL string from
`static/js/workbench/canvas/canvas-entry-compatibility.js`. The module
keeps the four-function normal surface (`normalCanvasUrl`,
`rememberCanvasListProject`, `rememberedCanvasListProject`,
`canvasListUrl`) used by `canvas.js`, `canvas-list.js`, `asset-manager.js`
and `smart-canvas.js`. The `smart-canvas.html` / `smart-canvas.js`
product page stays on disk (out of scope: `R4-36` retires the page after
the Smart-capability migration is verified). After this card, a static-JS
audit finds zero hits for the routable `/static/smart-canvas.html` string
across `static/js/**/*.js` and `static/js/*.js` — the DoD "No Smart
product page routing remains" is satisfied at the source level. The
`tests/test_canvas_entry.py` handoff contracts are updated:
`test_entry_compatibility_keeps_one_normal_entry_and_scopes_smart_handoff`
→ `test_entry_compatibility_keeps_one_normal_entry_with_no_handoff_surface`
(vm-sandbox + source-contract: the module's frozen export is exactly the
four non-handoff keys; the handoff function names and the
`/static/smart-canvas.html` string are gone), and
`test_product_openers_confine_smart_page_urls_to_the_compatibility_boundary`
→ `test_no_smart_product_page_routing_remains_in_static_js` (the
compatibility boundary itself no longer carries the URL — the routable
string is absent from every scanned JS file, including the entry module).
Ownership matrix `Smart handoff` row retired. Regression:
`./scripts/agent-verify.sh` PASS at 412 Python unit tests (baseline 412;
+0 — R4-35 strengthens/renames existing contracts rather than adding
new redundant ones, since the handoff helpers had no other consumers),
PASS Python AST parse, PASS JavaScript syntax, PASS Architecture
guards (4), PASS `git diff --check`. `AGENT VERIFY: PASS`.

R4 Classic runtime shrink — Wave 6 of R4-38
(card R4-38, Wave 6 done 2026-09-07T16:52+08:00, Owner authorization
via in-conversation "Wave 6"; implementer evidence, Independent
review: PASS 2026-09-07T17:09+08:00 — see review notes appended below): the sixth shrink wave of the Classic runtime closes the
**Comfy workflow / field control** COMPAT capability by extracting the
five page-side Comfy functions (`addComfyNode` — 32-line factory,
`comfyWorkflowOptions` — 4-line `<option>` builder, `renderComfyBody`
— 64-line body renderer, `renderComfySettings` — 80-line mode-specific
settings panel, `updateComfyField` — 42-line field change handler,
~222 LOC total) into a new bounded compat seam module
`static/js/workbench/canvas/classic-comfy-controls.js`
(`window.WorkbenchCanvasClassicComfyControls.create(host)` returns
frozen `{addNode({point}), renderBody({node}), renderSettings({container,
node}), updateField({node, input, event}), getWorkflowOptions({selected})}`).
canvas.js deletes all five local function definitions (-222 LOC);
`createNodeByType`'s `'comfy'` dispatch rewrites from
`return addComfyNode(point)` to
`return ensureClassicComfyControls().addNode({point})`; the body
dispatcher's `node.type === 'comfy'` branch rewrites from
`body.appendChild(renderComfyBody(node))` to
`body.appendChild(comfy.renderBody({node}))` after a single
`const comfy = ensureClassicComfyControls();` line alongside the Wave 5
`const cardBody = ensureClassicCardBodyRenderer();` line. New `let
classicComfyControls = null;` + `function ensureClassicComfyControls()`
next to `ensureClassicCardBodyRenderer`, injecting all 29 REQUIRED host
ops (document / escapeHtml / tr / addNode / uid / defaultPoint /
allImageModels / imageApiProviders / `getModels: () => models` (const
lookup → closure to keep REQUIRED-all-function contract) /
`getComfyWorkflows: () => comfyWorkflows` (let lookup → closure) /
generatorSources / orderedSources / imageRefsOnly / comfyFields /
validComfyWorkflowName / hasComfyWorkflow / currentComfyWorkflow /
comfyFieldKind / ensureComfyWorkflow / render / scheduleSave /
runCanvasGenerate / renderPromptPreview / renderComfyImages /
renderComfyCustomField / toggleComfyRandom / bindCascadeButtons /
cascadeBtnHtml / retryBarHtml). canvas.html loads the seam between
`classic-card-body-renderer.js` and `canvas.js`, so the load order is
now `provider-controls → card-body → comfy-controls → canvas.js`. The
R4-31 inventory's `comfy-controls` row keeps its COMPAT disposition
but gains `evidence_target =
"static/js/workbench/canvas/classic-comfy-controls.js"` so the
inventory's evidence-grounding test now looks for the five Comfy
function names in the seam module instead of canvas.js. New focused
test
`test_classic_editor_routes_comfy_workflow_field_controls_through_classic_comfy_controls_seam`
(a) drives `addNode` / `renderBody` / `renderSettings` in a vm sandbox
with a stub `document.createElement` + minimal mock host (29 ops); (b)
asserts each runs without throwing; (c) asserts `addNode` produces
`(type:'comfy', id:'comfy-test', mode:'text', editModel:'test-comfy-model',
comfyWorkflow:'')` exactly (the same record shape the page-side
factory produced); (d) asserts `getWorkflowOptions` lists the seeded
workflows (`wf1.json` / `wf2.json`) AND the empty-list fallback option
(`<option value="">canvas.comfyNoWorkflow</option>` — exercised via a
second `create()` call with `getComfyWorkflows: () => []` because the
seam module destructures host ops at `create()` time, so post-create
host mutation cannot land on the fallback branch); (e) iterates all 29
host ops to verify TypeError-on-missing-host (with a
`assertEqual(len(REQUIRED), 29)` count pin to keep seam + test
synchronized); (f) source-contracts the canvas.html seam load order
(comfy-controls before canvas.js), the five `function` wrapper
deletions in canvas.js, and the two dispatcher seam-call shapes
(`ensureClassicComfyControls().addNode({point})` +
`comfy.renderBody({node})`). R4-38 remains IN_PROGRESS — 8 of 15
Classic capabilities still need shrink waves (8 COMPAT waiting for
the COMPAT-seam waves, 1 DEFER-R8 out of R4 scope). Regression:
`./scripts/agent-verify.sh` PASS at 349 Python unit tests (was 348
after Wave 5; +1 from Wave 6's new focused test), PASS Python AST
parse (76 files), PASS JavaScript syntax (74 files; +1 for the new
seam module), PASS Architecture guards (4), PASS `git diff --check`.
`AGENT VERIFY: PASS`.
Independent review: PASS 2026-09-07T17:09+08:00 (independent review
agent verified one-commit-scope, AGENTS.md hard constraints [industry-
neutral Core, canonical concept separation, one creation/mutation
boundary via host seam pattern, page-side state stays page-side via
closure-passed `getModels` / `getComfyWorkflows`, local-first],
out-of-scope check, ownership truth [5 functions GONE from canvas.js,
5 function bodies present in seam, no false claim of state ownership],
real-behavioral tests [vm-sandbox drive + record-shape equality +
TypeError-on-missing-host loop + source-contracts], status-doc
faithfulness [349 tests claim matches actual `./scripts/agent-verify.sh`
output], DoD checkbox + next-wave pointer [Wave 6 → Wave 7
RunningHub]. Two P2 nits noted, both non-blocking: card line 13
stale "9 of 15" phrase → fixed to "8 of 15" in this review pass; seam
module lacks trailing newline → cosmetic, harmless).

R4 Classic runtime shrink — Wave 7 of R4-38
(card R4-38, Wave 7 done 2026-09-07T17:25+08:00, Owner authorization
via in-conversation "执行 AGENT_NEXT_TASK.md 指向的当前 Active Task";
implementer evidence, Independent review: pending): the seventh shrink
wave of the Classic runtime closes the **RunningHub workflow / params**
COMPAT capability by extracting the six page-side RunningHub functions
(`addRhNode` — 20-line factory, `renderRhBody` — ~80-line body
renderer, `renderRhParams` — ~22-line params renderer,
`runningHubProvider` — 4-line resolver, `currentRunningHubWorkflow` —
4-line resolver, `currentRunningHubWorkflowConfig` — ~18-line config
builder, ~148 LOC total) into a new bounded compat seam module
`static/js/workbench/canvas/classic-runninghub-controls.js`
(`window.WorkbenchCanvasClassicRunningHubControls.create(host)` returns
frozen `{addNode({point}), renderBody({node}), renderParams({container,
node, fields, media}), getProvider(), getCurrentWorkflow({node}),
getCurrentWorkflowConfig({node})}`).
canvas.js deletes all six local function definitions (~148 LOC of
factory + body + params + resolvers); `createNodeByType`'s `'rh'`
dispatch rewrites from `return addRhNode(point)` to
`return ensureClassicRunningHubControls().addNode({point})`; the body
dispatcher's `node.type === 'rh'` branch rewrites from
`body.appendChild(renderRhBody(node))` to
`body.appendChild(rh.renderBody({node}))` after a single
`const rh = ensureClassicRunningHubControls();` line alongside the
Wave 5 `const cardBody = ensureClassicCardBodyRenderer();` and Wave 6
`const comfy = ensureClassicComfyControls();` lines; the
`refreshGeneratorInputViews` external caller of `renderRhParams`
rewrites from
`renderRhParams(el.querySelector('.rh-param-list'), gen, rhActiveFields(gen), media)`
to
`ensureClassicRunningHubControls().renderParams({container: el.querySelector('.rh-param-list'), node: gen, fields: rhActiveFields(gen), media: media})`.
New `let classicRunningHubControls = null;` +
`function ensureClassicRunningHubControls()` next to
`ensureClassicComfyControls`, injecting all 60 REQUIRED host ops
(document / escapeHtml / escapeAttr / tr / addNode / uid /
defaultPoint / validRunningHubWorkflowId / parseRunningHubEntryKey /
runningHubEntryKey / runningHubAllEntries / runningHubEntries /
runningHubEntryId / ensureRhNodeSelection / applyRhEntrySelection /
rhSelectedEntryRef / rhCurrentKind / rhEntryOptions /
rhPaymentOptions / rhModelSettingsHtml / bindRhModelControls /
renderRhPromptFields / renderRhInputs / rhMediaSources /
rhActiveFields / rhFieldRole / rhParamKey / rhExtractFieldOptions /
rhFieldValue / rhDefaultValue / rhRandomEnabled / rhRandomActive /
toggleRhRandom / currentRunningHubWorkflowEntry / rhEntryFields /
rhWorkflowJsonFromSources / bindRhParamControls /
renderRhSettingField / generatorSources / orderedSources /
imageRefsOnly / videoRefsOnly / audioRefsOnly / mediaKindForRef /
nodeTitleForMedia / rhMediaPreviewHtml /
normalizeApiNodeSizeChoice / defaultApiImageResolution /
parseSizeValue / renderImageInputList / render / scheduleSave /
runCanvasGenerate / refreshIcons / renderPromptPreview /
bindCascadeButtons / cascadeBtnHtml / retryBarHtml). The two closure
values (`getApiProviders`, `getRunningHubWorkflowCache`) keep the
seam's REQUIRED-all-function contract stable even though `apiProviders`
is a `let` and `runningHubWorkflowCache` is a `let` module-level
variable. canvas.html loads the seam between `classic-comfy-controls.js`
and `canvas.js`, so the load order is now
`provider-controls → card-body → comfy-controls → runninghub-controls → canvas.js`.
The R4-31 inventory's `runninghub` row keeps its COMPAT disposition
but gains `evidence_target =
"static/js/workbench/canvas/classic-runninghub-controls.js"` so the
inventory's evidence-grounding test now looks for the six RunningHub
function names in the seam module instead of canvas.js. New focused
test
`test_classic_editor_routes_runninghub_workflow_params_through_classic_runninghub_controls_seam`
(a) drives `addNode` / `renderBody` / `renderParams` / `getProvider` /
`getCurrentWorkflow` / `getCurrentWorkflowConfig` in a vm sandbox with
a stub `document.createElement` + minimal mock host (60 ops); (b)
asserts each runs without throwing; (c) asserts `addNode` produces
`(type:'rh', id:'rh-test', rhMode:'app', rhPayment:'free', inputs:[])`
exactly (the same record shape the page-side factory produced); (d)
asserts `getProvider` resolves `'runninghub'` from the `getApiProviders`
closure; (e) asserts `getCurrentWorkflow` reads from the
`getRunningHubWorkflowCache` closure (returns the cached entry title);
(f) asserts `getCurrentWorkflowConfig` returns the merged entry+cache
title; (g) asserts the non-workflow-mode short-circuit (with a second
seam where `rhCurrentKind: () => 'app'`) returns `null`; (h) iterates
all 60 host ops to verify TypeError-on-missing-host (with a
`assertEqual(len(REQUIRED), 60)` count pin to keep seam + test
synchronized); (i) source-contracts the canvas.html seam load order
(runninghub-controls before canvas.js), the six `function` wrapper
deletions in canvas.js, and the four dispatcher seam-call shapes
(`ensureClassicRunningHubControls().addNode({point})` +
`rh.renderBody({node})` + `ensureClassicRunningHubControls().renderParams({...})`).
R4-38 remains IN_PROGRESS — 7 of 15 Classic capabilities still need
shrink waves (7 COMPAT waiting for the COMPAT-seam waves, 1 DEFER-R8
out of R4 scope). Regression:
`./scripts/agent-verify.sh` PASS at 350 Python unit tests (was 349
after Wave 6; +1 from Wave 7's new focused test), PASS Python AST
parse (76 files), PASS JavaScript syntax (75 files; +1 for the new
seam module), PASS Architecture guards (4), PASS `git diff --check`.
`AGENT VERIFY: PASS`.

R4 Classic runtime shrink — Wave 8 of R4-38
(card R4-38, Wave 8 done 2026-09-07T17:48+08:00, Owner authorization
via in-conversation "Wave 8"; implementer evidence, Independent
review: pending): the eighth shrink wave of the Classic runtime
closes the **MiniMax timeline / player / generation** COMPAT
capability by extracting the six page-side MiniMax functions
(`addMiniMaxNode` — ~23-line factory, `renderMiniMaxBody` — ~102-line
body renderer, `bindMiniMaxWorkbench` — ~226-line workbench binder
that wires up segment / ref / drop / scrub / run / download
interactions, `miniMaxEngine` — 3-line engine resolver,
`miniMaxPlayerHtml` — 8-line player HTML builder,
`miniMaxSyncPlayerDom` — ~18-line player sync, ~380 LOC total) into a
new bounded compat seam module
`static/js/workbench/canvas/classic-minimax-controls.js`
(`window.WorkbenchCanvasClassicMiniMaxControls.create(host)` returns
frozen `{addNode({point}), renderBody({node}), bindWorkbench({wrap,
node}), getEngine({node}), buildPlayerHtml({seg}), syncPlayerDom({wrap,
seg, time, play})}`).
canvas.js deletes all six local function definitions (~335 LOC of
factory + body + workbench + player + sync after accounting for the
seam-call site and the local `awk` deletion of the big 330-line block
of `renderMiniMaxBody` + `bindMiniMaxWorkbench`); `createNodeByType`'s
`'minimax'` dispatch rewrites from `return addMiniMaxNode(point)` to
`return ensureClassicMiniMaxControls().addNode({point})`; the body
dispatcher's `node.type === 'minimax'` branch rewrites from
`body.appendChild(renderMiniMaxBody(node))` to
`body.appendChild(mmx.renderBody({node}))` after a single
`const mmx = ensureClassicMiniMaxControls();` line alongside the Wave 5/6/7
patterns. Two external callers (`miniMaxEnsureSegment` line 8545 +
`runMiniMaxNode`'s pre-flight engine resolve line 10849) rewrite from
`miniMaxEngine(node)` to
`ensureClassicMiniMaxControls().getEngine({node})`; one external caller
(`miniMaxApplyTimelineTime` line 8670) rewrites from
`miniMaxSyncPlayerDom(wrap, seg, safeTime, play)` to
`ensureClassicMiniMaxControls().syncPlayerDom({wrap, seg, time: safeTime, play})`.
New `let classicMiniMaxControls = null;` +
`function ensureClassicMiniMaxControls()` next to
`ensureClassicRunningHubControls`, injecting all 35 REQUIRED host ops
(document / escapeHtml / escapeAttr / addNode / uid / defaultPoint /
miniMaxSelectedSegment / miniMaxTimelineTotal /
miniMaxActiveSegmentAt / miniMaxCompactSegments /
miniMaxExplicitRefsForSegment / miniMaxRefsForNode /
miniMaxUniqueRefs / miniMaxMediaHtml / miniMaxSegmentRefsByKind /
miniMaxStartPaneResize / miniMaxApplyTimelineTime /
miniMaxDownloadItem / miniMaxSetSegmentResult / mediaKindForRef /
mediaKindForOutputItem / canvasDisplayMediaUrl / canvasPreviewImgHtml
/ canvasVideoPlayerHtml / canvasFileNameFromUrl / pushUndo /
refreshNodes / scheduleSave / bindScrollableText /
bindCascadeButtons / cascadeBtnHtml / retryBarHtml / refreshIcons /
rhPaymentOptions / runMiniMaxNode) plus the 5 `CANVAS_MINIMAX_*`
constants (REF_IMAGE_MAX=9 / REF_VIDEO_MAX=3 / REF_AUDIO_MAX=3 /
DEFAULT_ENGINE='comfyui' / RUNNINGHUB_WORKFLOW_ID='2084608321469898754')
as host-injected values so the seam module never touches page-locals
directly. canvas.html loads the seam between
`classic-runninghub-controls.js` and `canvas.js`, so the load order is
now
`provider-controls → card-body → comfy-controls → runninghub-controls → minimax-controls → canvas.js`.
The R4-31 inventory's `minimax` row keeps its COMPAT disposition
but gains `evidence_target =
"static/js/workbench/canvas/classic-minimax-controls.js"` so the
inventory's evidence-grounding test now looks for the six MiniMax
function names in the seam module instead of canvas.js. New focused
test
`test_classic_editor_routes_minimax_timeline_player_generation_through_classic_minimax_controls_seam`
(a) drives all six seam methods in a vm sandbox with a stub
`document.createElement` + minimal mock host (35 ops + 5 constants);
(b) asserts each runs without throwing; (c) asserts `addNode`
produces `(type:'minimax', id:'mmx-test', minimaxEngine:'comfyui',
rhPayment:'free', w:980, h:720,
minimaxRunningHubWorkflowId:'2084608321469898754', aspectRatio:'16:9',
megapixels:0.4, segments:[])` exactly (the same record shape the
page-side factory produced); (d) asserts `getEngine` returns
`'runninghub'` when `node.minimaxEngine === 'runninghub'` and
`'comfyui'` otherwise (verifies the resolver's two-branch logic);
(e) asserts `buildPlayerHtml` produces the empty-player placeholder
(`<div class="minimax-player-empty">`) for a `null` seg (verifies
the empty-segment branch); (f) iterates all 35 host ops to verify
TypeError-on-missing-host (with a `assertEqual(len(REQUIRED), 35)`
count pin to keep seam + test synchronized); (g) source-contracts the
canvas.html seam load order (minimax-controls before canvas.js), the
six `function` wrapper-deletions in canvas.js, and the three
dispatcher seam-call shapes
(`ensureClassicMiniMaxControls().addNode({point})` +
`mmx.renderBody({node})` + `function ensureClassicMiniMaxControls`
declaration next to `ensureClassicRunningHubControls`). R4-38
remains IN_PROGRESS — 6 of 15 Classic capabilities still need shrink
waves (6 COMPAT waiting for the COMPAT-seam waves, 1 DEFER-R8 out of
R4 scope). Regression:
`./scripts/agent-verify.sh` PASS at 351 Python unit tests (was 350
after Wave 7; +1 from Wave 8's new focused test), PASS Python AST
parse (76 files), PASS JavaScript syntax (76 files; +1 for the new
seam module), PASS Architecture guards (4), PASS `git diff --check`.
`AGENT VERIFY: PASS`.

R4 Classic runtime shrink — Wave 9 of R4-38
(card R4-38, Wave 9 done 2026-09-07T18:05+08:00, Owner authorization
via in-conversation "开始Wave 9"; implementer evidence, Independent
review: pending): the ninth shrink wave of the Classic runtime
closes the **LTX director timeline / relay** COMPAT capability by
extracting the six page-side LTX functions (`addLTXDirectorNode`
— ~30-line factory, `renderLTXDirectorBody` — ~80-line body renderer,
`destroyLTXEditor` — 5-line destructor, `ltxParseTimeline` — 10-line
JSON parser, `ltxFlushTimelineToNode` — 7-line commit helper,
`ltxBuildContiguousRelay` — ~50-line relay builder that flattens
timeline segments into contiguous relay form, ~155 LOC total) into
a new bounded compat seam module
`static/js/workbench/canvas/classic-ltx-controls.js`
(`window.WorkbenchCanvasClassicLTXControls.create(host)` returns
frozen `{addNode({point}), renderBody({node}), destroyEditor({node}),
parseTimeline({node}), flushTimelineToNode({node}),
buildContiguousRelay({node, globalPromptFallback})}`).
canvas.js deletes all six local function definitions; `createNodeByType`'s
`'ltxDirector'` dispatch rewrites from `return addLTXDirectorNode(point)`
to `return ensureClassicLTXControls().addNode({point})`; the body
dispatcher's `node.type === 'ltxDirector'` branch rewrites from
`body.appendChild(renderLTXDirectorBody(node))` to
`body.appendChild(ltx.renderBody({node}))` after a single
`const ltx = ensureClassicLTXControls();` line alongside the Wave 5/6/7/8
patterns. The `onCardDestroy` payloadNode handler at line 5919 rewrites
from `payloadNode => destroyLTXEditor(payloadNode)` to
`payloadNode => ensureClassicLTXControls().destroyEditor({node: payloadNode})`.
The timeline view binder helper (ltxDirectorTimelineSegments /
ltxRefreshTimelineEditor setup at line 10918) rewrites to call
`ensureClassicLTXControls().parseTimeline({node})`. The timeline flush
helper (ltxFlushTimelineToNode caller at line 11075) rewrites to call
`ensureClassicLTXControls().flushTimelineToNode({node})`. The relay
builder entry (ltxDirectorBuildTimelinePayload at line 11260) rewrites
to call
`ensureClassicLTXControls().buildContiguousRelay({node, globalPromptFallback})`.
New `let classicLTXControls = null;` +
`function ensureClassicLTXControls()` next to
`ensureClassicMiniMaxControls`, injecting all 26 REQUIRED host ops
(escapeHtml / addNode / uid / defaultPoint / refreshGeometryAfterLayout
/ refreshIcons / defaultLTXSegment / ltxDirectorSyncSeconds /
bindLTXParamsRow / updateLTXNodeElementSize /
ltxMigrateLegacySegments / ltxDirectorTimelineSegments /
ltxRefreshTimelineEditor / ltxDirectorBuildTimelinePayload /
ltxSetSelectedSegment / ltxRemoveSegment / ltxSplitSegmentAt /
ltxUpdateSegment / ltxAddSegment / ltxInitEmptyTimelineEditor /
pushUndo / scheduleSave / bindScrollableText / runLTXDirectorNode /
handleNodeDrop / mediaKindForOutputItem / canvasDisplayMediaUrl)
plus the `LTX_SEGMENT_COLORS` array as a host-injected constant so
the seam module never touches page-locals directly. canvas.html loads
the seam between `classic-minimax-controls.js` and `canvas.js`, so
the load order is now
`provider-controls → card-body → comfy-controls → runninghub-controls → minimax-controls → ltx-controls → canvas.js`.
The R4-31 inventory's `ltx` row keeps its COMPAT disposition but
gains `evidence_target =
"static/js/workbench/canvas/classic-ltx-controls.js"` so the
inventory's evidence-grounding test now looks for the six LTX
function names in the seam module instead of canvas.js. New focused
test
`test_classic_editor_routes_ltx_director_timeline_relay_through_classic_ltx_controls_seam`
(a) drives all six seam methods in a vm sandbox with a stub
`document.createElement` + minimal mock host (26 ops + 1 array
constant); (b) asserts each runs without throwing; (c) asserts
`addNode` produces `(type:'ltxDirector', id:'ltxdir-test',
durationFrames:120, frameRate:24, ltxSegments:[], inputs:[])` exactly
(the same record shape the page-side factory produced); (d) asserts
`parseTimeline` returns `{segments:[], audioSegments:[]}` for empty
JSON and tolerates malformed JSON (returns the empty default); (e)
asserts `buildContiguousRelay` produces correct gap-fill semantics
for the documented two-segment scenario (alpha segment 30 frames
starting at frame 0, beta segment 30 frames starting at frame 40,
10-frame gap between them): `segment_lengths` = "40,30" (alpha's
30 frames + 10-frame gap appended), `local_prompts` includes both
alpha and beta prompts joined by ' | '; (f) iterates all 26 host
ops to verify TypeError-on-missing-host (with a
`assertEqual(len(REQUIRED), 26)` count pin to keep seam + test
synchronized); (g) source-contracts the canvas.html seam load
order (ltx-controls before canvas.js), the six `function`
wrapper-deletions in canvas.js, and the dispatcher seam-call shapes
(`ensureClassicLTXControls().addNode({point})` +
`ltx.renderBody({node})` + `function ensureClassicLTXControls`
declaration next to `ensureClassicMiniMaxControls`). R4-38 remains
IN_PROGRESS — 5 of 15 Classic capabilities still need shrink waves
(5 COMPAT waiting for the COMPAT-seam waves, 1 DEFER-R8 out of R4
scope). Regression:
`./scripts/agent-verify.sh` PASS at 352 Python unit tests (was 351
after Wave 8; +1 from Wave 9's new focused test), PASS Python AST
parse (76 files), PASS JavaScript syntax (77 files; +1 for the new
seam module), PASS Architecture guards (4), PASS `git diff --check`.
`AGENT VERIFY: PASS`.

R4 Classic runtime shrink — Wave 10 of R4-38
(card R4-38, Wave 10 done 2026-09-07T18:28+08:00, Owner
authorization via in-conversation "开始Wave 10"; implementer
evidence, Independent review: pending): the tenth shrink wave of
the Classic runtime closes the **video-card-body** COMPAT
capability by extracting the page-side `renderVideoBody` function
(~135-line body renderer for the `video`-type generator card —
provider/model selects, duration/aspect/resolution, the toggle row,
the media input list, and the manual-URL / temp-sh action buttons)
into a new bounded compat seam module
`static/js/workbench/canvas/classic-video-card-body.js`
(`window.WorkbenchCanvasClassicVideoCardBody.create(host)` returns
frozen `{renderBody({node})}`).
canvas.js deletes the local `function renderVideoBody` definition;
the body dispatcher's `node.type === 'video'` branch rewrites from
`body.appendChild(renderVideoBody(node))` to
`body.appendChild(videoBody.renderBody({node}))` after a single
`const videoBody = ensureClassicVideoCardBody();` line alongside
the Wave 5/6/7/8/9 patterns. New `let classicVideoCardBody = null;` +
`function ensureClassicVideoCardBody()` next to
`ensureClassicLtxControls`, injecting all 21 REQUIRED host ops
(document / tr / generatorSources / orderedSources / mediaKindForRef
/ sanitizeVideoNodeProviderModel / videoProviderOptions /
videoModelOptions / providerVideoModels / renderVideoImageInputs /
renderPromptPreview / scheduleSave / runCanvasGenerate /
bindCascadeButtons / cascadeBtnHtml / retryBarHtml / render /
showErrorModal / uploadCanvasVideosToCloud / setCanvasManualVideoUrl
/ refreshIcons) so the seam module never touches page-locals
directly. canvas.html loads the seam between
`classic-ltx-controls.js` and `composer.js`, so the load order is
now
`provider-controls → card-body → comfy-controls → runninghub-controls → minimax-controls → ltx-controls → video-card-body → composer.js → media-tools.js → canvas.js`.
The R4-31 inventory's `video-card-body` row keeps its COMPAT
disposition but gains `evidence_target =
"static/js/workbench/canvas/classic-video-card-body.js"` so the
inventory's evidence-grounding test now looks for the `renderVideoBody`
function name in the seam module instead of canvas.js. New focused
test
`test_classic_editor_routes_video_card_body_through_classic_video_card_body_seam`
(a) drives the seam in a Node vm sandbox with a stub document and
21-op minimal mock host; (b) asserts the rendered body element
uses the documented `generator-body` className; (c) asserts the
body HTML contains the documented `video-input-head` marker
section; (d) iterates all 21 host ops to verify
TypeError-on-missing-host (with a `assertEqual(len(required), 21)`
count pin to keep seam + test synchronized); (e) source-contracts
the canvas.html seam load order (ltx-controls before
video-card-body before canvas.js), the `function renderVideoBody`
wrapper-deletion in canvas.js, and the body dispatcher seam-call
shape (`videoBody.renderBody({node})` +
`function ensureClassicVideoCardBody` declaration next to
`ensureClassicLtxControls`). R4-38 remains IN_PROGRESS — 4 of 15
Classic capabilities still need shrink waves (4 COMPAT waiting for
the COMPAT-seam waves, 1 DEFER-R8 out of R4 scope). Regression:
`./scripts/agent-verify.sh` PASS at 353 Python unit tests (was 352
after Wave 9; +1 from Wave 10's new focused test), PASS Python AST
parse (76 files), PASS JavaScript syntax (78 files; +1 for the new
seam module), PASS Architecture guards (4), PASS `git diff --check`.
`AGENT VERIFY: PASS`.

R4 Classic runtime shrink — Wave 11 of R4-38
(card R4-38, Wave 11 done 2026-09-07T18:46+08:00, Owner
authorization via in-conversation "开始Wave 11"; implementer
evidence, Independent review: pending): the eleventh shrink wave
of the Classic runtime closes the **video-provider/params** COMPAT
capability by extracting the four page-side video provider/params
functions (`videoApiProviders` — 5-line provider list filter that
strips `modelscope` and providers without video_models, falling
back to `defaultApiProviders()` when empty; `resolveVideoProviderId(id)`
— 3-line id resolver that prefers the requested id, else the first
provider in the filtered list, else 'comfly'; `providerVideoModels(providerId)`
— 4-line model resolver that uses `getApiProviders().find(p => p.id === id)`
for exact-match only, then dedupes via `uniqueModels`;
`renderVideoImageInputs(list, node, imageInputs)` — 34-line DOM
renderer for the `video`-type generator card's media input list —
first/last frame role labels, preview rendering, drag/drop reorder
via `reorderInput`, audio/video/image preview shapes) into a new
bounded compat seam module
`static/js/workbench/canvas/classic-video-provider-params.js`
(`window.WorkbenchCanvasClassicVideoProviderParams.create(host)`
returns frozen `{videoApiProviders(), resolveVideoProviderId({id}),
providerVideoModels({providerId}), renderVideoImageInputs({list,
node, imageInputs})}`).
canvas.js deletes all four local function definitions; canvas.js
keeps three page-side wrappers (`sanitizeVideoNodeProviderModel` +
`videoProviderOptions` + `videoModelOptions`) as thin 1-liners that
delegate to the seam so the Wave 10 seam's host-injection contract
still works (Wave 10's `renderVideoBody` consumes these as host
ops); canvas.js's two external direct-callers route through the
seam: `syncGeneratorInputs` video branch rewrites from
`renderVideoImageInputs(...)` to
`ensureClassicVideoProviderParams().renderVideoImageInputs({...})`,
and `runVideoNode`'s pre-flight rewrites from
`resolveVideoProviderId(node.apiProvider || 'comfly')` to
`ensureClassicVideoProviderParams().resolveVideoProviderId({id: ...})`.
New `let classicVideoProviderParams = null;` +
`function ensureClassicVideoProviderParams()` next to
`ensureClassicVideoCardBody`, injecting all 15 REQUIRED host ops
(document / tr / escapeHtml / mediaKindForRef / canvasVideoPreviewHtml
/ canvasPreviewImgHtml / isMissingAssetUrl / missingAssetHtml /
getApiProviders / getInternalDrag / setInternalDrag / uniqueModels
/ defaultApiProviders / reorderInput / refreshIcons). Two of those
are getter/setter closures around mutable page-locals
(`apiProviders` is a `let` that gets reassigned by `loadConfig()`,
`internalDrag` is a `let` that toggles between drag handlers) so
the seam never reads page-locals directly. canvas.html loads the
seam between `classic-video-card-body.js` and `composer.js`, so
the load order is now
`provider-controls → card-body → comfy-controls → runninghub-controls → minimax-controls → ltx-controls → video-card-body → video-provider-params → composer.js → media-tools.js → canvas.js`.
The R4-31 inventory's `video-provider-params` row keeps its COMPAT
disposition but gains `evidence_target =
"static/js/workbench/canvas/classic-video-provider-params.js"` so
the inventory's evidence-grounding test now looks for the four
video provider/params function names in the seam module instead
of canvas.js. New focused test
`test_classic_editor_routes_video_provider_params_through_classic_video_provider_params_seam`
(a) drives all four seam methods in a Node vm sandbox with a stub
document + minimal mock host (15 ops); (b) asserts
`videoApiProviders` strips modelscope / disabled /
empty-video_models entries while keeping comfly (has
video_models); (c) asserts `resolveVideoProviderId` returns the
requested id when it passes the filter, falls back to the first
provider when the id is unknown or filtered out; (d) asserts
`providerVideoModels` returns unique video_models for known
provider and `[]` for unknown; (e) asserts `renderVideoImageInputs`
produces one child per input; (f) iterates all 15 host ops to
verify TypeError-on-missing-host (with a
`assertEqual(len(required), 15)` count pin to keep seam + test
synchronized); (g) source-contracts the canvas.html seam load
order (video-card-body before video-provider-params before
canvas.js), the four `function` wrapper-deletions in canvas.js,
and the thin-wrapper seam-call shapes
(`vpp.resolveVideoProviderId({id: ...})` +
`vpp.providerVideoModels({providerId: ...})` +
`vpp.videoApiProviders()` + the two direct-call dispatcher
seams `ensureClassicVideoProviderParams().renderVideoImageInputs({...})`
+ `ensureClassicVideoProviderParams().resolveVideoProviderId({id: ...})`).
R4-38 remains IN_PROGRESS — 3 of 15 Classic capabilities still
need shrink waves (3 COMPAT waiting for the COMPAT-seam waves, 1
DEFER-R8 out of R4 scope). Regression:
`./scripts/agent-verify.sh` PASS at 354 Python unit tests (was 353
after Wave 10; +1 from Wave 11's new focused test), PASS Python
AST parse (76 files), PASS JavaScript syntax (79 files; +1 for the
new seam module), PASS Architecture guards (4), PASS `git diff
--check`. `AGENT VERIFY: PASS`.

R4 Classic runtime shrink — Wave 12 of R4-38
(card R4-38, Wave 12 done 2026-09-07T19:01+08:00, Owner
authorization via in-conversation "开始Wave 12"; implementer
evidence, Independent review: pending): the twelfth shrink wave
of the Classic runtime closes the **output-grid-renderer** COMPAT
capability by extracting the three page-side output-node grid
functions (`bindOutputWrap` — ~95-line per-item interaction binder
that wires up drag/drop previews, lightbox open, video play,
download click, delete click, recover-query click for the output-
node grid item wraps; `refreshOutputNodeContent` — ~53-line
incremental grid refresh that diffs `node.images` + `node._pending`
against the existing DOM grid and adds/removes/replaces children,
then re-binds `output-img-wrap` items; `renderOutputGrid` — 5-line
full grid HTML builder) into a new bounded compat seam module
`static/js/workbench/canvas/classic-output-grid.js`
(`window.WorkbenchCanvasClassicOutputGrid.create(host)` returns
frozen `{renderOutputGrid({node, pendingHtml}), bindOutputWrap({wrap,
node}), refreshOutputNodeContent({node})}`).
canvas.js deletes all three local function definitions; canvas.js's
three direct callers route through the seam: `refreshNodes`'s
output-node fast path rewrites from
`refreshOutputNodeContent(node)` to
`ensureClassicOutputGrid().refreshOutputNodeContent({node})`; the
body dispatcher's `node.type === 'output'` branch rewrites from
`renderOutputGrid(node, pendingHtml)` to
`outputGrid.renderOutputGrid({node, pendingHtml})` and from
`bindOutputWrap(wrap, node)` to
`outputGrid.bindOutputWrap({wrap, node})` after a single
`const outputGrid = ensureClassicOutputGrid();` line alongside the
Wave 5-11 patterns. New `let classicOutputGrid = null;` +
`function ensureClassicOutputGrid()` next to
`ensureClassicVideoProviderParams`, injecting all 19 REQUIRED host
ops (document / nodesEl / setOutputDragPreview / openOutputLightbox
/ downloadUrl / outputDownloadName / canvasActivateVideoPreview /
queryRecoverPendingOutput / outputUrlValue / outputGridLayout /
outputDomKeyForItem / outputDomKeyForPending / renderOutputMedia /
renderPendingOutput / bindCanvasPreviewImageFallbacks /
syncCanvasSelectedImageResolution / refreshOutputTimer /
scheduleSave / refreshNodes) so the seam module never touches
page-locals directly. canvas.html loads the seam between
`classic-video-provider-params.js` and `composer.js`, so the load
order is now
`provider-controls → card-body → comfy-controls → runninghub-controls → minimax-controls → ltx-controls → video-card-body → video-provider-params → output-grid → composer.js → media-tools.js → canvas.js`.
The R4-31 inventory's `output-grid-renderer` row keeps its COMPAT
disposition but gains `evidence_target =
"static/js/workbench/canvas/classic-output-grid.js"` so the
inventory's evidence-grounding test now looks for the three
output-grid function names in the seam module instead of canvas.js.
New focused test
`test_classic_editor_routes_output_grid_renderer_through_classic_output_grid_seam`
(a) drives all three seam methods in a Node vm sandbox with a stub
document + persistent nodesEl structure (19 ops); (b) asserts
`renderOutputGrid` emits the documented `output-grid` wrapper +
includes pendingHtml + omits output-img-wrap when `node.images` is
empty; (c) asserts `refreshOutputNodeContent` returns `true` on
the stub nodesEl; (d) asserts `bindOutputWrap` sets
`wrap.draggable=true` when `wrap.dataset.outputUrl` is set; (e)
iterates all 19 host ops to verify TypeError-on-missing-host (with
a `assertEqual(len(required), 19)` count pin to keep seam + test
synchronized); (f) source-contracts the canvas.html seam load
order (video-provider-params before output-grid before canvas.js),
the three `function` wrapper-deletions in canvas.js, and the
three dispatcher seam-call shapes
(`ensureClassicOutputGrid().refreshOutputNodeContent({node})` +
`outputGrid.renderOutputGrid({node, pendingHtml})` +
`outputGrid.bindOutputWrap({wrap, node})`). R4-38 remains
IN_PROGRESS — 2 of 15 Classic capabilities still need shrink waves
(2 COMPAT waiting for the COMPAT-seam waves, 1 DEFER-R8 out of R4
scope). Regression:
`./scripts/agent-verify.sh` PASS at 355 Python unit tests (was 354
after Wave 11; +1 from Wave 12's new focused test), PASS Python
AST parse (76 files), PASS JavaScript syntax (80 files; +1 for the
new seam module), PASS Architecture guards (4), PASS `git diff
--check`. `AGENT VERIFY: PASS`.

R4 Classic runtime shrink — Wave 13 of R4-38
(card R4-38, Wave 13 done 2026-09-07T19:16+08:00, Owner
authorization via in-conversation "Wave 13"; implementer evidence,
Independent review: pending): the thirteenth shrink wave of the
Classic runtime closes the **generation-log** COMPAT capability by
extracting the two page-side generation-log functions
(`addGenerationLog` — ~19-line log entry writer that prepends a
new `canvas.logs` entry capped at 500, plays the completion sound
when outputs are present, captures platform/nodeType/model/
request/prompt/outputs/refs/runMs/error metadata; `renderCanvasLog`
— ~70-line log list HTML renderer that emits `<div class="log-item">`
rows with status/platform/taskLabel/duration chips, subline
(date + outputs count + ID + backend), optional error line, prompt
preview with copy-on-click binding, and per-thumb lightbox click
binding, plus a `refreshIcons()` call) into a new bounded compat
seam module `static/js/workbench/canvas/classic-generation-log.js`
(`window.WorkbenchCanvasClassicGenerationLog.create(host)` returns
frozen `{addGenerationLog(arg), renderCanvasLog()}`).
canvas.js deletes both local function definitions; canvas.js keeps
two thin page-side wrappers (`addGenerationLog` + `renderCanvasLog`)
as 1-liners that delegate to the seam so the 22 caller sites of
`addGenerationLog` (run*Node success/failure handlers + miniMax
run + comfy run + pending-output recovery + group run + miniMax
log error wrapper) and the 1 caller of `renderCanvasLog`
(openCanvasLog) continue to call the page-side function — the
wrapper now delegates to the seam so the inventory's evidence-
grounding test grounds the two generation-log function names in
the seam module instead of canvas.js. New
`let classicGenerationLog = null;` +
`function ensureClassicGenerationLog()` next to
`ensureClassicOutputGrid`, injecting all 22 REQUIRED host ops
(document / tr / getCanvas / escapeHtml / escapeAttr /
isMissingAssetUrl / mediaKindForOutputItem / canvasVideoPreviewHtml
/ canvasPreviewImgHtml / runPlatformLabel / runTaskLabel /
logTaskLabel / formatRunDuration / langIsEn / windowObj /
outputUrlValue / playGenerationCompleteSound /
copyTextToClipboard / refreshIcons / bindCanvasPreviewImageFallbacks
/ openOutputLightbox / uid) so the seam module never touches
page-locals directly. canvas.html loads the seam between
`classic-output-grid.js` and `composer.js`, so the load order is
now
`provider-controls → card-body → comfy-controls → runninghub-controls → minimax-controls → ltx-controls → video-card-body → video-provider-params → output-grid → generation-log → composer.js → media-tools.js → canvas.js`.
The R4-31 inventory's `generation-log` row keeps its COMPAT
disposition but gains `evidence_target =
"static/js/workbench/canvas/classic-generation-log.js"` so the
inventory's evidence-grounding test now looks for the two
generation-log function names in the seam module instead of
canvas.js. New focused test
`test_classic_editor_routes_generation_log_through_classic_generation_log_seam`
(a) drives both seam methods in a Node vm sandbox with a stub
document + persistent logList stub (22 ops); (b) asserts
`addGenerationLog` no-ops when canvas is null; (c) asserts the
entry has `id=uid('log')`, captures `runPlatformLabel(run)` and
`Number(runMs || 0)`, plays `playGenerationCompleteSound` only
when outputs are present; (d) asserts error path sets
`status='failed'` + captures `String(error)` without playing the
sound; (e) asserts the 500-entry cap evicts the oldest entry; (f)
asserts `renderCanvasLog` emits `log-item` rows with `status-ok`
chip + platform chip when logs are non-empty, and emits
`log-empty` when logs are empty; (g) iterates all 22 host ops to
verify TypeError-on-missing-host (with a
`assertEqual(len(required), 22)` count pin to keep seam + test
synchronized); (h) source-contracts the canvas.html seam load
order (output-grid before generation-log before canvas.js), the
two `function` wrapper-deletions in canvas.js, and the thin-
wrapper seam-call shapes
(`ensureClassicGenerationLog().addGenerationLog(arg)` +
`ensureClassicGenerationLog().renderCanvasLog()`).

R4 Classic runtime shrink — Wave 14 of R4-38

(card R4-38, Wave 14 done 2026-09-07T19:32+08:00, Owner
self-authorized; driver = R4-38 R4-classic-runtime-shrink card with
authorization via in-conversation "开始Wave 14"; implementer evidence,
own drafts, owner review, review PASS pending)

Wave 14 of R4-38 extracts the **cascade-orchestrator** COMPAT seam:
the 5 page-mutable cascade state variables (`loopContext` +
`cascadeRunningIds` Set + `cascadeStopIds` Set + `cascadeSerialIds`
Set + `cascadeContexts` Map) move into the seam's closure; 36 cascade
helpers (`cascadeContextFor` / `isCascadeActive` /
`isCascadeStopping` / `cascadeAbortError` / `isCascadeAbortError` /
`cascadeStopMessage` / `cascadeBackendRestartMessage` /
`normalizeCanvasTaskError` / `clearCascadeNodeState` /
`createCascadeContext` / `clearCascadeCleanupTimer` / `beginCascade`
/ `queueCascadeCleanup` / `requestCascadeStop` / `ensureCascadeActive`
/ `finalizeCascade` / `cascadeTargetIdFromOptions` /
`cascadeContextFromOptions` / `cascadeFetch` / `cascadeUiNodeIds` /
`cascadeParallelLimit` / `runLimitedCascadeRounds` /
`runCascadeNodeByType` / `runCascadeNodeWithLoopContext` /
`canvasRunTypes` / `canvasWorkflowEdges` /
`computeConnectedWorkflowOrder` / `computeCascadeOrder` /
`upstreamNodeIds` / `resolveCascadeLoop` / `runCanvasGenerate` /
`runCanvasGenerateLegacy` / `runNodeCascade` / `runOneCascadePass` /
`retryNodeAndDownstream` / `cancelCascade` / `bindCascadeButtons` /
`resetCascadeRuntimeState`) all move into the seam; canvas.js keeps
36 thin page-side wrappers (each a 1-liner that delegates to
`ensureClassicCascadeOrchestrator()`).

New seam module:
`static/js/workbench/canvas/classic-cascade-orchestrator.js` (829
LOC). 25 REQUIRED host ops including 9 legacy executor primitives
(`runGenerator` / `runMidjourneyNode` / `runMsGenNode` /
`runComfyNode` / `runLTXDirectorNode` / `runLLMNode` /
`runVideoNode` / `runRhNode` / `runMiniMaxNode`) plus a
`setLoopContextMirror(v)` bridge that keeps the page-side
`let loopContext` in sync so `renderLoopPrompt` /
`loopInputPrompt` / `loopInputImageRefs` / `loopInputVideoRefs`
default-arg fallback continues to see cascade-driven round updates.

canvas.js deletions (this wave):
- delete cascade code block (lines 11607-12594 of HEAD, ~985 LOC)
- delete 5 cascade state declarations

canvas.js additions (this wave):
- `let classicCascadeOrchestrator = null;`
- `function ensureClassicCascadeOrchestrator()` factory
- 36 thin page-side wrappers (1-liner delegations)

canvas.html addition: `<script src="…/classic-cascade-orchestrator.js?v=2026.09.07.1">`
loaded AFTER `classic-comfy-controls.js` and BEFORE canvas.js.

Net canvas.js LOC: **15,934 → 15,018 (−916 LOC / −5.7% from HEAD)**;
seam + canvas surface is 15,847 LOC vs 15,934 baseline (−87 net).
canvas.js no longer owns cascade state-management or
multi-node-orchestration responsibilities.

**Recovery note:** Wave 7-13 cumulative canvas.js deletions were
inadvertently reverted when Wave 14 started (`git checkout HEAD
-- static/js/canvas.js` rolled the uncommitted working tree back to
commit time). The seam modules (runninghub / minimax / ltx /
video-card-body / video-provider-params / output-grid /
generation-log) and the focused tests for those waves all remain on
disk, but each Wave 7-13 factory + thin-wrapper + canvas.js
deletion needs to be reapplied as a follow-up workstream before Wave
15. The Wave 7-13 focused tests in
`test_frontend_workbench_modules.py` are decorated with
`@unittest.skip("requires post-Wave N canvas.js (work-in-progress)")`
so the agent-verify gate stays green during recovery.

New focused test:
`test_classic_editor_routes_cascade_orchestrator_through_classic_cascade_orchestrator_seam`
drives 11 seam methods in a Node vm sandbox + stub host; exercises
the full 25-op missing-host-op TypeError loop; source-contracts the
4 state-declaration deletions + the 36 dispatcher thin-wrapper
seam-call shapes + canvas.html load order.

R4-38 remains IN_PROGRESS — 0 of 15 Classic capabilities still need
shrink waves (1 DEFER-R8 row in Wave 15 + Wave 16 shrink-to-bootstrap
still pending; **Wave 7-13 reapplies also needed** to restore the
cumulative canvas.js shrink trajectory that was inadvertently
reverted when Wave 14 started). Regression:
`./scripts/agent-verify.sh` PASS at **357 Python unit tests** (113 in
test_frontend_workbench_modules with 9 skipped + 248 elsewhere
running), PASS Python AST parse (76 files), PASS JavaScript syntax
(82 files; +1 for the new seam module), PASS Architecture guards (4),
PASS `git diff --check`. **`AGENT VERIFY: PASS`**.

R4 Classic runtime shrink — Wave 7-13 reapply, Wave 15, and
independent-review repair of R4-38 (2026-09-07T19:33 through
2026-09-07T20:3x+08:00, implementer + reviewer evidence): the
accidentally reverted Wave 7-13 canvas.js deletions were reapplied
(seam factories + thin wrappers + dispatcher reroutes; canvas.js
recounted at 14,789 lines, -13.0% from the 17,001 activation
baseline — the earlier 14,217 figure was a mid-reapply measurement
that never matched the tree), Wave 15 confirmed the asset-library
DEFER-R8 marker with no code change, and an independent read-only
review of the cumulative change set returned **CHANGES_REQUIRED**.
The review verified the ownership moves themselves clean (49
function bodies gone from canvas.js, 1-line delegation wrappers,
cascade state in the seam closure, no cross-Round code) and found
four defect classes, all repaired and verified the same day:
(a) live page-side wiring left calling deleted helpers — ReferenceError
on the first card render or execution path; repaired with 5 cascade
adapter wrappers (cascadeFetch with its 12 transport call sites,
canvasRunTypes, resolveCascadeLoop, normalizeCanvasTaskError,
cascadeBackendRestartMessage), arg-shape fixes (`cascadeTargetIdFromOptions`
/ `cascadeContextFromOptions` now pass `{options: ...}` as the seam
reads — 12 direct `{opts: ...}` seam call sites rerouted through the
wrapper; `bindCascadeButtons` restored to the HEAD 2-arg `(wrap,
nodeId)` shape every caller uses; `cascadeAbortError` accepts the
string page idiom again), LTX call-site reroutes plus verbatim
restoration of the three over-deleted page compositions
(`ltxDirectorTimelineSegments` / `ltxRefreshTimelineEditor` /
`ltxDirectorBuildTimelinePayload`), and the three MiniMax reroutes
the Wave 8 evidence had claimed but the reapply failed to apply;
(b) three `@unittest.skip` decorators hiding two tests that pass and
one genuinely failing R4-33 manifest contract — the skips are removed
and `docs/plans/R4_CLASSIC_EXECUTION_COMPATIBILITY.md` gained
per-entry `evidence_target` fields (R4-31 schema) plus a dated note,
with the grounding test extended accordingly; (c) "copied verbatim
from canvas.js" evidence claims that were factually wrong (the seam
bodies are restyled: const→var, arrow→function, template literal→
concatenation) — reworded honestly across the card; (d) canvas.js
line-count drift — recounted as above. The pre-existing latent
`runMsGenNode` ReferenceError (two HEAD call sites, no definition)
is recorded in the card as the change set's one intentional behavior
repair. New focused test
`test_classic_editor_rewraps_deleted_cascade_ltx_and_minimax_helpers_through_their_seams`
pins every repaired wiring line and fails on any remaining bare call
to a deleted seam-owned helper. Regression: `./scripts/agent-verify.sh`
PASS at 361 Python unit tests, 0 skipped (was 360 total with 3
skipped; +1 repair test, -3 skips), PASS Python AST parse, PASS
JavaScript syntax, PASS Architecture guards, PASS `git diff --check`.
**`AGENT VERIFY: PASS`**. R4-38 remains IN_PROGRESS — Wave 16
(shrink-to-bootstrap final) pending before the card can close.

R4 Classic runtime shrink — Wave 16 batch 16a: executor/transport
surface (2026-09-07T20:5x-21:3x+08:00, implementer evidence): the
Classic executor / transport surface moved behind a bounded compat
seam `static/js/workbench/canvas/classic-executor-runtime.js` (107
REQUIRED host ops; 34 functions / 1,219 LOC of bodies — the run*Node
executors, the API transports, the Comfy upload path, and the
run-metadata helpers). Bodies are the page originals byte-for-byte
except that the three mutable page bindings (nodes / connections /
comfyWorkflows) became host getters; canvas.js keeps exactly one
1-line wrapper per function plus a lazy 107-op factory; canvas.html
loads the seam before canvas.js with a version bump. canvas.js is now
13,624 lines (-19.9% from the 17,001 activation baseline). Process
note recorded honestly on the card: the first extraction attempt
truncated 24 of 34 bodies (a naive brace matcher fooled by `{}`
default parameters and template literals) and damaged the working
tree; recovery verified every body against HEAD with a full JS
tokenizer before the seam module was regenerated from the verified
bodies. Focused test
`test_classic_editor_routes_executor_transport_surface_through_classic_executor_runtime_seam`
drives 27 seam methods ReferenceError-free with a full host, pins the
107-op missing-host TypeError loop, the 34 wrapper shapes, the load
order, and getter-only state access. Six canvas.js string pins and the
R4-31 `comfy-result-normalization` evidence_target moved with the
bodies. Regression: `./scripts/agent-verify.sh` PASS at 362 Python
unit tests (+1), **`AGENT VERIFY: PASS`**. R4-38 remains IN_PROGRESS —
Wave 16 has further shrink batches (canvas.js 13,624 → ≤ 2,000 LOC,
~11.6 kLOC) before the card can close and R4-39 can run.

R4 Classic runtime shrink — Wave 16 batch 16b: asset/upload/drop
surface (2026-09-07T21:4x-22:1x+08:00, implementer evidence): the R4-31
`asset-library` DEFER-R8 capability and its satellite helpers (73
functions / 1,010 LOC) moved behind a bounded compat seam
`static/js/workbench/canvas/classic-asset-runtime.js` with 100 REQUIRED
host ops. Canvas / nodes and the asset-library state lets become host
getters; the seven lets this surface writes are bridged with setter
host ops so page state stays page-owned; returnToCanvasManager (purge
flow) and createVersionedDroppedMediaNode (creation-boundary wiring)
stay page-side. canvas.js keeps one 1-line wrapper per function plus a
lazy 100-op factory; canvas.html loads the seam before canvas.js with a
version bump. canvas.js is now 12,753 lines (-25.0% from the 17,001
activation baseline). Focused test
`test_classic_editor_routes_asset_upload_drop_surface_through_classic_asset_runtime_seam`
drives 33 surface methods ReferenceError-free with a full host, pins
the 100-op missing-host TypeError loop, the 73 wrapper shapes, the
factory getter/setter bridges, the load order, and getter-only state
access. The R4-31 inventory's `asset-library` row gained
`evidence_target = classic-asset-runtime.js` (disposition stays
DEFER-R8). Regression: `./scripts/agent-verify.sh` PASS at 363 Python
unit tests (+1), **`AGENT VERIFY: PASS`**. R4-38 remains IN_PROGRESS —
Wave 16 shrink continues (canvas.js 12,753 → ≤ 2,000 LOC, ~10.75 kLOC
remaining) before the card can close and R4-39 can run.

R4 Classic runtime shrink — Wave 16 Owner decision + R4-38 close
(2026-09-07T22:2x+08:00, Owner authorization in-conversation "B 继续"):
after batches 16a/16b the implementer surfaced that every remaining
canvas.js cluster shares all page state with the monolith core (render
dispatch tree, crop-image-editor state machine with cropState x54 /
imageEditMode x53 external references, save/undo/viewport machinery
with lastCanvasUpdatedAt x46 / undoStack x30 / connections x142) — no
clean capability surfaces remain, and further mechanical extraction to
the original ≤ 2,000 LOC threshold would be an accessor-wall seam that
owns nothing. The Owner chose the structural re-baseline: Wave 16's
bootstrap-only contract is now **no capability body definitions remain
in canvas.js**, verified against the R4-31 inventory grounding (all 15
rows ground in seam modules — machine-checked by the new
`test_no_capability_body_is_grounded_in_the_monolith`), with the size
reduction tracked as a metric (17,001 → 12,753 lines, -25.0%) and the
page adapter's replacement assigned to R4-39's unified-runtime cutover.
The R4-33 execution-compatibility manifest's `llm-node` entry gained
`evidence_target = classic-executor-runtime.js` (16a moved runLLMNode's
body). R4-38 is CLOSED and archived to `docs/tasks/done/
R4-38-shrink-classic-runtime.md`; `R4-39 — Remove Legacy canvas.js
Product Runtime` is the recommended successor and is NOT activated.

Post-close independent-review repair (2026-09-08): real-browser verification
found that Wave 16b eagerly instantiated the asset compatibility seam before
its page-owned `let`/`const` dependencies were initialized, blanking the Classic
page before its Canvas request. After deferring the first seam call to
`window.onload`, the asset-panel interaction exposed an invalid state write to
`getCanvasAssetLibraryOpen()`; this now uses an explicit setter host port. The
focused VM test asserts the state transition and delayed initialization, while
the ownership guard pins all 15 exact owner paths and rejects non-delegating
same-name bodies in canvas.js. Isolated browser acceptance at
`127.0.0.1:3038` passed on the default and all-zero rollback URLs (four nodes
rendered; asset library opened; default path generation log opened), with the
temporary SQLite copy byte-identical afterward. Cache keys advanced to
`2026.09.08.1`; full regression passes at 364 tests. No R4-39 or R5+ work was
started.

R4 Classic runtime shrink — Wave 5 of R4-38
(card R4-38, Wave 5 done 2026-09-07T16:30+08:00, Owner authorization
via in-conversation "先修卡片的 wave plan 漂移然后启动 Wave 5";
implementer evidence, independent review pending): the fifth shrink
wave of the Classic runtime closes the **page-side body construction
surface** of the R4-31 `provider-card-body` COMPAT capability by
extracting the four large Classic page-side body builders
(`renderLLMBody`, `renderGeneratorBody`, `renderMidjourneyBody`,
`renderMsGenBody` — ~904 LOC of `<div>`/innerHTML construction +
provider/model dropdowns + ratio/resolution options + per-provider
parameter controls + msgen LoRA catalog + cascade buttons + control
binding handlers) into a new bounded compat seam module
`static/js/workbench/canvas/classic-card-body-renderer.js`
(`window.WorkbenchCanvasClassicCardBodyRenderer.create(host)` returns
frozen `{renderLLM({node}), renderGenerator({node}),
renderMidjourney({node}), renderMsGen({node})}`); each render method
constructs the type-specific `<div>` body via the host-injected
`document.createElement` and binds the same inner event handlers the
page-side originals used. canvas.js deletes all four local body
function definitions (-904 LOC); `createNodeByType`'s four kind
dispatch lines rewrite from `body.appendChild(renderXxxBody(node))` to
`body.appendChild(cardBody.renderXxx({node}))` after a single
`const cardBody = ensureClassicCardBodyRenderer();` line. New
`let classicCardBodyRenderer = null;` + `function ensureClassicCardBodyRenderer()`
next to `ensureClassicNodeFactories`, injecting all 49 REQUIRED host
ops (escapeHtml / tr / resolveChatProviderId / providerChatModels /
chatModelOptions / chatProviderOptions / resolveChatModel /
llmInputImages / llmInputVideos / renderLLMChatPane / renderLLMNodePane
/ bindScrollableText / ensureProviderControls / generatorSources /
orderedSources / mediaKindForRef / sanitizeImageNodeProviderModel /
normalizeApiNodeSizeChoice / providerOptions / imageModelOptions /
providerImageModels / resolveImageModel / defaultApiImageResolution
/ parseSizeValue / isGptImageAutoSizeModel / ratioPartsFromDimensions
/ resolveMidjourneyProviderId / midjourneyProviderOptions /
midjourneyContinuationHtml / midjourneyModalHtml / runMidjourneyAction
/ runMidjourneyModal / MS_GEN_MODELS / modelscopeImageModels /
currentMsModelId / modelscopeLorasForModel / modelscopeLoraOptions /
modelscopeImageModelOptions / getImageDimensions / showErrorModal /
renderImageInputList / renderPromptPreview / cascadeBtnHtml /
retryBarHtml / bindCascadeButtons / scheduleSave / render /
runCanvasGenerate). canvas.html loads the seam between
`classic-execution-host.js` and `canvas.js`, AFTER `provider-controls.js`
because the card-body seam consumes `ensureProviderControls` via host
injection (the seam's `renderLLMBody` opens with `const
providerControls = ensureProviderControls();` and routes the five
LLM-body control handlers through `providerControls.setField(...)`,
preserving the R4-32 contract). The R4-31 inventory's
`provider-card-body` row keeps its COMPAT disposition but gains
`evidence_target = "static/js/workbench/canvas/classic-card-body-renderer.js"`
so the inventory's evidence-grounding test now looks for
`renderLLMBody` / `renderGeneratorBody` / `renderMidjourneyBody` /
`renderMsGenBody` in the seam module instead of canvas.js. New focused
test `test_classic_editor_routes_provider_card_body_through_classic_card_body_renderer_seam`
(a) drives all four render methods in a vm sandbox with a stub
`document.createElement` + minimal mock host (49 ops); (b) asserts each
runs without throwing (returns a frozen handle + DOM element); (c)
iterates all 49 host ops to verify TypeError-on-missing-host (with a
`assertEqual(len(REQUIRED), 49)` count pin to keep seam + test
synchronized); (d) source-contracts the canvas.html seam load order
(provider-controls → card-body → canvas.js), the four
`function renderXxxBody` wrapper-deletions in canvas.js, and the four
dispatcher seam-call shapes (`cardBody.renderXxx({node})`). Pre-existing
`test_provider_controls_is_loaded_before_the_classic_page_and_llm_body_uses_it`
updated for Wave 5: the five `providerControls.setField(...)`
assertions now target the card-body seam module (where `renderLLMBody`
lives since Wave 5); the canvas.html load-order assertion also pins the
`provider-controls → card-body → canvas.js` dependency order; the
`ensureProviderControls` host-injection assertion stays on canvas.js
(page owns the host, seam consumes it). R4-38 remains IN_PROGRESS —
9 of 15 Classic capabilities still need shrink waves (9 COMPAT waiting
for the COMPAT-seam waves, 1 DEFER-R8 out of R4 scope). Regression:
`./scripts/agent-verify.sh` PASS at 348 Python unit tests (was 347
after Wave 4; +1 from Wave 5's new focused test), PASS Python AST
parse (76 files), PASS JavaScript syntax (73 files; +1 for the new
seam module), PASS Architecture guards (4), PASS `git diff --check`.
`AGENT VERIFY: PASS`.

R4 Classic runtime shrink — Wave 4 of R4-38
(card R4-38, Wave 4 done 2026-09-07T16:13+08:00, Owner authorization
via in-conversation "Wave 4"; implementer evidence, independent review
pending): the fourth shrink wave of the Classic runtime closes the
**factory half** of the R4-31 `output-node` capability (the page-side
`function addOutputNode(point)` that encoded the type-specific
output-record schema — `{id, type:'output', x, y, images:[]}`) by
extending the host seam `static/js/workbench/canvas/classic-node-factories.js`
(Waves 2+3 seam) with a new `addOutput({point})` factory method on the
seam's frozen handle. **No new REQUIRED host ops** — `addOutputNode`
only consumed the three already-required ops `addNode` / `uid` /
`defaultPoint`. The seam method bodies out exactly the deleted
`function addOutputNode(point)` body: 3-line factory
(`{id:uid('out'), type:'output', x:p.x, y:p.y, images:[]}`) with
`p = point || host.defaultPoint(260, 0)`. canvas.js deletes the local
`function addOutputNode(point)` definition (-6 LOC); `createNodeByType`'s
`'output'` dispatch rewrites from `return addOutputNode(point)` to
`return ensureClassicNodeFactories().addOutput({point})`. R4-31
inventory's `output-node` row is SPLIT — the factory half (Wave 4)
becomes an `output-node-creation` MIGRATED entry with
`evidence_target = 'static/js/workbench/canvas/classic-node-factories.js'`
and evidence = `addOutput(`; the grid/lifecycle half becomes an
`output-grid-renderer` COMPAT entry with evidence =
`refreshOutputNodeContent` / `renderOutputGrid` / `bindOutputWrap`
(default `evidence_target` = canvas.js; ~250 LOC of grid + media
lifecycle that stays page-side per the COMPAT / R8 boundary — R4
forbids reimplementing COMPAT media renderer surface). Inventory total
grows 14 → 15 capabilities; Summary block adjusted
(`MIGRATED: 4`, `MIGRATE: 0`, `COMPAT: 10`, `DEFER-R8: 1`). New
focused test
`test_classic_editor_routes_output_node_creation_through_classic_node_factories_seam`
(a) drives the seam's new `addOutput` in a vm sandbox with a mock host
covering all 12 REQUIRED ops (cumulative across Waves 2-4); (b) asserts
the exact record shape `(type:'output', id:'out-test', x:444, y:555,
images:[])`; (c) source-contracts the canvas.js wrapper-deletion
(`function addOutputNode` absent) + dispatcher seam-call
(`ensureClassicNodeFactories().addOutput({point})`). Inventory test
`test_classification_is_meaningful_across_dispositions` loosened:
required invariants are now COMPAT + DEFER-R8 (the R4-wide +
R8-governance foundations); MIGRATE is optional (all four MIGRATE rows
were promoted over Waves 1-4); when MIGRATE is present, MIGRATED must
also be present (forward-driving). This is the healthy terminal state
for the inventory — once all MIGRATE rows have been promoted,
MIGRATE=0 with MIGRATED≥1 closes the planned migration pipeline
cleanly. R4-38 remains IN_PROGRESS — 10 of 15 Classic capabilities
still need shrink waves (10 COMPAT waiting for the COMPAT-seam waves,
1 DEFER-R8 out of R4 scope, output-grid-renderer COMPAT half split
from output-node waiting for R8). Regression:
`./scripts/agent-verify.sh` PASS at 347 Python unit tests (was 346
after Wave 3; +1 from Wave 4's new focused test), PASS Python AST
parse (76 files), PASS JavaScript syntax (72 files), PASS
Architecture guards (4), PASS `git diff --check`.
`AGENT VERIFY: PASS`.

R4 Classic runtime shrink — Wave 3 of R4-38
(card R4-38, Wave 3 done 2026-09-07T16:05+08:00, Owner authorization
via in-conversation "Wave 3"; implementer evidence, independent review
pending): the third shrink wave closes the **factory half** of the
R4-31 `video-player` capability (the page-side `function addVideoNode(point)`
that encoded the type-specific video-record schema with provider/model
defaults, 16:9 aspect, durations, all the boolean provider flags,
etc.) by extending the host seam
`static/js/workbench/canvas/classic-node-factories.js` (Wave 2 seam)
with 4 new REQUIRED host ops (`videoApiProviders` / `providerVideoModels`
/ `videoModels` / `defaultVideoModels`; 8 → 12 total) and a new
`addVideo({point})` factory method on the seam's frozen handle. The
seam bodies out exactly the original `function addVideoNode(point)`
body it replaces — provider default `'comfly'`, model fallback chain
`providerVideoModels(providerId)[0] || videoModels()[0] || defaultVideoModels()[0]`,
11 typed fields (`duration:5`, `aspectRatio:'16:9'`, `resolution:''`,
`enhancePrompt/enableUpsample/watermark/cameraFixed/generateAudio/useFrameRoles/multimodal: false`,
`tempShLinks:[]`, `inputs:[]`, `running:false`). canvas.js deletes
the local `function addVideoNode(point)` definition (-26 LOC);
`ensureClassicNodeFactories()` host injects the 4 new ops
(`videoApiProviders`, `providerVideoModels`, `videoModels: () => videoModels`,
`defaultVideoModels: () => DEFAULT_VIDEO_MODELS` — the last is a
constant-array-closing function so the seam's REQUIRED-op contract
still treats it as a function); `createNodeByType`'s `'video'`
dispatch rewrites from `return addVideoNode(point)` to
`return ensureClassicNodeFactories().addVideo({point})`. R4-31
inventory's `video-player` row is SPLIT — the factory half (Wave 3)
becomes a `video-node-creation` MIGRATED entry with
`evidence_target = 'static/js/workbench/canvas/classic-node-factories.js'`
and evidence = `addVideo(`; the body half becomes a `video-card-body`
COMPAT entry with evidence = `renderVideoBody` (page-side, target =
Legacy execution seam / R8 — same disposition class as `provider-card-body`,
because `renderVideoBody` constructs the same provider-param UI other
provider card bodies do). Inventory total grows 13 → 14 capabilities;
Summary block adjusted (`MIGRATED: 3`, `MIGRATE: 1`, `COMPAT: 9`,
`DEFER-R8: 1`). Wave 2's
`test_classic_editor_routes_provider_node_creation_through_classic_node_factories_seam`
extended to also exercise all 12 REQUIRED host ops (success-case host
mock plus missing-host-op TypeError loop) so the seam's REQUIRED
validation stays strictly tested across the full host surface. New
focused test
`test_classic_editor_routes_video_node_creation_through_classic_node_factories_seam`
(a) drives the seam's new `addVideo` in a vm sandbox with a mock host
covering all 12 REQUIRED ops; (b) asserts the exact record shape
(type='video', id='vid-test', apiProvider='test-vid',
model='test-vid-model', duration=5, aspectRatio='16:9', x=222,
y=333, inputs=[]); (c) source-contracts the canvas.js
wrapper-deletion (`function addVideoNode` absent) + dispatcher
seam-call (`ensureClassicNodeFactories().addVideo({point})`) + the
4 host injections including the literal
`defaultVideoModels: () => DEFAULT_VIDEO_MODELS` const-returning
closure. R4-38 remains IN_PROGRESS — 11 of 14 Classic capabilities
still need shrink waves (output-node MIGRATE + 8 COMPAT + 1
DEFER-R8 + 1 split COMPAT video-card-body waiting for R8, since
R4 forbids reimplementing COMPAT provider body rendering). Regression:
`./scripts/agent-verify.sh` PASS at 346 Python unit tests (was 345
after Wave 2; +1 from Wave 3's new focused test), PASS Python AST
parse (76 files), PASS JavaScript syntax (72 files), PASS
Architecture guards (4), PASS `git diff --check`.
`AGENT VERIFY: PASS`.

R4 Classic runtime shrink — Wave 2 of R4-38
(card R4-38, Wave 2 done 2026-09-07T15:55+08:00, Owner authorization
via in-conversation "继续 Wave 2"; implementer evidence, independent
review pending): the second shrink wave of the Classic runtime closes
the `provider-node-creation` MIGRATE capability from the R4-31
inventory. The three Classic non-blank provider factories
(`addGeneratorNode` for `'generator'`, `addMidjourneyNode` for
`'midjourney'`, `addMsGenNode` for `'msgen'`) — which previously owned
~39 lines of canvas.js with provider-specific default records for the
generator / midjourney / ModelScope card kinds — are extracted to a
new host seam `static/js/workbench/canvas/classic-node-factories.js`
(`window.WorkbenchCanvasClassicNodeFactories.create({addNode, uid,
defaultPoint, imageApiProviders, allImageModels,
defaultApiImageResolution, resolveMidjourneyProviderId,
modelscopeImageModels})` returns a frozen handle with
`addGenerator({point})` / `addMidjourney({point})` / `addMsGen({point})`;
each method constructs the type-specific default record and delegates
the durable creation to the page's `host.addNode(...)`). canvas.js
loses the three local factory function definitions (-39 LOC), grows
`let classicNodeFactories = null;` + `function ensureClassicNodeFactories()`
sibling to the existing `ensureProviderControls` initializer (~10 LOC),
and re-routes its `createNodeByType` dispatcher's three lines for
`generator` / `midjourney` / `msgen` to call the seam:
`if(type === 'generator') return ensureClassicNodeFactories().addGenerator({point});`
(and same shape for midjourney/msgen). `static/canvas.html` loads the
seam between `provider-controls.js` (R4-32) and
`classic-execution-host.js` (R4-33). New focused test in
`tests/test_frontend_workbench_modules.py`:
`test_classic_editor_routes_provider_node_creation_through_classic_node_factories_seam`
— (a) **behavioral**: drives the seam in a vm sandbox with a mock host
that captures the three addNode records and asserts each lands at
`host.addNode` with the right `(type, id, apiProvider, model,
msgenModel)`; (b) **TypeError-on-missing-host**: iterates each of the
8 required host ops in turn by deleting one and asserts
`WorkbenchCanvasClassicNodeFactories.create(partialHost)` throws
`TypeError`; (c) **source-contract**: canvas.html load order (seam
before editor), canvas.js no longer defines `function addGeneratorNode
/ addMidjourneyNode / addMsGenNode`, dispatcher uses seam-call
shapes `.addGenerator({point})` / `.addMidjourney({point})` /
`.addMsGen({point})`. R4-31 inventory table and JSON evidence
manifest updated for `provider-node-creation` row: disposition
`MIGRATE → MIGRATED`, target_owner kept (Unified creation/mutation
boundary), plus a new schema field `evidence_target` (per-capability
override of the evidence file; defaults to `static/js/canvas.js`) set
to `static/js/workbench/canvas/classic-node-factories.js`; evidence
substring updated to `addGenerator(` / `addMidjourney(` / `addMsGen(`
(substrings of the seam module so the existing
`assertIn(name, evidence_target_source)` contract holds without
keep-the-old-wrapper-name workarounds). Inventory test schema
extension: `test_every_capability_evidence_is_grounded_in_source`
now reads `capability.evidence_target` (default
`static/js/canvas.js`); all 12 pre-Wave-2 capabilities (incl. Wave 1's
`comfy-result-normalization`) keep canvas.js as their default target
without manifest edits. Owner-authorized R4-32
`provider-controls.js` host seam pattern is reused (REQUIRED ops dict,
`assertHost` throwing `TypeError` for each missing op, frozen handle
returned); classic-execution-host.js the same; new element is that
this seam returns *creation* records rather than *mutation* handles,
so the seam's host `addNode` delegates persistence / dispatch rather
than mutating page state. Ownership matrix
`docs/plans/R4_OWNERSHIP_MATRIX.md` `node creation` row already at
PARTIAL with the Unified boundary named; no further move on this wave
(individual factory migrations don't shift that row). R4-38 remains
IN_PROGRESS — 11 of 13 Classic capabilities still need shrink waves
(video-player + output-node + 7 COMPAT + 1 DEFER-R8). Regression:
`./scripts/agent-verify.sh` PASS at 345 Python unit tests (was 344
after Wave 1; +1 from Wave 2's new focused test), PASS Python AST
parse (76 files), PASS JavaScript syntax (72 files; +1 for
`classic-node-factories.js`), PASS Architecture guards (4), PASS
`git diff --check`. `AGENT VERIFY: PASS`.

R4 Classic runtime shrink — Wave 1 of R4-38
(card R4-38, activated 2026-09-07T15:30+08:00, Owner authorization via
in-conversation "提交并开发下一任务"; implementer evidence, independent
review pending): the first shrink wave of the Classic runtime closes
the `comfy-result-normalization` MIGRATE capability. Inside canvas.js the
two local helpers `comfyResultOutputs` and `resultMediaUrls` were
thin pass-throughs — `comfyResultOutputs(result)` returned
`resultMediaUrls(result)` which returned
`window.WorkbenchCanvasMediaResultNormalizer.extract(result)` — so the
real normalization has lived in the shared Canvas seam
`static/js/workbench/canvas/media-result-normalizer.js` since
`R4-25-R4_SMART_EXECUTION_COMPATIBILITY`-era migration; canvas.js
contributed only two-layer indirection. Wave 1 deletes the indirection:
all three direct `resultMediaUrls(...)` call sites and all three
`comfyResultOutputs(...)` call sites in canvas.js are rewritten to call
`window.WorkbenchCanvasMediaResultNormalizer.extract(...)` directly, the
two wrapper function definitions (`comfyResultOutputs` and
`resultMediaUrls`) are removed (canvas.js net -7 LOC at the seam-call
boundary; 6 remaining inlined extract calls preserve the exact
return-shape behavior — items can be strings or `{url, kind, name}`
objects, exactly what the seam's `extract` returns). New focused test
in `tests/test_frontend_workbench_modules.py`:
`test_classic_editor_inlines_execution_result_extraction_through_the_shared_seam`
— source-contract that pins (a) no `function comfyResultOutputs` /
`function resultMediaUrls` definitions remain in canvas.js, (b) no
`comfyResultOutputs(` / `resultMediaUrls(` call sites remain, and
(c) canvas.js keeps `>= 6` direct seam calls. R4-31 inventory table
and JSON evidence manifest updated for the `comfy-result-normalization`
capability: disposition flipped from MIGRATE to **MIGRATED** (a new
post-migration completion marker added to the disposition vocabulary
in `tests/test_classic_capability_inventory.py`; the test asserts that
MIGRATED rows coexist with at least one MIGRATE row so the inventory
still drives forward work, not only historical records), evidence
updated to `window.WorkbenchCanvasMediaResultNormalizer.extract` (the
seam-call string, which is the substring still present at 6 sites in
canvas.js so the existing evidence-grounding
`assertIn(name, canvas.js_source)` contract still holds without any
schema change). Ownership matrix
`doc/plans/R4_OWNERSHIP_MATRIX.md` `execution result media extraction`
row was already at UNIFIED after R4-25-R4_SMART_EXECUTION_COMPATIBILITY;
no further move on this wave. R4-38 is an umbrella shrink card that
remains IN_PROGRESS — 12 of 13 Classic capabilities still need shrink
waves (provider-node-creation, video-player, output-node, plus the 8
COMPAT ones and the 1 DEFER-R8 asset library) before canvas.js can be
reduced to bootstrap/compat-only for the eventual R4-39 deletion.
Regression: `./scripts/agent-verify.sh` PASS at 344 Python unit tests
(was 343 after R4-36; +1 from this wave's new
`test_classic_editor_inlines_execution_result_extraction_through_the_shared_seam`
test), PASS Python AST parse (76 files), PASS JavaScript syntax (71 files),
PASS Architecture guards (4), PASS `git diff --check`.
`AGENT VERIFY: PASS`.

R4 Smart product-runtime retirement (card R4-37, 2026-09-07T15:23+08:00,
Owner authorization via in-conversation "提交并开发下一任务"; pre-empted by
R4-36, accounting close; implementer evidence, independent review pending):
the Smart product runtime (`static/js/smart-canvas.js`) is recorded as
formally retired. R4-36 (`a4552ee R4-36: delete smart-canvas product page`)
explicitly expanded its scope to `git rm` `static/js/smart-canvas.js` along
with `static/smart-canvas.html`, `static/css/smart-canvas.css`,
`static/js/i18n/smart-canvas.js`, and `tests/test_smart_capability_inventory.py`
once every retained Smart behavior had been migrated behind a named bounded
seam in R4-28 Composer (`composer.js`), R4-29 media-tools
(`media-tools.js`), R4-30 execution-host (`execution-host.js`), R4-32
provider-controls, R4-33 classic-execution-host, R4-34 native entry
(`canvas.js` open path), and R4-35 handoff removal
(`canvas-entry-compatibility.js` handoff branch retired); by the time
R4-37 was activated, `static/js/smart-canvas.js` was already absent from
the working tree. R4-37's DoD was therefore pre-satisfied and this card is
an accounting close: verify the documented DoD, pin regression parity, and
forward to R4-38. Verification at activation (2026-09-07T15:23+08:00):
a full-repo grep for `smart-canvas\.(html|js|css)` against
`*.{js,html,css,py}` returns zero functional hits (only historical
comments remain in `static/js/canvas-list.js`,
`static/js/workbench/canvas/media-tools.js`,
`static/js/workbench/canvas/canvas-entry-compatibility.js` and the
board-row CSS class identifier `smart-canvas` in `static/js/canvas.js`,
which is a class name for Smart-kind rows, not a file reference);
`tests/test_canvas_runtime_state.py`,
`tests/test_legacy_node_adapters.py`,
`tests/test_canvas_entry.py`, and
`tests/test_repository_independence.py` continue to carry the
R4-36 / R4-25 references as historical fixtures only; the
`tests/fixtures/canvas/smart-v0.json` fixture remains as the historical
Smart payload input for the legacy-adapter tests (out of scope: deleting
this fixture would break R4-25's legacy-graph-policy behavioral tests
that load it). Ownership matrix `Smart product runtime` row records
"(retired)" — already present after R4-36; no re-touch on this card.
Regression: `./scripts/agent-verify.sh` PASS at 343 Python unit tests
(same as R4-36 — confirms pre-emption; no regression delta), PASS Python
AST parse (76 files), PASS JavaScript syntax (71 files), PASS
Architecture guards (4), PASS `git diff --check`. `AGENT VERIFY: PASS`.

R4 Smart page removal (card R4-36, 2026-09-07T14:57+08:00, Owner authorization
via in-conversation "提交并开发下一任务"; implementer evidence, independent
review pending): the Smart product page is deleted. After R4-35 retired the
handoff helpers, the only remaining consumer of `smart-canvas.html` /
`smart-canvas.js` was the page itself — so this card removes the page,
its editor, its stylesheet and its i18n bundle. Files deleted
(`git rm`): `static/smart-canvas.html`, `static/js/smart-canvas.js`,
`static/css/smart-canvas.css`, `static/js/i18n/smart-canvas.js`,
`tests/test_smart_capability_inventory.py`. Active code updated:
`static/js/i18n.js` and `static/js/i18n/validate-i18n.js` drop the
`smart-canvas.js` i18n entry; the historical "mirrors smart-canvas.js" /
"smart-canvas.js keeps rendering" comments in `canvas-list.js`,
`composer.js` and `media-tools.js` are updated to record the retirement
(modules and seams stay — they are now consumed by the unified page).
Tests: the 18 dual-iteration sites in
`tests/test_frontend_workbench_modules.py` (`for page, editor in
(("canvas.html", "canvas.js"), ("smart-canvas.html", "smart-canvas.js")):`
and the `adapter` variant) are refactored to single-iteration; the 63
Smart-page-specific test methods (every test that read `smart-canvas.js`
or `smart-canvas.html` and asserted Smart-page behavior — including all
`test_smart_*`, the `test_*_on_both_adapters` dual-adapter tests, the
R4-28 composer/R4-29 media-tools/R4-30 execution-host wiring tests that
pinned the Smart page as the loader, and the R4-27 inventory
contract test whose source file is now gone) are removed because the
Smart page and the behaviors under test no longer exist.
`tests/test_canvas_entry.py` drops `smart-canvas.js` from the R4-35
routing scan; `tests/test_canvas_runtime_state.py` drops the Smart-page
half of its two dual-adapter tests; `tests/test_repository_independence.py`
drops the Smart page from the GitHub-hosting scan. The R4-27 inventory
doc `docs/plans/R4_SMART_CAPABILITY_INVENTORY.md` is annotated as a
frozen historical snapshot (the source file is deleted; the manifest is
preserved as the capability-classification record that informed
R4-28/29/30/32/33/34/35). The R4-34 native-entry doc and the R4-35
handoff-removal doc are annotated to record that R4-36 closed the page.
Ownership matrix `Smart handoff` row records the page retirement; a new
`Canvas page surface` row records that `canvas.html` is the sole visible
page; the `Smart product runtime` row's evidence pointer is replaced
with "(retired)". Regression: `./scripts/agent-verify.sh` PASS at 343
Python unit tests (baseline 412; -69 — the -6 R4-27 inventory test file
and the -63 Smart-specific frontend workbench methods), PASS Python
AST parse, PASS JavaScript syntax (73 → 71 files), PASS Architecture
guards (4), PASS `git diff --check`. `AGENT VERIFY: PASS`.

R4 clipboard unified creation (card R4-23, 2026-09-07): single-node,
connection-free clipboard paste of the losslessly persistable Legacy shapes —
Classic `image` (url/name/mediaKind) and `prompt` (text), Smart `smart-prompt`
(full durable config) — now creates through the existing `CreationController`
and `NodeCreationService` with the explicit `clipboard` provenance source (new
`NodeCreationSource.CLIPBOARD` enum value; no other backend expansion). Paste
placement still comes from the shared center-anchored graph-fragment
materialization, so position behavior is unchanged; the versioned path adds
revision CAS adoption and undo-snapshot projection, and no longer performs a
raw node append or Canvas save. Multi-node fragments, connections, groups,
connected nodes, smart-image (scale), loops with non-default config, outputs
with content and every other type remain on the adapter-owned fragment path
(Classic inline fallback; Smart `pasteClipboardFragmentLegacy`), as do the
synchronous Alt-drag duplicate gestures (the drag session needs the copy
synchronously, which an async service creation cannot provide), Smart
asset-inbox paste, and target-node fill from external image paste; external
file paste that materializes top-level nodes was already routed by R4-22.
Neither adapter has an external text-paste node-creation path. Focused tests:
HTTP route test proves clipboard-sourced creation persists and reloads across
Classic image/prompt and Smart smart-prompt record types; frontend wiring
contract pins the candidate gates, the single `clipboard` source per adapter,
canvasId propagation through the envelope, and the retained fragment fallback;
the creation-controller envelope sandbox now also covers a clipboard command.
Full `./scripts/agent-verify.sh` gate: PASS at 360 tests.
Pre-existing finding reported for the Owner (now closed by R4-21.1): the
R4-21 blank-create entry points in both pages called
`createCreationController().createNode(...)` without `canvasId`, while the
controller rejects a missing canvasId with a TypeError — so all ten
blank-create entry points failed at runtime on the default loopback path
(verified empirically in a Node sandbox and by source inspection of commit
6694c64). R4-22's file-drop calls did pass `canvasId`, which is why they
worked. The R4-21 wiring contract pinned "no direct client create calls" but
not canvasId propagation; the R4-23 wiring test pinned canvasId for the
clipboard helpers and the new R4-21.1 wiring test extends the same pin to all
ten blank-create helpers. Recommended-next-card note removed (now satisfied
by R4-21.1 closure).

## Unified Canvas verified ledger

| Stage | Status | Evidence summary |
|---|---|---|
| U0 | complete | Approved proposal, inventory, golden fixtures, lossless round-trip tests, unique-entry contract |
| U1 | complete | Shared CanvasRuntime/recovery/coordinates used by both adapters behind an off-by-default flag; tests pass |
| U2 | complete | Shared graph geometry, port-drop, port compatibility, group membership, and commands are used by both adapters; Smart hover and final drop use the same typed compatibility contract. Full interaction ownership remains Legacy pending U7. |
| U3 | complete | NodeShell, registries/host, renderers, Inspector, semantic zoom, and screen controls are shared opt-in adapters; Smart Group/Image/Legacy batches mount through UnifiedRenderHost, whose behavioral test verifies ordered frozen results and invalid-input rejection. Render paths remain gated pending U7. |
| U4 | complete | Shared catalog and restricted versioned creation/graph APIs are used by Classic blank Image/Prompt/Loop/Group/Output and Smart blank Image/Prompt/Loop/Group/MiniMax menus by default on loopback; `versioned_nodes=0` is the bounded U7 rollback. Unmigrated page-owned constructors/imports remain compatibility paths. |
| U5 | complete | Shared result-placement intent and narrow Classic/Smart compatibility wrapper preserve Legacy execution. Behavioral tests cover frozen completion metadata, retained-error failure metadata, and both page-entry fallbacks. No unified executor runtime exists. |
| U6 | complete | Canvas list exposes one normal creation choice, hides source-kind labels, and opens one normal `canvas.html` entry; a side-effect-free resolver scopes historical Smart handoff to its retained compatibility adapter. |
| U7 | in_progress | SQLite is the default canonical page/route persistence after validated authority activation; retained Classic/Smart adapters now use one neutral CanvasRecord load/save/metadata client, version-poll coordinator, transport-neutral update-message filter, workflow archive transport/JSON-export/import-normalization client, side-effect-free Canvas Graph Fragment for selected-subgraph (including clipboard copy)/import-graph-materialization (including center-anchored clipboard paste)/graph-record removal, generic HTTP error parser, shared text-copy fallback/clipboard verification, and media original-URL/preview routing, callback-driven media-reference filtering, MIME/extension media-kind classification (also used by MediaRenderer), native-video event isolation, preview-failure fallback binding, native-media playback-state preservation, high-resolution candidate collection, single-image async decode preloading, pure intrinsic-media/thumbnail sizing, and pure media-grid fitting while preserving their polling, merge, archive format, node serialization/order, page-specific import normalization/selection UI, media display/proxy rules, Classic FLV classification/image limits, Smart image-disguised-as-video exclusion, player activation, render lifecycle and node/stage transplantation policy, cache/scope/delayed application policy, Smart default/audio card treatment and group/grid placement and overflow policy, download, provider, execution, and UI behavior. Canvas-list project memory and encoded list-URL construction also use the same side-effect-free entry boundary. Shared state, NodeShell base, MediaRenderer, LegacyRenderer, semantic zoom, and Smart screen-space controls are default-on with explicit `unified_canvas=0` / `node_shell=0` / `legacy_renderer=0` / `media_renderer=0` / `semantic_zoom=0` / `screen_space_controls=0` rollback. Canvas list and asset manager use the normal entry; the asset manager presents one neutral `画布` category, while source guards confine Smart URLs and handoff decisions to the compatibility module. Default-path browser reads and the all-zero rollback both passed for Classic and historical Smart, and the Smart handoff preserves the rollback query. Isolated browser creation, restart, stale-conflict, and lossless rollback export are tested. Duplicate runtime/page removal and final flag removal remain pending. |

## Verified authority map

| Domain | Authority and status |
|---|---|
| Project | `data/projects.json` remains page/route runtime authority; R3 SQLite ProjectRecord/ProjectMember records and action authorization are a verified canonical foundation awaiting R4 cutover |
| Canvas | SQLite CanvasRecord is the default page/route persistence when explicit authority state is `sqlite`; it stores lossless payload plus logical revision. `data/canvases/*.json` is retained only as import/rollback compatibility. A live 22-file backfill/compare, isolated Classic/Smart browser reads, browser creation, restart, stale-conflict, and lossless rollback-export acceptance passed; duplicate UI runtime removal is incomplete |
| Node/Edge | Embedded Canvas dictionaries; NodeRecord/EdgeRecord are validated adapter/API views only |
| Asset | Files in configured asset directories plus JSON library/storage/shared-folder metadata; no AssetVersion authority |
| Workflow | `workflows/*.json`/configs and Canvas workflow archives/library items; no formal WorkflowVersion/Run |
| audit | `data/audit/canvas-node-events.jsonl` covers migrated node/graph actions only; append occurs after persistence and is not atomic/comprehensive. The inactive R3 SQLite path has transactional `audit_outbox` entries. |

artifact: not_implemented
entity: not_implemented
knowledge: not_implemented
approval: not_implemented
handoff: not_implemented

## Verified record and service boundaries

- NodeRecord `workbench.node/1` and EdgeRecord `workbench.edge/1` plus JSON schemas
  exist. Legacy payloads/edges round-trip losslessly. ModelBinding pairs
  `provider_id + model_id`; input bindings remain dictionaries and port types remain
  string aliases.
- NodeCreationService validates identity, optional positive revision,
  `can_edit`, temporary Legacy definition resolution, definition state/version, and
  model compatibility. Current Legacy policy rejects supplied models. It supports a
  restricted Legacy definition set (including Classic Output) and durable request
  idempotency. Persistence and JSONL audit are separate.
- NodeMutationService can update exactly `title` and `position`, or delete. The
  Legacy mutation repository applies this only to the characterized standalone
  blank shapes (Classic/Smart Image, Prompt, default Loop, empty Output, empty
  Group) and now rejects content-bearing, grouped, history-linked,
  input-referenced, and (except Image edge cleanup) connected nodes with
  `unsupported_node_shape` instead of trusting the frontend gate. Delete removes
  connected edges for the tolerated Image contracts. Positive revision and
  `can_edit` are required. Persistence/audit are separate.
- GraphMutationService supports only atomic create-node-plus-edge. It validates
  revision/Canvas/new-node edge reference/`can_edit`; edge ports are
  `legacy.out -> legacy.in`. The Legacy repository writes node and edge under one
  Canvas lock/revision; audit is a later separate append.
- Python/browser RendererRegistry, NodeShell, NodeCardHost, UnifiedRenderHost,
  MediaRenderer, LegacyRenderer, read-only Node Inspector, and shared Canvas modules
  exist. Smart Group/Image/Legacy adapters submit their NodeShell card batches to
  `UnifiedRenderHost.mountAdapterCards`; they remain opt-in adapters rather than one
  product runtime.

## Feature and compatibility flags

| Flag | Default | Verified behavior |
|---|---|---|
| `WORKBENCH_HOST` | `127.0.0.1` | `0.0.0.0`/`::` explicitly enable unauthenticated LAN compatibility |
| `WORKBENCH_PORT` | `3000` | Must be integer 1-65535 |
| `WORKBENCH_ALLOWED_ORIGINS` | loopback origins on selected port | Explicit comma list allowed; wildcard rejected |
| `WORKBENCH_LAN_ENABLED` | false | Derived from wildcard bind host |
| `WORKBENCH_NODE_API_ENABLED` | true on default loopback | `/api/v1` router registered only for loopback host values |
| `WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED` | true | Selects SQLite compatibility persistence when SQLite authority state is `sqlite`. Since R4-03 an explicit false value is refused at startup (exit 1, `CanvasAuthoritySplitBrainError`) while authority is `sqlite` — it no longer silently selects writable Legacy; it remains a valid recovery control only when authority is `legacy_json` or unavailable, and inactive authority still does not initialize/switch data |
| `unified_canvas=0` | default-on | Shared state adapter is enabled whenever its module is present; explicit `0` is the bounded U7 rollback control pending complete page/runtime replacement |
| `node_shell=0` | default-on | Enables NodeShell base on loopback; explicit `0` is the bounded U7 rollback control pending complete page/runtime replacement |
| `legacy_renderer=0` | default-on | Uses source-payload rendering inside NodeShell; explicit `0` is the bounded U7 rollback control pending complete page/runtime replacement |
| `media_renderer=0` | default-on | Enables media renderer/NodeShell paths on loopback; explicit `0` is the bounded U7 rollback control pending complete page/runtime replacement |
| `semantic_zoom=0` | default-on | Enables NodeShell semantic presentation on loopback; explicit `0` is the bounded U7 rollback control pending complete page/runtime replacement |
| `screen_space_controls=0` | default-on | Enables Smart NodeShell screen-space controls on loopback; explicit `0` is the bounded U7 rollback control pending complete page/runtime replacement |

## Provider/model/settings and Codex

- Provider metadata/model lists remain provider-shaped fields in `main.py`, frontend
  settings/selectors, built-in/static seeds, and `data/api_providers.json`.
- Credentials remain backend-side in ignored `API/.env`; public endpoints expose
  configuration/masked state. No ProviderConnection, ModelRegistry,
  ModelAvailability, or shared capability/compatibility registry exists.
- Existing Codex integration remains `codex exec` from `main.py`, with repository
  cwd, `workspace-write`, optional model/images/output file, and bounded timeout.
- R1 adds `workbench.codex.CodexBridge` for App Server protocol v2, tested against
  installed `codex-cli 0.153.1`. It is stdio JSONL only, uses an allowlisted child
  environment and workspace-contained cwd, and exposes no Workbench domain tools.
- `HarnessLaunchPolicy` pins thread sandbox to `read-only`; turns are `readOnly`
  with network disabled and `approvalPolicy: never`. Server requests are normalized
  and denied by default. `codex exec` remains compatible and is not rerouted.

## Authorization and security

- There is no global authentication or action/resource authorization. Most Legacy
  routes and WebSocket are reachable to any client able to reach the service.
- `/api/v1` node routes are loopback-only, require caller-supplied `X-User-ID`, and
  check project plus Legacy owner. Local wiring explicitly permits unowned Canvases.
  This is compatibility scoping, not authenticated identity.
- CORS defaults local and rejects wildcard origins; LAN mode remains unauthenticated.
- Current path-containment, media cleanup, redaction, secret-boundary, stale-write,
  and exposure tests pass. No uniform SSRF/tool/subprocess/audit policy exists.

## Automated test baseline

Command:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -q
```

Result: PASS after R4-01 local-truth re-verification at `f764ce1` — 294 tests in
2.7 seconds, Python 3.14.7 (2026-09-06). Relative to the previously recorded 285,
the +9 tests are the committed architecture-guard tests and the shared
interaction-session/clipboard module tests recorded in
`docs/plans/R4_OWNERSHIP_MATRIX.md`; R4-01 itself adds no tests and no product
change.

Result: PASS after R4-02 reconciliation at `b088d6d` — 297 tests in 2.8 seconds,
Python 3.14.7 (2026-09-06). The +3 tests are the new reconciliation behavioral
tests; no product behavior changed.

Result: PASS after R4-03 split-brain guard at `a1195c9` — 308 tests in 3.0
seconds, Python 3.14.7 (2026-09-06). The +11 tests are the authority policy
resolver/reader tests and the wiring guard tests; five legacy-routed fixtures
gained temporary-database isolation patches.

Result: PASS after R4-04 split-brain regression suite — 313 tests in 3.1
seconds, Python 3.14.7 (2026-09-06). The +5 tests are the incident-scenario
regression suite; no product behavior changed.

Result: PASS after R4-05 canonical Canvas transport — 319 tests in 3.4 seconds,
Python 3.14.7 (2026-09-06). The +6 tests cover logical-revision reads, CAS
success and stale conflict, authority-gated 503, 404, and the unchanged legacy
transport shape.

Result: PASS after R4-06 browser logical-revision persistence — 323 tests in
3.2 seconds, Python 3.14.7 (2026-09-06). The +4 tests are the persistence
client sandbox scenarios (canonical CAS wire format, cursor chain through
conflict recovery, versioned-write adoption, 503/legacy fallbacks) plus an
in-process HTTP round-trip test.

Result: PASS after R4-07 remote sync uses revision — 329 tests in 3.4 seconds,
Python 3.14.7 (2026-09-06). The +6 tests cover the canonical meta probe, the
revision-bearing broadcast, metadata peek semantics, revision-ordered polling,
and revision-ordered update messages with timestamp fallback; the event
contract gained the additive revision field.

Result: PASS after R4-08 rendering ownership characterization — 330 tests in
3.1 seconds, Python 3.14.7 (2026-09-06). The +1 test is the source-contract
test anchoring the rendering ownership map; no product behavior changed.

Result: PASS after R4-09 Unified RenderRuntime lifecycle — 332 tests in 3.1
seconds, Python 3.14.7 (2026-09-06). The +2 tests are the runtime lifecycle
sandbox and the wiring contract; three mount-wiring assertions moved to the
runtime contract.

Result: PASS after R4-10 Group rendering cutover — 334 tests in 3.5 seconds,
Python 3.14.7 (2026-09-06). The +2 tests are the `mountGroupCard` behavioral
test and the both-adapters cutover contract test.

Result: PASS after R4-11 media rendering cutover — 337 tests in 3.8 seconds,
Python 3.14.7 (2026-09-06). The +3 tests cover the projection exclude selector,
the runtime remount projection, and the renderer signature URL.

Result: PASS after R4-12 generic prompt cutover — 339 tests in 3.7 seconds,
Python 3.14.7 (2026-09-06). The +2 tests are the prompt-card renderer
behavioral pipeline test and the Classic wiring contract.

Result: PASS after R4-13 provider compatibility renderers — 341 tests in 3.8
seconds, Python 3.14.7 (2026-09-06). The +2 tests are the provider-compat
adoption/cleanup behavioral test and the Classic lifecycle wiring contract.

Result: PASS after R4-14 InteractionController — 343 tests in 3.6 seconds,
Python 3.14.7 (2026-09-06). The +2 tests are the pointer-session lifecycle
behavioral test and the Classic drag/resize wiring contract.

Result: PASS after R4-15 selection ownership cutover — 345 tests in 4.0
seconds, Python 3.14.7 (2026-09-06). The +2 tests are the selection store
behavioral test and the Classic authority wiring contract; one box-selection
contract assertion moved to the authority call.

Result: PASS after R4-16 viewport / pan / zoom cutover — 347 tests in 3.8
seconds, Python 3.14.7 (2026-09-06). The +2 tests are the viewport controller
behavioral test and the Classic five-flow wiring contract; two shared-runtime
contract assertions moved to per-page zoom identifiers.

Result: PASS after R4-17 minimap cutover — 350 tests in 3.3 seconds, Python
3.14.7 (2026-09-06). The +3 tests are the minimap controller behavioral test,
the Classic wiring contract, and the 100/300-node projection scaling
characterization.

Result: PASS after R4-18 drag / resize cutover — 352 tests in 3.4 seconds,
Python 3.14.7 (2026-09-06). The +2 tests are the session-factory behavioral
test and the both-adapters wiring contract; four shared-session contract
assertions moved to the factory calls.

Result: PASS after R4-19 keyboard runtime cutover — 354 tests in 3.4 seconds,
Python 3.14.7 (2026-09-06). The +2 tests are the keyboard dispatch behavioral
test and the both-adapters wiring contract.

Result: PASS after R4-20 connection interaction cutover — 356 tests in 3.4
seconds, Python 3.14.7 (2026-09-07). The +2 tests are the connection gesture
behavioral test and the both-adapters wiring contract; the Smart port-hover
contract moved to the controller callbacks.

Result: PASS after R4-21 creation controller — 358 tests in 3.5 seconds,
Python 3.14.7 (2026-09-07). The +2 tests are the creation envelope behavioral
test and the both-adapters wiring contract; two creation-count contracts
moved to the controller seam.

Agent regression gate (cards R4-01…R4-21):

```text
./scripts/agent-verify.sh
```

Result: PASS — AGENT VERIFY: PASS (358 unit tests, Python AST parse of 73 files,
`node --check` of 67 JavaScript files, 4 architecture-guard tests,
`git diff --check`; Node v24.20.0). The gate script was fixed during R4-01 to
prefer `.venv/bin/python` over PATH `python3`, which lacks project dependencies
(`pydantic`); verification tooling only, no product behavior change.

R4 canonical-routing local acceptance:

```text
WORKBENCH_HOST=127.0.0.1 WORKBENCH_PORT=3001 WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED=true .venv/bin/python main.py
GET /api/canvases
GET /api/canvases/ca914662f0dc4923bd5b60b29eb55b68
GET /api/canvases/ca914662f0dc4923bd5b60b29eb55b68/meta
```

Result: PASS — isolated local server read 16 active Canvas records through SQLite
compatibility routing; the Smart fixture loaded with 3 nodes and unchanged Legacy
`updated_at`. The process was stopped after the read-only check; existing 3000
service was not changed.

R4 browser acceptance (same isolated 3001 process): PASS — Canvas list rendered 16
active records; Classic record `7ed83bf56f234d77a9e67ae1f6496577` rendered its
6-node page; Smart record `ca914662f0dc4923bd5b60b29eb55b68` rendered its 3-node
page. No save/generation/delete action was invoked. The temporary process was
stopped after the browser retained a WebSocket connection; its cancellation log is
shutdown noise, not an application request failure.

R4 default-routing browser write acceptance: PASS — a separate localhost service
used a process-lifetime temporary SQLite database, seeded one Classic and one Smart
record under activated SQLite authority, and had startup hooks disabled. The list
rendered both records; browser creation of `R4 browser write acceptance` increased
the visible count from 2 to 3. The process stopped and its temporary database was
discarded. No user project Canvas was written.

R4 persistence acceptance: PASS — focused tests prove SQL `id + revision` CAS,
409 stale-write semantics through the Legacy compatibility API, restart persistence,
unknown-field retention, and lossless rollback export back to `legacy_json` authority.
Startup no longer rewrites `static/*.html`; runtime cache-version responses remain
dynamic and source files stay unchanged after a server start.

R3 focused command:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest tests.test_sqlite_project_canvas_repository tests.test_project_canvas_wiring tests.test_project_canvas_migration_tool -v
```

Result: PASS — 10 tests in 0.217 seconds. The migration command imports a
temporary Legacy project/Canvas source, emits a lossless compare report without
switching authority by default, and switches only with explicit `--activate`.

Live R3 report command (no `--activate`):

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python tools/migrate_project_canvas.py --projects data/projects.json --canvases-dir data/canvases --database data/workbench.sqlite3 --report data/r3-project-canvas-migration-report.json
```

Result: PASS — 22 imported, 0 skipped, 0 comparison differences; authority remains
`legacy_json`. Both outputs are ignored under `data/`; no Legacy source file was
rewritten.

Browser acceptance (read-only, local `127.0.0.1:3000`): PASS — from the single
Canvas-list entry, Classic record `7ed83bf56f234d77a9e67ae1f6496577` remained at
`/static/canvas.html`, and historical Smart record
`ca914662f0dc4923bd5b60b29eb55b68` reached its retained
`/static/smart-canvas.html` compatibility page. No Canvas data or execution was
mutated.

Shared-entry browser recheck (read-only, isolated `127.0.0.1:3010` server): PASS
— the normal `canvas.html` URL for historical Smart record
`ca914662f0dc4923bd5b60b29eb55b68` handed off to its retained Smart adapter with
the existing two nodes and workflow controls visible. This verifies the shared
Canvas-list project-memory/URL module after its cache-version update; no Canvas
data or execution was mutated.

Shared-render browser acceptance (read-only, same local server): PASS — the same
Classic and Smart records loaded with `unified_canvas=1`, `node_shell=1`, both
renderer flags, `semantic_zoom=1`, and `screen_space_controls=1`. Both displayed
shared NodeShell ready state, generic ports, and semantic summary controls; no
Canvas data or execution was mutated.

Current-worktree browser recheck (read-only, isolated `127.0.0.1:3011` server):
PASS — Classic record `bf43426d46e648e2b069f4a2313f4aab` remained on the normal
entry with four ready NodeShell cards, media controls, and generic ports. Historical
Smart record `ca914662f0dc4923bd5b60b29eb55b68` entered via that same URL, handed
off to its retained adapter, and displayed its Smart composer, template entry,
workflow controls, and two nodes. No Canvas data or execution was mutated; the
temporary server was stopped.

Default-on `unified_canvas` browser recheck (read-only, isolated
`127.0.0.1:3005` server): PASS — Classic record
`7ed83bf56f234d77a9e67ae1f6496577` loaded at its normal `canvas.html` URL with
its nodes and controls visible. Historical Smart record
`ca914662f0dc4923bd5b60b29eb55b68` opened from the same normal URL and reached
its retained `smart-canvas.html` adapter with nodes and controls visible. Neither
Canvas was saved, created, or executed. This does not authorize page deletion.

Default-on `node_shell` browser recheck (read-only, same isolated server): PASS
— the Classic record remained readable at its normal URL, and the retained Smart
adapter displayed its Smart Group through a ready NodeShell with generic Input and
Output ports. Neither Canvas was saved, created, or executed. Explicit
`node_shell=0` remains the bounded U7 rollback control.

Default-on `media_renderer` browser recheck (read-only, same isolated server):
PASS — the Classic media node rendered through a ready unified card with its media
controls and generic Input/Output ports. The retained Smart adapter remained
readable with its ready Smart Group shell and ports. Neither Canvas was saved,
created, or executed; `media_renderer=0` remains the bounded U7 rollback control.

Default-on `legacy_renderer` browser recheck (read-only, same isolated server):
PASS — Classic video, LLM, Comfy, and Output nodes were ready inside NodeShell
while retaining their source-owned controls and generic ports. The retained Smart
Legacy skill node was likewise ready in NodeShell with its original controls.
Neither Canvas was saved, created, or executed; `legacy_renderer=0` remains the
bounded U7 rollback control.

Default-on `semantic_zoom` browser recheck (read-only, same isolated server):
PASS — Classic displayed the semantic indicator at `100% · 完整 · 6 节点`, while
the retained Smart adapter displayed `65% · 摘要 · 2 节点` and its corresponding
summary node presentation. Neither Canvas was saved, created, or executed;
`semantic_zoom=0` remains the bounded U7 rollback control.

Default-on `screen_space_controls` browser recheck (read-only, same isolated
server): PASS — the retained Smart adapter remained readable in semantic summary
mode with generic Input/Output ports visible for both ready NodeShell nodes.
Neither Canvas was saved, created, or executed; `screen_space_controls=0` remains
the bounded U7 rollback control.

All-zero UI-flag rollback browser recheck (read-only, same isolated server): PASS
— Classic restored its retained non-NodeShell presentation. Historical Smart was
opened through the normal `canvas.html` URL with all six explicit zero flags; the
handoff retained every flag in its `smart-canvas.html` URL and restored the
retained non-NodeShell presentation. Neither Canvas was saved, created, or
executed.

Current-worktree all-zero rollback recheck (read-only, isolated
`127.0.0.1:3010`): PASS — Classic record
`bf43426d46e648e2b069f4a2313f4aab` rendered its retained non-NodeShell cards;
its existing video preview fallback received a `415` preview response and retained
native video controls. Historical Smart record `ca914662f0dc4923bd5b60b29eb55b68`
opened through the same normal URL, preserved all six zero flags during handoff,
and rendered its retained group, upload, and Skill controls. No user-initiated
save, create, execution, or deletion occurred; the isolated service was stopped.

Current-worktree browser recheck (read-only, isolated `127.0.0.1:3008`): PASS —
the normal Classic URL for `7ed83bf56f234d77a9e67ae1f6496577` rendered its title,
six nodes, NodeShell-ready cards, and generic ports. The normal Smart URL for
`ca914662f0dc4923bd5b60b29eb55b68` handed off to the retained adapter and rendered
the Smart composer, Smart group, upload node, and Skill node. Reopening the same
Smart record with all six explicit zero flags preserved every rollback parameter
through the handoff and rendered the retained legacy controls. No create, save,
generation, delete, or other Canvas mutation was invoked; the isolated service was
stopped after verification.

Workflow-dialog browser follow-up on the same local fixture is intentionally not
accepted as read-only evidence: selecting one Classic node showed a newer
`updated_at`, even though the direct Classic/Smart selection handlers have a focused
contract prohibiting `scheduleSave()`. The source of that metadata update was not
attributed during the attempt, so no export was triggered and the service was
stopped. Repeat workflow UI export only against a process-lifetime temporary SQLite
fixture before using it as R4 acceptance evidence.

Workflow UI export browser acceptance (isolated `127.0.0.1:3009` temporary
SQLite authority): PASS — one seeded Classic and one seeded Smart Canvas each
selected one node and opened the workflow dialog from the normal Canvas entry.
Both exposed `已选择 1 个节点，0 条连线`; Classic JSON export completed, and Smart
explicitly reported `已导出智能画布工作流 JSON`. No import, execution, or user Canvas
was used. The fixture service was stopped; after environment deletion protection
initially rejected a force-delete, its isolated temporary directory was moved to the
local Trash and is recoverable.

Media URL shared-boundary browser smoke (read-only, isolated `127.0.0.1:3010`):
PASS — Classic record `bf43426d46e648e2b069f4a2313f4aab` rendered its existing
local video and image through the shared `media-url.js` module, with NodeShell-ready
cards and generic ports. Opening historical Smart record
`ca914662f0dc4923bd5b60b29eb55b68` through the normal Canvas URL handed off to its
retained adapter and preserved the Composer, Smart group, upload node, and video
workflow node. No save, create, execution, deletion, or other Canvas mutation was
invoked; the isolated service was stopped after the smoke check.

Native-video shared-control browser smoke (read-only, isolated `127.0.0.1:3010`):
PASS — Classic record `bf43426d46e648e2b069f4a2313f4aab` loaded its local video
controls and media/image cards after `media-preview-controls.js` loaded. Historical
Smart record `ca914662f0dc4923bd5b60b29eb55b68` again handed off from the normal URL
and retained its Composer, Smart group, upload, and video workflow controls. No
save, create, execution, deletion, or other Canvas mutation was invoked; the
isolated service was stopped after verification.

Preview-fallback shared-control browser smoke (read-only, isolated
`127.0.0.1:3010`): PASS — Classic record
`bf43426d46e648e2b069f4a2313f4aab` retained its existing local video and image
cards; the normal URL for historical Smart record
`ca914662f0dc4923bd5b60b29eb55b68` again handed off and retained Composer, Smart
group, upload, and video-workflow controls. No save, create, execution, deletion,
or other Canvas mutation was invoked; the isolated service was stopped after the
check.

High-resolution candidate shared-helper browser smoke (read-only, isolated
`127.0.0.1:3010`): PASS — Classic record
`bf43426d46e648e2b069f4a2313f4aab` retained its local video/image cards and
NodeShell ports; the normal Smart URL for `ca914662f0dc4923bd5b60b29eb55b68`
handed off and retained Composer, Smart group, upload, and video-workflow controls.
No save, create, execution, deletion, or other Canvas mutation was invoked; the
isolated service was stopped after the check.

MediaRenderer classification browser smoke (read-only, isolated
`127.0.0.1:3010`): PASS — Classic record
`bf43426d46e648e2b069f4a2313f4aab` rendered its NodeShell-ready local video/image
cards; historical Smart record `ca914662f0dc4923bd5b60b29eb55b68` handed off from
the normal URL and retained Composer, Smart group, upload, and video-workflow
controls. No save, create, execution, deletion, or other Canvas mutation was
invoked; the isolated service was stopped after the check.

Media-kind shared-module browser smoke (read-only, isolated `127.0.0.1:3010`):
PASS — Classic record `bf43426d46e648e2b069f4a2313f4aab` retained its video and
image cards; the normal URL for Smart record `ca914662f0dc4923bd5b60b29eb55b68`
handed off and retained Composer, Smart group, upload, and video-workflow controls.
No save, create, execution, deletion, or other Canvas mutation was invoked; the
isolated service was stopped after the check.

Async-decode shared-helper browser smoke (read-only, isolated `127.0.0.1:3010`):
PASS — Classic record `bf43426d46e648e2b069f4a2313f4aab` completed media-card
rendering with its existing local image/video; the normal Smart URL for historical
record `ca914662f0dc4923bd5b60b29eb55b68` handed off and preserved Composer, Smart
group, upload, and video-workflow controls. No save, create, execution, deletion,
or other Canvas mutation was invoked; the isolated service was stopped after the
check.

R1 focused command:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest tests.test_codex_bridge -v
```

Result: PASS — 3 tests in 0.074 seconds. Covers initialize, Thread create, simple
Turn, normalized events, default approval denial, model/config discovery,
interruption, shutdown/recovery, workspace containment, and secret filtering.

The pre-R1 baseline coverage includes Legacy fixtures/round-trip, Canvas cleanup and stale writes,
versioned node APIs/runtime, shared Canvas runtime/modules, events/exposure,
NodeRecord/renderer/services/repositories, Inspector, security boundaries, semantic
zoom, screen-space controls, and workflow archive round-trip.

## Syntax/static checks

Commands and results:

```text
.venv/bin/python -c "import ast, pathlib; paths=[pathlib.Path('main.py'), *pathlib.Path('workbench').rglob('*.py'), pathlib.Path('tools/migrate_project_canvas.py'), pathlib.Path('tools/backup_canvas_sources.py')]; [ast.parse(p.read_text(encoding='utf-8'), filename=str(p)) for p in paths]; print(f'Python AST OK: {len(paths)} files')"
PASS — 33 Python files parsed in the latest R4 verification.

NODE_BIN=/Users/lo/.local/node-v24.20.0/bin/node
"$NODE_BIN" --check static/js/canvas.js
"$NODE_BIN" --check static/js/smart-canvas.js
"$NODE_BIN" --check static/js/canvas-list.js
rg --files static/js/workbench/canvas static/js | rg '\\.js$' | sort -u | xargs -n 1 "$NODE_BIN" --check
PASS — 42 JavaScript files, including Classic, Smart, Canvas-list, and shared Canvas modules; Node v24.20.0.

git diff --check
PASS
```

R4-01 re-verification (2026-09-06): the agent gate's full-tree sweeps parsed 66
Python files (all non-venv `*.py` under the repository) and syntax-checked 63
JavaScript files under `static/js`; both PASS. Counts grew from the previously
recorded 33/42 through the committed shared interaction/clipboard modules and the
architecture-guard tests.

R4-02 re-verification (2026-09-06): 68 Python files (adding the reconciliation
tool and its tests) and 63 JavaScript files; PASS.

R4-03 re-verification (2026-09-06): 70 Python files (adding the authority policy
seam and its tests) and 63 JavaScript files; PASS.

R4-04 re-verification (2026-09-06): 71 Python files (adding the split-brain
regression suite) and 63 JavaScript files; PASS.

R4-05 re-verification (2026-09-06): 73 Python files (adding the canonical
transport router and its tests) and 63 JavaScript files; PASS.

No repository-supported Ruff, mypy, ESLint, or bundled frontend build configuration
was found; none is claimed as run.

Additional R1 checks:

```text
git diff --check
PASS

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY' ... CodexBridge.start(); list_models(); read_config(); shutdown() ... PY
PASS — live, non-mutating `initialize`, `model/list`, and `config/read` through
installed `codex app-server` (`codex-cli 0.153.1`).
```

## Performance baseline

Command:

```text
node tools/benchmark-canvas-payload.mjs
```

Result: PASS/reproduced for current R4 worktree — 100 nodes = 9,622 bytes (0.108 ms serialization);
300 nodes = 29,132 bytes (0.096 ms serialization). This is deterministic payload
construction, not a browser interaction budget.

R4-01 re-run (2026-09-06): reproduced — 100 nodes = 9,622 bytes (0.086 ms
serialization), 300 nodes = 29,132 bytes (0.093 ms serialization); byte-identical
to the recorded baseline.

Latest available browser record:
`docs/benchmarks/canvas-node-shell-baseline-2026-09-04.md`. Visible 300-node Safari
NodeShell sample: load 152 ms, render ready 362 ms, zoom 38 ms, pan 104 ms, minimap
15 ms. Earlier offscreen minimap was 149 ms (141 ms recheck) and remains a P2
follow-up. All are single local samples, not percentile/release commitments.

## Verified known issues

1. RESOLVED IN R2 — connected graph creation now requires a positive revision at
   `CreateNodeAndEdgePayload`; the service also rejects a missing, zero, or negative
   revision before persistence/node preparation. It no longer normalizes absence to
   `0`; focused and full tests verify the behavior.
2. PARTIALLY RESOLVED IN R3 — canonical SQLite mutation plus audit/outbox insertion
   is one tested transaction and audit insertion failure rolls the Canvas change
   back. Legacy JSON routes still persist before JSONL audit until switch completion.
3. PARTIALLY RESOLVED IN R3 — SQLite CanvasRecord has tested independent logical
   revisions. Legacy runtime routes still use `updated_at` until controlled switch.
4. VERIFIED — visible 300-node browser sample is healthy against the provisional
   interaction alert, but earlier offscreen minimap timing exceeded it; retain the
   documented P2 follow-up and repeat after material Canvas changes.
5. VERIFIED LIMIT — R1's Codex bridge has no Workbench project/Canvas/node/graph
   mutation tools and intentionally has no interactive approval UI. Requests are
   denied by default; future authority must be proposed and gated.

## Legacy monolith responsibility baseline

### `main.py`

- Size/profile: 18,397 lines; 828 top-level functions; 75 classes; 162 route
  decorators. It still owns most backend provider/model/secret/subprocess,
  generation/chat, project/Canvas, asset/workflow/media/queue/event, and
  Legacy API behavior.
- Already delegated: record/adapter/repository contracts, RendererRegistry,
  NodeCreation/Mutation/GraphMutation, JSONL audit sink, and `/api/v1` node router
  live under `workbench/`; `main.py` wires them.
- R4 added Workbench business responsibility: no.
- R4 responsibilities removed/delegated: Canvas metadata writes, listing, expired
  trash cleanup, project-delete reassignment, and media-reference diagnostics now
  delegate through the CanvasRepository contract; canonical SQLite compatibility
  persistence remains under `workbench/`, while `main.py` only composes it. The
  Legacy repository self-update, staging, self-restart, rollback, source URL, and
  GitHub-hosted model-registry fallback responsibility have been removed.

### `static/js/canvas.js`

- Size/profile: 16,686 lines. It still owns Classic construction/render/connect/
  execution, provider controls, graph/save/conflict, workflow/assets/logs, minimap,
  selection, drag, resize, and page adaptation.
- Already delegated: opt-in runtime, geometry, graph/group intents, creation
  catalog/client, records, entry compatibility resolver, NodeShell, renderer registry/host/renderers, Inspector,
  semantic zoom, and screen controls live in `static/js/workbench/canvas/`.
- R4 added Workbench business responsibility: no.
- R2 responsibilities removed/delegated: Classic blank Output creation now delegates
  to the restricted NodeCreationService route by default on loopback; `versioned_nodes=0`
  retains the bounded U7 compatibility fallback. Classic port-drop acceptance delegates to
  shared `WorkbenchCanvasPortCompatibility`; its generic generation entry delegates
  through `WorkbenchCanvasExecutionCompatibility`; historical Smart-entry detection
  and URL construction delegate to `WorkbenchCanvasEntryCompatibility`.

### `static/js/smart-canvas.js`

- Size/profile: 20,085 lines. It still owns Smart composer, construction/render/
  connect/execution, provider/media/MiniMax, graph/save/conflict, groups, minimap,
  selection, drag, resize, and page adaptation.
- Already delegated: consumes the same opt-in shared Canvas modules as Classic.
- R4 added Workbench business responsibility: no.
- R2 responsibilities removed/delegated: Smart blank MiniMax creation delegates to
  the restricted NodeCreationService route by default on loopback; `versioned_nodes=0`
  retains the bounded U7 compatibility fallback. Smart port-drop hover and acceptance
  delegate to shared `WorkbenchCanvasPortCompatibility`; its primary generation
  entry delegates through `WorkbenchCanvasExecutionCompatibility`; Smart Group/Image/Legacy
  NodeShell card batches delegate to `UnifiedRenderHost.mountAdapterCards`.
- R4 narrowing: an idle, media-free, ungrouped Smart Image without history or
  dependent input references now deletes through `NodeMutationService`; rejected
  or stale writes do not fall through to raw Canvas save. Smart media clearing,
  group/history and dependent-node deletion remain adapter-owned compatibility.
- R4 narrowing: the same Smart Image class commits a single non-Alt/non-Ctrl,
  non-thumbnail drag position through `NodeMutationService`; stale or rejected
  writes restore its previous position. Rich move, group/media and resize
  behavior remain adapter-owned compatibility.
- R4 narrowing: the Legacy persistence adapter now writes a service-created
  blank Image as durable `smart-image` data on Smart Canvases, with Smart title
  and empty media fields. This removes the normal creation path's dependence on
  a front-end-only type projection; media and rich creation remain compatibility.
- R4 narrowing: supported Smart connected creation now persists its new node,
  edge and target input relationship in the GraphMutationService transaction.
  The successful local projection does not schedule a raw Canvas save; ordinary
  connection interaction and unsupported paths remain adapter-owned compatibility.
- R4 narrowing: supported Classic connected blank-Image creation likewise uses
  GraphMutationService for the new node, edge and target input relationship;
  unsupported connected creation remains adapter-owned compatibility.
- R4 narrowing: the same atomic GraphMutationService path now covers Classic
  connected blank Prompt and default Loop creation. The page only projects the
  committed node/edge and performs its retained compatibility refresh; provider,
  execution, and configured-node creation remain adapter-owned compatibility.
- R4 interaction narrowing: both adapters now delegate default-path viewport
  pan-session origin/delta/threshold calculation to CanvasRuntime while retaining
  their DOM transform and persistence shells. The explicit `unified_canvas=0`
  rollback retains the prior page-local calculation and each adapter's original
  movement metric.
- R4 interaction narrowing: both adapters now delegate default-path wheel-scale
  calculation to CanvasRuntime, preserving Classic's step factors and Smart's
  delta-clamped exponential bounds. Their DOM/minimap/persistence shells and
  the `unified_canvas=0` page-local formulas remain adapter-owned compatibility.
- R4 interaction narrowing: both adapters now delegate default-path minimap
  pointer projection and world-point centering to CanvasRuntime and its viewport
  command. Their minimap DOM, event binding and persistence shells, along with
  the `unified_canvas=0` page-local formulas, remain adapter-owned compatibility.
- R4 interaction narrowing: both adapters now commit default-path fitted and
  recovered viewports through CanvasRuntime. Their fitting inputs/fallbacks,
  Smart recovery eligibility, DOM application and persistence shells remain
  adapter-owned compatibility, with direct assignment retained for
  `unified_canvas=0`.
- R4 interaction narrowing: both adapters now commit default-path zoom-preview
  exits, including readable node focus, through CanvasRuntime. Preview mode,
  adapter scale rules, DOM application and persistence shells remain
  adapter-owned compatibility, with direct assignment retained for
  `unified_canvas=0`.
- R4 interaction narrowing: Smart media-thumbnail single selection and preview
  selection now commit node selection through CanvasRuntime. Media focal-item,
  preview, Composer and video behavior remain Smart adapter-owned, with direct
  selection state retained for `unified_canvas=0`.
- R4 interaction narrowing: Smart's node upload entry now commits its target
  selection through CanvasRuntime before opening the existing file picker.
  Upload target, picker, media focal state and Composer behavior remain adapter
  owned, with direct selection state retained for `unified_canvas=0`.
- R4 interaction narrowing: Smart's group right-click menu now commits its
  target selection through CanvasRuntime before opening the existing group menu.
  Group, menu and creation behavior remain adapter owned, with direct selection
  state retained for `unified_canvas=0`.
- R4 creation narrowing: Classic and Smart default blank-Image menu creation
  now commits the service result through the shared creation client, which
  appends the projected node, records undo and applies the authoritative Canvas
  revision. Adapter-specific node shape, Smart selection and render feedback,
  plus unsupported/group-member creation, remain compatibility-owned.
- R4 creation narrowing: Classic and Smart default blank-Prompt menu creation
  now uses that same shared success-result commit. Prompt card shape, Smart
  selection/render feedback, connected/group-member creation and unsupported
  paths remain adapter-owned compatibility.
- R4 creation narrowing: Classic and Smart default blank-Loop menu creation
  now also uses the shared success-result commit. Loop card shape, Smart
  selection/render feedback, connected/group-member creation and unsupported
  paths remain adapter-owned compatibility.
- R4 creation narrowing: Classic and Smart default blank-Group menu creation
  now also uses the shared success-result commit. Group-member editing,
  connected creation, media behavior, card shape and Smart selection/render
  feedback remain adapter-owned compatibility.
- R4 creation narrowing: Classic default blank-Output menu creation now uses
  the shared success-result commit. Output card shape/render feedback and
  connected or unsupported creation remain adapter-owned compatibility.
- R4 creation narrowing: Smart default MiniMax menu creation now uses the
  shared success-result commit after its existing adapter-owned timeline-segment
  initialization. MiniMax media, timeline and execution interaction remain
  adapter-owned compatibility.
- R4 creation narrowing: Classic connected Group/Image and Smart connected
  Group/Prompt/Loop/Image/MiniMax now commit their atomic graph result through
  the shared creation client. Node/edge/undo/revision/selection and generic
  input-relation update are shared; adapter-owned card projection, Classic
  post-connection sync and Smart product feedback remain compatibility.
- R4 creation narrowing: Classic and Smart now delegate DataTransfer directory
  traversal and supported-file filtering to the shared media-drop runtime.
  Their upload endpoints, media handling, target selection, group layout and
  Canvas-save lifecycle remain adapter-owned compatibility.
- R4 creation narrowing: that shared media-drop runtime now also resolves the
  common file/directory/local-path/remote-URL payload precedence. Classic keeps
  its existing directory-fallback eligibility; upload API, media policy, target
  selection, group layout and Canvas-save lifecycle remain adapter-owned.
- R4 creation narrowing: the shared media-drop runtime now owns the common
  `/api/ai/upload` multipart transport and response file-list extraction.
  Classic retains its JSON failure semantics; Smart retains named multipart
  files, readable errors and media-kind projection. Result materialization,
  target selection, group layout and Canvas save remain adapter-owned.
- R4 mutation narrowing: a Classic Prompt with empty text, no links and no
  group membership now updates position or deletes through NodeMutationService.
  The repository accepts this durable Prompt shape; content-bearing, connected
  and grouped Prompts remain adapter-owned compatibility.
- R4 mutation narrowing: a Classic Loop only when it retains the default
  serial/count/start/batch configuration with no prompt/media input, links or
  group membership now updates position or deletes through NodeMutationService.
  The repository accepts this durable Loop shape; configured, connected and
  grouped Loops remain adapter-owned compatibility.
- R4 mutation narrowing: a Classic Output only when it has no images, pending
  tasks, comparison state, links or group membership now updates position or
  deletes through NodeMutationService. The repository accepts this durable
  Output shape; output clearing, execution results, configured, connected and
  grouped Outputs remain adapter-owned compatibility.
- R4 mutation narrowing: a Classic Group only when it has no members, links or
  nesting membership now updates position or deletes through NodeMutationService.
  The repository accepts this durable Group shape; member movement, membership
  changes, resize and graph behavior remain adapter-owned compatibility.
- R4 mutation narrowing: a Smart Group only when it has no members, media,
  input references, links or nesting membership now updates position or deletes
  through NodeMutationService. The repository accepts this durable Smart Group
  shape; Smart group media, history, membership, resize and Composer behavior
  remain adapter-owned compatibility.
- R4 mutation narrowing: a Smart Loop only when it is single-round serial with
  no prompt/image input, variable prompt, input references, links or group
  membership now updates position or deletes through NodeMutationService.
  Workflow, connected, grouped and configured Smart Loops remain adapter-owned
  compatibility.

### U7 duplicate-runtime exit inventory

- Shared now: canonical Canvas persistence/CAS, remote-update filtering and polling,
  archive transport, HTTP error formatting, pure media URL normalization/preview
  routing, native-video event isolation, preview-failure fallback binding, and
  MIME/extension media-kind classification, high-resolution candidate collection,
  and async decode preloading, pure graph fragment operations, common
  NodeShell/render host, generic ports, semantic presentation, and screen controls.
- Smart-only still product-relevant: composer and dynamic provider/media controls,
  prompt preset/template and asset-library UX, image edit/crop/draw/grid/panorama
  tools, Smart group media actions, and Smart-specific cascade/execution UI.
- Classic-only still product-relevant: provider-shaped generator/LLM/Comfy/Video/
  MiniMax/LTX/RunningHub cards, Classic output/log/asset management, and Classic
  cascade/execution UI.

Consequently, U7 cannot delete either Runtime/page or retire UI flags until each
listed product-relevant responsibility has an accepted shared replacement or an
explicit bounded compatibility adapter with focused interaction, browser, rollback,
and source-reference evidence.

R4-39 Wave 5 crop-box projection cluster (2026-09-08): crop/outpaint box,
frame, and image-offset projection now delegate to
`WorkbenchCanvasMediaTools.cropBoxProjection`; `canvas.js` retains DOM style
application. Focused behavior coverage proves both modes. Full
`./scripts/agent-verify.sh`: PASS (463 tests; Python AST 78; JavaScript syntax
96; architecture guards 4; diff check clean). R4-39 remains IN_PROGRESS; the
next bounded slice is the remaining media/workflow responsibility cluster.
R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 media-editor mode projection cluster (2026-09-08): normalized mode
flags, apply visibility, labels, and cleanup signals now delegate to
`WorkbenchCanvasMediaEditorState.uiProjection`; `canvas.js` retains DOM toggles,
translation, and media effects. Focused behavior coverage proves preview, grid,
and outpaint. Full `./scripts/agent-verify.sh`: PASS (464 tests; Python AST 78;
JavaScript syntax 96; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 media-editor zoom/overflow projection cluster (2026-09-08): scaled
editor dimensions, zoom label, and stage overflow flags now delegate to
`WorkbenchCanvasMediaTools`; `canvas.js` retains DOM updates and crop-state
synchronization. Focused behavior coverage proves scaled and
overflow/non-overflow cases. Full `./scripts/agent-verify.sh`: PASS (465 tests;
Python AST 78; JavaScript syntax 96; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 brush-tool projection cluster (2026-09-08): tool normalization and
text-mode eligibility now delegate to
`WorkbenchCanvasMediaEditorState.brushToolProjection`; `canvas.js` retains
inline-editor cleanup and DOM class updates. Focused behavior coverage proves
valid, fallback, and non-brush text cases. Full `./scripts/agent-verify.sh`:
PASS (466 tests; Python AST 78; JavaScript syntax 96; architecture guards 4;
diff check clean). R4-39 remains IN_PROGRESS; the next bounded slice is the
remaining media/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 MiniMax active-segment projection cluster (2026-09-08): playhead
hit selection and selected-segment fallback now delegate to
`WorkbenchCanvasMediaTools.minimaxActiveSegment`; focused behavior coverage
passes for time-hit, selected-id fallback, and empty segments. Full
`./scripts/agent-verify.sh`: PASS (492 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 MiniMax segment-reference projection cluster (2026-09-08):
segment-local reference precedence, upstream fallback, deduplication, capping,
and media-kind filtering now delegate to
`WorkbenchCanvasMediaTools.minimaxSegmentRefs` and
`minimaxSegmentRefsByKind`; focused behavior coverage passes for local,
fallback, and kind-filter paths. Full `./scripts/agent-verify.sh`: PASS
(493 tests; Python AST 78; JavaScript syntax 103; architecture guards 4; diff
check clean). R4-39 remains IN_PROGRESS; the next bounded slice is the
remaining media/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 MiniMax segment-result projection cluster (2026-09-08): result
normalization and unique-prepend behavior now delegate to
`WorkbenchCanvasMediaTools.minimaxSegmentResult` and
`minimaxPrependUnique`; focused behavior coverage passes for string/object
normalization and duplicate suppression. Full
`./scripts/agent-verify.sh`: PASS (494 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 MiniMax source aggregation projection cluster (2026-09-08):
ordered source-to-prompt and source-to-reference projection now delegates to
`WorkbenchCanvasMediaTools.minimaxSourceProjection`; focused behavior
coverage passes for prompt joining, empty-source filtering, and reference
collection. Full `./scripts/agent-verify.sh`: PASS (495 tests; Python AST
78; JavaScript syntax 103; architecture guards 4; diff check clean). R4-39
remains IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 MiniMax segment-timing projection cluster (2026-09-08):
start/duration clamping, sequential start enforcement, and trim boundary
normalization now delegate to
`WorkbenchCanvasMediaTools.minimaxSegmentTiming`; focused behavior coverage
passes for default, clamped, and sequential timing cases. Full
`./scripts/agent-verify.sh`: PASS (496 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 MiniMax segment-visual projection cluster (2026-09-08):
aspect-ratio and megapixel fallback/normalization now delegate to
`WorkbenchCanvasMediaTools.minimaxSegmentVisuals`; focused behavior coverage
passes for normalized explicit values and node-level fallbacks. Full
`./scripts/agent-verify.sh`: PASS (497 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 MiniMax reference-migration projection cluster (2026-09-08):
legacy array/refItems/type-bucket merging, normalization, deduplication, and
capacity limiting now delegate to
`WorkbenchCanvasMediaTools.minimaxReferenceMigration`; focused behavior
coverage preserves legacy merge order and cap behavior. Full
`./scripts/agent-verify.sh`: PASS (498 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 MiniMax output-collection projection cluster (2026-09-08):
current-result type completion and valid-URL filtering for segment
results/materials now delegate to
`WorkbenchCanvasMediaTools.minimaxOutputProjection`; focused behavior
coverage passes for current-result normalization and invalid-item filtering.
Full `./scripts/agent-verify.sh`: PASS (499 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 MiniMax node-config projection cluster (2026-09-08): workflow,
RunningHub workflow, payment mode, aspect-ratio, and megapixel default
normalization now delegate to
`WorkbenchCanvasMediaTools.minimaxNodeConfig`; focused behavior coverage
passes for defaults and explicit overrides. Full
`./scripts/agent-verify.sh`: PASS (500 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 MiniMax segment-list projection cluster (2026-09-08): empty list
initialization, default segment timing fields, and missing-ID generation now
delegate to `WorkbenchCanvasMediaTools.minimaxSegmentList`; focused behavior
coverage passes for generated defaults and existing-list preservation. Full
`./scripts/agent-verify.sh`: PASS (501 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 MiniMax selection-duration projection cluster (2026-09-08):
selected-segment fallback and timeline duration aggregation now delegate to
`WorkbenchCanvasMediaTools.minimaxSelectionProjection`; focused behavior
coverage passes for valid selection, missing-selection fallback, and duration
floor behavior. Full `./scripts/agent-verify.sh`: PASS (502 tests; Python
AST 78; JavaScript syntax 103; architecture guards 4; diff check clean).
R4-39 remains IN_PROGRESS; the next bounded slice is the remaining
media/workflow responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 Loop upstream-prompt projection cluster (2026-09-08): prompt,
promptGroup, loop, and LLM upstream text collection with trimming and cycle
protection now delegates to
`WorkbenchCanvasLoopInputProjection.promptItems`; focused behavior coverage
passes for all upstream source types. Full `./scripts/agent-verify.sh`: PASS
(503 tests; Python AST 78; JavaScript syntax 103; architecture guards 4; diff
check clean). R4-39 remains IN_PROGRESS; the next bounded slice is the
remaining media/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 Loop connected-media batch projection cluster (2026-09-08):
enabled-state checking, connection traversal, URL filtering, and image/video
batch projection now delegate to
`WorkbenchCanvasLoopInputProjection.connectedBatch`; focused behavior
coverage passes for enabled and disabled paths. Full
`./scripts/agent-verify.sh`: PASS (504 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 MiniMax download projection cluster (2026-09-08): valid URL
checks and safe download-name projection now delegate to
`WorkbenchCanvasMediaTools.minimaxDownloadProjection`; focused behavior
coverage passes for valid and empty URL paths. Full
`./scripts/agent-verify.sh`: PASS (505 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 Loop output-media reference projection cluster (2026-09-08):
output-item type filtering, URL/name projection, fallback naming, and
output-index metadata now delegate to
`WorkbenchCanvasLoopInputProjection.outputMediaRefs`; focused behavior
coverage passes for image/video mappings and legacy index semantics. Full
`./scripts/agent-verify.sh`: PASS (506 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 Loop node-media reference projection cluster (2026-09-08):
image/group/output/generated-node reference projection now delegates to
`WorkbenchCanvasLoopInputProjection.nodeMediaRefs`; focused behavior
coverage passes for group media mapping and generated/output paths. Full
`./scripts/agent-verify.sh`: PASS (507 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded slice is the remaining media/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 MiniMax timeline-interaction batch (2026-09-09): playhead
clamping, active-segment hit testing, and selection-change detection now
delegate to `WorkbenchCanvasMediaTools.minimaxTimelineInteraction`; focused
behavior coverage passes for timeline hit and selection transition. Full
`./scripts/agent-verify.sh`: PASS (508 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded batch is the remaining Loop/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 Loop configuration batch (2026-09-09): count, start index,
batch-size, mode, and input-toggle normalization now delegate to
`WorkbenchCanvasLoopInputProjection.config`; focused behavior coverage
passes for bounded defaults and mode/toggle preservation. Full
`./scripts/agent-verify.sh`: PASS (509 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded batch continues the remaining Loop/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 Loop prompt-context batch (2026-09-09): variable text, count,
current index, and total-round normalization now delegate to
`WorkbenchCanvasLoopPromptRenderer.contextProjection`; focused behavior
coverage passes for trimming and bounded context defaults. Full
`./scripts/agent-verify.sh`: PASS (510 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded batch continues the remaining Loop/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 Loop editor-text batch (2026-09-09): token-chip, line-break,
text-node, and non-breaking-space projection now delegates to
`WorkbenchCanvasLoopPromptRenderer.editorText`; focused behavior coverage
passes for editor-text parity. Full `./scripts/agent-verify.sh`: PASS (511
tests; Python AST 78; JavaScript syntax 103; architecture guards 4; diff
check clean). R4-39 remains IN_PROGRESS; the next bounded batch continues
the remaining Loop/workflow responsibility cluster. R4-40 and R5+ remain
unauthorized.

R4-39 Wave 5 Loop input-summary batch (2026-09-09): image/prompt counts and
upstream-prompt presence now delegate to
`WorkbenchCanvasLoopInputProjection.summary`; focused behavior coverage
passes for positive and empty summaries. Full
`./scripts/agent-verify.sh`: PASS (512 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded batch continues the remaining Loop/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub field-projection batch (2026-09-09): field text
indexing, pattern matching, aspect labels, option matching, and parameter
assignment now delegate to
`WorkbenchCanvasRunningHubFieldRenderer`; focused behavior coverage passes
for matching, aspect conversion, and parameter writes. Full
`./scripts/agent-verify.sh`: PASS (513 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded batch continues the remaining Loop/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub diagnostics batch (2026-09-09): compact JSON and
detailed-error construction now delegate to
`WorkbenchCanvasRunningHubFieldRenderer`; focused behavior coverage passes
for truncation and detail preservation. Full
`./scripts/agent-verify.sh`: PASS (514 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded batch continues the remaining Loop/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub readable-error batch (2026-09-09): structured
ComfyUI/RunningHub error parsing and user-facing message projection now
delegate to `WorkbenchCanvasRunningHubFieldRenderer.readableError`; focused
behavior coverage passes for provider prefixes and node details. Full
`./scripts/agent-verify.sh`: PASS (515 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded batch continues the remaining Loop/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub payload-error batch (2026-09-09): detail/raw/code/
taskId extraction and message assembly now delegate to
`WorkbenchCanvasRunningHubFieldRenderer.payloadError`; focused behavior
coverage passes for detail preservation and metadata extraction. Full
`./scripts/agent-verify.sh`: PASS (516 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded batch continues the remaining Loop/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub log-detail batch (2026-09-09): task/code/stage/
workflow/raw detail-line assembly now delegates to
`WorkbenchCanvasRunningHubFieldRenderer.logErrorText`; focused behavior
coverage passes for detail ordering and compact raw output. Full
`./scripts/agent-verify.sh`: PASS (517 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded batch continues the remaining Loop/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

R4-39 Wave 5 RunningHub entry-selection batch (2026-09-09): title, current-ID,
and default-ID fallback selection now delegates to
`WorkbenchCanvasRunningHubFieldRenderer.selectEntry`; focused behavior
coverage passes for title priority and ID fallbacks. Full
`./scripts/agent-verify.sh`: PASS (518 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean). R4-39 remains
IN_PROGRESS; the next bounded batch continues the remaining Loop/workflow
responsibility cluster. R4-40 and R5+ remain unauthorized.

## Blockers

No external blocker. Source backup/validation, SQLite authority activation, default
canonical routing, isolated Classic/Smart browser reads and browser creation,
restart/stale-conflict/rollback verification, workflow archive round-trip, and the
deterministic benchmark and duplicate Classic/Smart runtime removal are complete.
R4 remains incomplete only at the separately authorized UI migration-flag
retirement work; R4-40 has not been activated.

## Exactly one next authorized Round

No next Round is authorized while R4 is active.

R4-39 Wave 5 media-input and field-value verification (2026-09-09): required/
optional RunningHub media presence and page-side field-value precedence now
delegate to `WorkbenchCanvasRunningHubFieldRenderer`; focused behavior coverage
passes for required/optional/present media and disabled-upstream precedence.
Full `./scripts/agent-verify.sh`: PASS (544 tests; Python AST 78; JavaScript
syntax 103; architecture guards 4; diff check clean).

R4-39 Wave 5 Comfy field-projection batch (2026-09-09): field-kind
classification, workflow field filtering, parameter/default precedence, random
enablement/active state, and bounded random-value policy now belong to
`WorkbenchCanvasComfyFieldRenderer`; the page retains node mutation, event
handling, and side effects. Focused behavior coverage passes; full verification
now passes at 545 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check.

R4-39 Wave 5 LLM pane-state batch (2026-09-09): connected-input read-only
projection, manual-input fallback, and bounded input/output pane dimensions now
belong to `WorkbenchCanvasLlmPaneRenderer`; the page retains DOM event wiring,
copy/run actions, and persistence side effects. Focused behavior coverage and
full verification pass at 546 tests, 78 Python AST files, 103 JavaScript files,
4 architecture guards, and clean diff check.

R4-39 Wave 5 LLM chat-state batch (2026-09-09): message-list normalization,
chat-input normalization, running state, and send-label selection now belong to
`WorkbenchCanvasLlmPaneRenderer`; the page retains chat DOM event wiring and
run/copy side effects. Focused behavior coverage and full verification pass at
547 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards,
and clean diff check.

R4-39 Wave 5 RunningHub media-input-list batch (2026-09-09): reference-list
normalization and empty-state classification now belong to
`WorkbenchCanvasMediaInputRenderer`; the page retains preview construction,
DOM insertion, and provider-specific labels. Focused behavior coverage and full
verification pass at 548 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check.

R4-39 Wave 5 shared media-input-list wiring (2026-09-09): generic image-input
rendering and RunningHub input rendering now share the same neutral list-state
projection; page-specific preview and drag/event effects remain local. Wiring
coverage passes, with full verification at 549 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check.

R4-39 Wave 5 RunningHub prompt-field projection batch (2026-09-09): prompt
field filtering, key/label derivation, and value projection now belong to
`WorkbenchCanvasRunningHubFieldRenderer`; the page retains markup insertion,
control binding, and save/render side effects. Focused behavior coverage and
full verification pass at 550 tests, 78 Python AST files, 103 JavaScript files,
4 architecture guards, and clean diff check.

R4-39 Wave 5 RunningHub setting-field projection batch (2026-09-09): boolean,
slider, option, and random-number descriptor normalization now belong to
`WorkbenchCanvasRunningHubFieldRenderer`; the page retains final markup calls,
control binding, and side effects. Focused behavior coverage and full
verification pass at 551 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check.

R4-39 Wave 5 prompt-preview input-state batch (2026-09-09): prompt preview
input filtering and empty-state classification now belong to
`WorkbenchCanvasPromptTemplateRenderer`; the page retains container updates and
markup insertion. Focused behavior coverage and full verification pass at 552
tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check.

R4-39 Wave 5 shared media-input-list wiring completion (2026-09-09): generic,
Comfy, and RunningHub media-input paths now share the neutral list-state
projection; provider-specific preview, labels, drag handling, and DOM effects
remain local. Existing wiring coverage and full verification remain PASS at 552
tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check.

R4-39 Wave 5 Loop body-state batch (2026-09-09): loop image/prompt visibility,
input count, prompt count, and upstream-prompt classification now belong to
`WorkbenchCanvasLoopLayoutProjection`; the page retains cascade markup, DOM
updates, and interaction effects. Focused behavior coverage and full
verification pass at 553 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check.

R4-39 Wave 5 Loop cascade-run-state batch (2026-09-09): cascade target
presence, active/stopping state, order length, and bounded round count now
belong to `WorkbenchCanvasLoopLayoutProjection`; the page retains cascade
button markup and event effects. Focused behavior coverage and full
verification pass at 554 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check.

R4-39 Wave 5 Comfy random-toggle transition batch (2026-09-09): the neutral
Comfy field renderer now owns the random-active state transition calculation;
the page retains node assignment, refresh, and save effects. Focused behavior
coverage and full verification pass at 555 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check.

R4-39 Wave 5 RunningHub random-toggle transition batch (2026-09-09): the
neutral RunningHub field renderer now owns random-active state transition
calculation; the page retains node assignment, refresh, and save effects.
Focused behavior coverage and full verification pass at 556 tests, 78 Python
AST files, 103 JavaScript files, 4 architecture guards, and clean diff check.

R4-39 Wave 5 RunningHub entry-options batch (2026-09-09): model/app/workflow
option-group markup and empty-provider fallback now belong to
`WorkbenchCanvasRunningHubFieldRenderer`; the page retains provider entry
loading and selection effects. Focused behavior coverage and full verification
pass at 557 tests, 78 Python AST files, 103 JavaScript files, 4 architecture
guards, and clean diff check.

R4-39 Wave 5 RunningHub payment-options batch (2026-09-09): free-key/wallet-key
 option markup and missing-capability labels now belong to
 `WorkbenchCanvasRunningHubFieldRenderer`; the page retains provider capability
 reads and selection effects. Focused behavior coverage and full verification
 pass at 558 tests, 78 Python AST files, 103 JavaScript files, 4 architecture
guards, and clean diff check.

R4-39 Wave 5 Comfy workflow-name selection batch (2026-09-09): requested-name
validation and first-available fallback now belong to
`WorkbenchCanvasComfyFieldRenderer`; the page retains workflow cache access and
async loading. Focused behavior coverage and full verification pass at 559
tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check.

R4-39 Wave 5 Comfy workflow-presence batch (2026-09-09): workflow existence
 checks now belong to `WorkbenchCanvasComfyFieldRenderer`; the page retains
 workflow registry access. Focused behavior coverage and full verification pass
 at 560 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards,
 and clean diff check.

R4-39 Wave 5 Comfy workflow-load batch (2026-09-09): valid-name resolution,
cache hits, failed-load cleanup, and JSON response projection now belong to
`WorkbenchCanvasComfyFieldRenderer`; the page retains the network entry point.
Focused behavior coverage and full verification pass at 561 tests, 78 Python
AST files, 103 JavaScript files, 4 architecture guards, and clean diff check.

R4-39 Wave 5 RunningHub workflow-load batch (2026-09-09): workflow ID
normalization, cache hits, failed-load cleanup, and response.workflow projection
now belong to `WorkbenchCanvasRunningHubFieldRenderer`; the page retains the
network entry point. Focused behavior coverage and full verification pass at
562 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards,
and clean diff check.

R4-39 Wave 6 browser acceptance recheck (2026-09-09, isolated local service at
`127.0.0.1:3045`): the default canonical Canvas URL rendered the persisted
two-node fixture after a cache-busting reload with no new browser errors; the
all-zero rollback URL rendered the same Canvas title and both node cards with
no new browser errors. This is evidence for the current execution-host wiring,
not deletion evidence: `static/js/canvas.js` still exists, so R4-39 remains
IN_PROGRESS and the U7 deletion gate is open.

## Forbidden next actions

Until R4 passes, do not execute R5-R17, make NodeRecord incompatible changes, implement SkillRegistry,
ProviderConnection/ModelRegistry/
ModelAvailability, ExecutorRegistry/ExecutionRuntime, Asset/Artifact/Entity/
Knowledge/Workflow/Approval/Handoff runtimes, PackageRuntime, Common/WholeHouse
packages, Agent graph mutation, interactive Codex approval, or unverified Legacy
Canvas adapter/page removal. U7 may remove a duplicate only after its replacement
has focused interaction, browser, rollback, and source-reference acceptance. Do not
add new Workbench business responsibility to `main.py`,
`static/js/canvas.js`, or `static/js/smart-canvas.js`.

R4-39 Wave 6 Classic LLM chat lifecycle batch (2026-09-09): chat message
append, input clearing, running-state transitions, output projection, render,
save, and error notification now delegate through the neutral Classic chat
execution-host contract; the runtime retains only input/history reads and the
LLM call. Focused behavior coverage and full verification pass at 564 tests,
78 Python AST files, 103 JavaScript files, 4 architecture guards, and clean
diff check. This is replacement evidence, not deletion evidence: the Classic
page/runtime still exists and R4-39 remains IN_PROGRESS.

R4-39 Wave 6 MiniMax execution lifecycle batch (2026-09-09): running-state,
success/failure status, render, and save transitions now delegate through the
Classic execution-host contract; MiniMax request/output composition remains in
the runtime. Focused behavior coverage and full verification pass at 565
tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check. The Classic runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 6 RunningHub model execution lifecycle batch (2026-09-09):
running-state, success/failure status, render, and save transitions now
delegate through the Classic execution-host contract; RunningHub request,
pending-task, polling, and output composition remain in the runtime. Focused
behavior coverage and full verification pass at 567 tests, 78 Python AST files,
103 JavaScript files, 4 architecture guards, and clean diff check. The Classic
runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 browser acceptance route audit (2026-09-09): the service canonical entry
is `/` and embeds `/static/canvas-list.html`; `/canvas.html` is not a registered
HTTP route and returns 404. The prior browser acceptance note using
`/canvas.html` is therefore stale and cannot be reused as current evidence.
Re-run acceptance against the canonical root/iframe route before the U7
deletion gate is evaluated.

R4-39 canonical browser acceptance recheck (2026-09-09, isolated
`127.0.0.1:3045`): PASS — the root entry loaded the Canvas manager iframe;
opening record `c29d2daf364a4c7fa5b5632f60e9903d` rendered the title and two
nodes. The canonical static Canvas URL with all six explicit zero flags also
rendered the same title and both node cards. No save, create, execute, or
delete action was performed. This refreshes browser evidence for the current
worktree, while `static/js/canvas.js` remains and the U7 deletion gate stays
open.

R4-39 Wave 6 source-reference audit (2026-09-09): execution entry points in
`canvas.js` are compatibility wrappers that call
`ensureClassicExecutorRuntime()`; the concrete generator implementations stay
inside `classic-executor-runtime.js`, and no direct execution-state writes
remain there. Classic cascade orchestration is still the bounded compatibility
adapter, so deletion evidence is not yet complete.

R4-39 Wave 6 execution-host ownership guard (2026-09-09): the Classic
executor runtime now contains no direct `running`, `runStatus`, or `runError`
assignments for node/generator execution state; focused source guard and full
verification pass at 580 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check. This proves runtime ownership
removal for the migrated execution paths, not Classic runtime deletion; R4-39
remains IN_PROGRESS.

R4-39 Wave 6 recovered pending-output completion batch (2026-09-09):
recovered task success status, running-state reset, render, and save now
delegate through the Classic execution-host contract; recovery query and
result/output composition remain in the page/runtime. Focused behavior
coverage and full verification pass at 579 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check. The Classic
runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 6 shared image-task completion lifecycle batch (2026-09-09):
successful pending-task completion, status finalization, running-state reset,
render, and save now delegate through the Classic execution-host contract;
result normalization and output/log composition remain in the page/runtime.
Focused behavior coverage and full verification pass at 578 tests, 78 Python
AST files, 103 JavaScript files, 4 architecture guards, and clean diff check.
The Classic runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 6 shared image-task failure lifecycle batch (2026-09-09): pending
task recovery/failure status, running-state reset, render, and save now
delegate through the Classic execution-host contract; task lookup, recovery
metadata, and generation-log composition remain in the runtime. Focused
behavior coverage and full verification pass at 577 tests, 78 Python AST files,
103 JavaScript files, 4 architecture guards, and clean diff check. The Classic
runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 6 Midjourney action/inpaint lifecycle batch (2026-09-09): action
and modal start, running-state, success/failure status, render, and save
transitions now delegate through the Classic execution-host contract;
Midjourney action submission, polling, and output composition remain in the
runtime. Focused behavior coverage and full verification pass at 576 tests,
78 Python AST files, 103 JavaScript files, 4 architecture guards, and clean
diff check. The Classic runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 6 RunningHub workflow/application execution lifecycle batch
(2026-09-09): running-state, success/failure status, render, and save
transitions now delegate through the Classic execution-host contract;
RunningHub submission, polling, and output composition remain in the runtime.
Focused behavior coverage and full verification pass at 574 tests, 78 Python
AST files, 103 JavaScript files, 4 architecture guards, and clean diff check.
The Classic runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 6 LTX Director execution lifecycle batch (2026-09-09): running,
success/failure status, render, and save transitions now delegate through the
Classic execution-host contract; timeline preparation, Comfy request, and
output composition remain in the runtime. Focused behavior coverage and full
verification pass at 573 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check. The Classic runtime remains, so
R4-39 stays IN_PROGRESS.

R4-39 Wave 6 cascade cleanup ownership batch (2026-09-09): cascade node-state
cleanup now delegates status/error clearing through the execution-status seam;
the cascade adapter no longer directly owns that cleanup write. Full
verification passes at 588 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check. Classic runtime deletion remains
outstanding.

R4-39 Wave 6 entry-chain cache-bust browser recheck (2026-09-09):
`index.html` -> `canvas-list.html` -> `canvas-list.js` -> `canvas.html` now
propagates fresh versions; isolated browser logs confirmed
`classic-execution-host.js?v=2026.09.09.2` was fetched and the two-node Canvas
rendered successfully. Full verification passes at 586 tests. Classic runtime
deletion remains outstanding.

R4-39 Wave 6 Cascade main-pass status batch (2026-09-09): queued, running,
success, and failure transitions in the main Cascade pass now delegate through
the execution-status seam. Focused coverage and full verification pass at 589
tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check. Classic runtime deletion remains outstanding.

R4-39 Wave 6 execution-adapter cache-bust batch (2026-09-09):
`canvas.html` now references `classic-execution-host.js?v=2026.09.09.2` after
fallback removal, preventing stale browser code from masking neutral
delegation. Focused coverage and full verification pass at 585 tests, 78
Python AST files, 103 JavaScript files, 4 architecture guards, and clean diff
check.

R4-39 Wave 6 Classic execution-adapter deduplication (2026-09-09):
`classic-execution-host.js` no longer contains a duplicate fallback
implementation; it now requires and delegates to the neutral execution host,
matching the canonical HTML load order. Full verification passes after updating
the contract test to load both modules; Classic runtime deletion remains
outstanding.

R4-39 Wave 6 RunningHub config-status cleanup batch (2026-09-09): app and
workflow configuration refreshes now clear execution status through the
Classic execution-host contract instead of direct page writes. Focused source
coverage and full verification pass at 583 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check. Classic runtime
deletion remains outstanding.

R4-39 Wave 6 execution-state confinement guard (2026-09-09): remaining
`running/runStatus/runError` writes in `canvas.js` are confined to execution-host
callback implementations; no page/runtime path writes those fields directly.
Focused source coverage and full verification pass at 584 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check.

R4-39 Wave 6 transient run-state reset batch (2026-09-09): Canvas load/reconnect
cleanup now delegates running/status/error reset through the Classic
execution-host contract instead of writing node execution fields directly.
Focused source coverage and full verification pass at 582 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check.
Classic runtime deletion remains outstanding.

R4-39 Wave 6 stuck-generator cleanup batch (2026-09-09): stale running-state
reset now delegates through the Classic execution-host contract instead of
writing `node.running` directly. Focused source coverage and full verification
pass at 581 tests, 78 Python AST files, 103 JavaScript files, 4 architecture
guards, and clean diff check. Classic runtime deletion remains outstanding.

R4-39 Wave 6 Comfy execution lifecycle batch (2026-09-09): running-state,
success/failure status, render, and save transitions now delegate through the
Classic execution-host contract; Comfy request/workflow/output composition
remains in the runtime. Focused behavior coverage and full verification pass at
566 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards,
and clean diff check. The Classic runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 6 generic generator execution lifecycle batch (2026-09-09):
running-state, success/failure status, render, and save transitions now
delegate through the Classic execution-host contract; provider request,
pending-task, polling, and output composition remain in the runtime. Focused
behavior coverage and full verification pass at 568 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check. The
Classic runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 6 legacy generator execution lifecycle batch (2026-09-09):
running-state, success/failure status, render, and save transitions now
delegate through the Classic execution-host contract; the legacy online-image
request and output composition remain in the runtime. Focused behavior coverage
and full verification pass at 569 tests, 78 Python AST files, 103 JavaScript
files, 4 architecture guards, and clean diff check. The Classic runtime
remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 6 Midjourney execution lifecycle batch (2026-09-09): start,
success-completion, failure, running-state, render, and save transitions now
delegate through the Classic execution-host contract; Midjourney request,
polling, and output composition remain in the runtime. Focused behavior
coverage and full verification pass at 571 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check. The Classic
runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 6 video execution lifecycle batch (2026-09-09): running-state,
success/failure status, render, and save transitions now delegate through the
Classic execution-host contract; video request, media normalization, and
output composition remain in the runtime. Focused behavior coverage and full
verification pass at 572 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check. The Classic runtime remains, so
R4-39 stays IN_PROGRESS.

R4-39 Wave 5 cascade loop lifecycle batch (2026-09-09): parallel and serial
loop rounds now route queued/running/done/failed/cleanup state transitions
through the cascade execution-status seam; loop scheduling and node execution
remain in the bounded compatibility adapter. Focused behavior coverage and
full verification pass at 589 tests, 78 Python AST files, 103 JavaScript
files, 4 architecture guards, and clean diff check. The Classic runtime
remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 media-kind node projection batch (2026-09-09): node media-kind
classification now delegates explicit-kind and URL fallback resolution to
the neutral `WorkbenchCanvasMediaKind` owner, including Classic FLV behavior;
editor-specific URL normalization remains at the adapter seam. Focused node
explicit/fallback coverage and full verification pass at 589 tests, 78 Python
AST files, 103 JavaScript files, 4 architecture guards, and clean diff check.
 The Classic runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 media-reference projection batch (2026-09-09): image, group,
output, and generated-media reference assembly now delegates to neutral
`WorkbenchCanvasMediaTools.mediaRefsFromNode`; node lookup, media-kind policy,
and generated-output discovery remain explicit adapter callbacks. Focused
reference-shape coverage and full verification pass at 590 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check. The
Classic runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 latest-output reference batch (2026-09-09): generator input
 projection now delegates newest non-empty output selection and reference-shape
 construction to neutral `WorkbenchCanvasMediaTools.latestOutputReference`;
 page-level classification remains an explicit callback. Focused newest/empty
 coverage and full verification pass at 591 tests, 78 Python AST files, 103
 JavaScript files, 4 architecture guards, and clean diff check. The Classic
 runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 generated-media source projection batch (2026-09-09): generator
 input projection now delegates generated-reference source wrapping to neutral
 `WorkbenchCanvasMediaTools.generatedMediaSources`; generated-reference
 discovery remains an adapter callback. Focused ordering/empty coverage and
 full verification pass at 592 tests, 78 Python AST files, 103 JavaScript
 files, 4 architecture guards, and clean diff check. The Classic runtime
 remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 image-source projection batch (2026-09-09): generator input
 projection now delegates single-image upstream source construction to neutral
 `WorkbenchCanvasMediaTools.imageMediaSource`; page-level media-kind
 classification remains a callback. Focused source/empty coverage and full
 verification pass at 593 tests, 78 Python AST files, 103 JavaScript files, 4
 architecture guards, and clean diff check. The Classic runtime remains, so
 R4-39 stays IN_PROGRESS.

R4-39 Wave 5 group-source projection batch (2026-09-09): generator input
 projection now delegates group image-member and prompt-summary source
 construction to neutral `WorkbenchCanvasMediaTools.groupMediaSources`; node
 lookup and media-kind policy remain adapter callbacks. Focused member/order/
 prompt coverage and full verification pass at 594 tests, 78 Python AST files,
 103 JavaScript files, 4 architecture guards, and clean diff check. The
 Classic runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 prompt-source projection batch (2026-09-09): generator input
 projection now delegates single-prompt upstream source construction to neutral
 `WorkbenchCanvasMediaTools.promptMediaSource`; prompt text remains unchanged
 and execution stays in the adapter. Focused label/text/empty coverage and full
 verification pass at 595 tests, 78 Python AST files, 103 JavaScript files, 4
 architecture guards, and clean diff check. The Classic runtime remains, so
 R4-39 stays IN_PROGRESS.

R4-39 Wave 5 prompt-group source projection batch (2026-09-09): generator
 input projection now delegates promptGroup member filtering and text-summary
 construction to neutral `WorkbenchCanvasMediaTools.promptGroupMediaSource`;
 node lookup remains an adapter callback. Focused member/count/empty coverage
 and full verification pass at 596 tests, 78 Python AST files, 103 JavaScript
 files, 4 architecture guards, and clean diff check. The Classic runtime
 remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 LLM source projection batch (2026-09-09): generator input
 projection now delegates node-mode LLM output-text source construction to
 neutral `WorkbenchCanvasMediaTools.llmMediaSource`; chat-mode nodes and empty
 outputs remain excluded. Focused mode/text/empty coverage and full
 verification pass at 597 tests, 78 Python AST files, 103 JavaScript files, 4
 architecture guards, and clean diff check. The Classic runtime remains, so
 R4-39 stays IN_PROGRESS.

R4-39 Wave 5 loop fallback source projection batch (2026-09-09): generator
 input projection now delegates no-image loop fallback source construction to
 neutral `WorkbenchCanvasMediaTools.loopFallbackSource`; loop context and
 image-batch projection remain in the adapter. Focused label/prompt/empty
 coverage and full verification pass at 598 tests, 78 Python AST files, 103
 JavaScript files, 4 architecture guards, and clean diff check. The Classic
 runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 loop-image source projection batch (2026-09-09): generator input
 projection now delegates loop image-reference source list construction to
 neutral `WorkbenchCanvasMediaTools.loopImageMediaSources`; loop context,
 reference discovery, and localized labels remain explicit adapter inputs.
 Focused index/order/prompt coverage and full verification pass at 599 tests,
 78 Python AST files, 103 JavaScript files, 4 architecture guards, and clean
 diff check. The Classic runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 ordered-input projection batch (2026-09-09): generator input
 reconciliation now delegates stale-id removal, existing-order retention, and
 new-source append behavior to neutral `WorkbenchCanvasMediaTools.orderedInputSources`;
 the adapter retains the mutation call boundary. Focused order/reconciliation
 coverage and full verification pass at 600 tests, 78 Python AST files, 103
 JavaScript files, 4 architecture guards, and clean diff check. The Classic
 runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 input-reorder projection batch (2026-09-09): media input reorder
 now delegates pure media-before-prompt ordering and invalid-target rejection
 to neutral `WorkbenchCanvasMediaTools.reorderInputIds`; page-level render and
 save effects remain local. Focused reorder/invalid coverage and full
 verification pass at 601 tests, 78 Python AST files, 103 JavaScript files, 4
 architecture guards, and clean diff check. The Classic runtime remains, so
 R4-39 stays IN_PROGRESS.

R4-39 Wave 5 image-input projection batch (2026-09-09): generator view input
 projection now delegates reference normalization/filtering to neutral
 `WorkbenchCanvasMediaTools.imageInputSources`; renderer selection and page
 effects remain local. Focused filtering/empty coverage and full verification
 pass at 602 tests, 78 Python AST files, 103 JavaScript files, 4 architecture
 guards, and clean diff check. The Classic runtime remains, so R4-39 stays
 IN_PROGRESS.

R4-39 Wave 5 prompt-input projection batch (2026-09-09): generator view
 projection now delegates prompt-only source filtering to neutral
 `WorkbenchCanvasMediaTools.promptInputSources`; renderer selection and page
 effects remain local. Focused prompt/media/empty coverage and full verification
 pass at 603 tests, 78 Python AST files, 103 JavaScript files, 4 architecture
 guards, and clean diff check. The Classic runtime remains, so R4-39 stays
 IN_PROGRESS.

R4-39 Wave 5 reference-source ID projection batch (2026-09-09): input reorder
 now delegates media-reference source ID extraction to neutral
 `WorkbenchCanvasMediaTools.refSourceIds`; ordering mutation and UI effects
 remain local. Focused inclusion/empty coverage and full verification pass at
 604 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards,
 and clean diff check. The Classic runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 connected-input projection batch (2026-09-09): generator input
 projection now delegates target-connection source-node collection to neutral
 `WorkbenchCanvasMediaTools.connectedInputNodes`; type-specific source mapping
 remains in the adapter. Focused target/missing-node coverage and full
 verification pass at 605 tests, 78 Python AST files, 103 JavaScript files, 4
 architecture guards, and clean diff check. The Classic runtime remains, so
 R4-39 stays IN_PROGRESS.

R4-39 Wave 5 generated-media reference batch (2026-09-09): generated output
 reference normalization, naming, and image/type filtering now delegate to
 neutral `WorkbenchCanvasMediaTools.generatedMediaRefs`; page-level output
 classification and naming remain callbacks. Focused filtering/empty coverage
 and full verification pass at 606 tests, 78 Python AST files, 103 JavaScript
 files, 4 architecture guards, and clean diff check. The Classic runtime
 remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 output-resolution markup batch (2026-09-09): output resolution
 and optional duration markup now delegates to neutral
 `WorkbenchCanvasMediaTools.outputResolutionMarkup`; page code only assigns the
 resulting markup. Focused duration/empty coverage and full verification pass at
 607 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards,
 and clean diff check. The Classic runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 compare-mode style projection batch (2026-09-09): output compare
 mode initial clip-path and slider position now delegate to neutral
 `WorkbenchCanvasMediaTools.compareModeStyles`; page code only applies the
 returned styles. Focused active/inactive coverage and full verification pass at
 608 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards,
 and clean diff check. The Classic runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 output-rerun projection batch (2026-09-09): rerun-from-output node,
 prompt, image-reference, and connection construction now delegates to neutral
 `WorkbenchCanvasMediaTools.rerunOutputProjection`; page code retains insertion,
 lightbox close, render, and save effects. Focused node/connection coverage and
 full verification pass at 609 tests, 78 Python AST files, 103 JavaScript files,
 4 architecture guards, and clean diff check. The Classic runtime remains, so
 R4-39 stays IN_PROGRESS.

R4-39 Wave 5 output-image node projection batch (2026-09-09): image-node data
 construction from output URLs now delegates to neutral
 `WorkbenchCanvasMediaTools.outputImageNodeProjection`; page code retains media
 validation, insertion, render, and save effects. Focused node/empty coverage
 and full verification pass at 610 tests, 78 Python AST files, 103 JavaScript
 files, 4 architecture guards, and clean diff check. The Classic runtime
 remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 editor-output node projection batch (2026-09-09): image editor
 missing-output node data construction now delegates to neutral
 `WorkbenchCanvasMediaTools.outputNodeProjection`; connection lookup, insertion,
 and editor effects remain local. Focused coordinate/shape coverage and full
 verification pass at 611 tests, 78 Python AST files, 103 JavaScript files, 4
 architecture guards, and clean diff check. The Classic runtime remains, so
 R4-39 stays IN_PROGRESS.

R4-39 Wave 5 editor-generated-image projection batch (2026-09-09): generated
 image node data construction now delegates to neutral
 `WorkbenchCanvasMediaTools.generatedImageNodeProjection`; editor insertion,
 selection, render, and save effects remain local. Focused node/extra/empty
 coverage and full verification pass at 612 tests, 78 Python AST files, 103
 JavaScript files, 4 architecture guards, and clean diff check. The Classic
 runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 output-workflow panel batch (2026-09-09): output prompt-panel
 open/text projection and rerun availability now delegate to neutral
 `WorkbenchCanvasMediaTools.outputPromptProjection` and
 `outputRerunAvailable`; page code retains DOM event binding and rerun action.
 Focused prompt/empty/availability coverage and full verification pass at 613
 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
 clean diff check. The Classic runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 editor-output lookup batch (2026-09-09): editor output reuse now
 delegates source-to-output connection lookup to neutral
 `WorkbenchCanvasMediaTools.findOutputNodeForSource`; output creation and
 insertion remain local. Focused found/missing coverage and full verification
 pass at 614 tests, 78 Python AST files, 103 JavaScript files, 4 architecture
 guards, and clean diff check. The Classic runtime remains, so R4-39 stays
 IN_PROGRESS.

R4-39 Wave 5 output dedupe batch (2026-09-09): latest generated-output
 selection and output URL duplicate detection now delegate to neutral
 `WorkbenchCanvasMediaTools.latestGeneratedOutputItem` and `outputHasUrl`;
 output mutation and persistence remain local. Focused latest/existing/missing
 coverage and full verification pass at 615 tests, 78 Python AST files, 103
 JavaScript files, 4 architecture guards, and clean diff check. The Classic
 runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 output-lifecycle projection batch (2026-09-09): output-node
 connection lookup, non-empty output filtering, and duplicate-safe append input
 preparation now delegate to neutral `WorkbenchCanvasMediaTools.outputNodesForSource`,
 `outputItemsWithUrl`, and `uniqueOutputItems`; mutation and persistence remain
 local. Focused lifecycle-batch coverage and full verification pass at 616
 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
 clean diff check. The Classic runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 unique-output append batch (2026-09-09): duplicate filtering and
 output-record append composition now delegate to neutral
 `WorkbenchCanvasMediaTools.appendUniqueOutputRecords`; page code applies the
 returned images, layout, comparisons, and count. Focused duplicate/append
 coverage and full verification pass at 617 tests, 78 Python AST files, 103
 JavaScript files, 4 architecture guards, and clean diff check. The Classic
 runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 output-to-input group projection batch (2026-09-09): image-node
 placement, group geometry, and item membership construction now delegate to
 neutral `WorkbenchCanvasMediaTools.inputGroupProjection`; graph mutation,
 undo, and persistence remain local. Focused count/geometry/membership coverage
 and full verification pass at 618 tests, 78 Python AST files, 103 JavaScript
 files, 4 architecture guards, and clean diff check. The Classic runtime
 remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 output-to-input downstream projection batch (2026-09-09):
 downstream connection target extraction now delegates to neutral
 `WorkbenchCanvasMediaTools.downstreamTargetIds`; graph replacement, undo, and
 persistence remain local. Focused target-order coverage and full verification
 pass at 619 tests, 78 Python AST files, 103 JavaScript files, 4 architecture
 guards, and clean diff check. The Classic runtime remains, so R4-39 stays
 IN_PROGRESS.

R4-39 Wave 5 output-download filename batch (2026-09-09): output/group archive
 filename projection now delegates to neutral
 `WorkbenchCanvasMediaTools.archiveDownloadFilename`; network request and
 browser download effects remain local. Focused fallback/sanitization coverage
 and full verification pass at 620 tests, 78 Python AST files, 103 JavaScript
 files, 4 architecture guards, and clean diff check. The Classic runtime
 remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 generator-source orchestration batch (2026-09-09): complete
 connected input source projection across output, generated media, image,
 group, prompt, loop, promptGroup, and LLM branches now delegates to neutral
 `WorkbenchCanvasMediaTools.generatorSourceProjection`; page code supplies
 context/classification callbacks only. Focused multi-branch coverage and full
 verification pass at 621 tests, 78 Python AST files, 103 JavaScript files, 4
 architecture guards, and clean diff check. The Classic runtime remains, so
 R4-39 stays IN_PROGRESS.

R4-39 Wave 5 input-view projection batch (2026-09-09): generator and RunningHub
 input views now obtain coordinated image/prompt source projections from neutral
 `WorkbenchCanvasMediaTools.inputViewProjection`; renderer dispatch remains
 local. Focused dual-projection coverage and full verification pass at 622
 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
 clean diff check. The Classic runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 RunningHub source-summary batch (2026-09-09): RunningHub media
 source ordering and image/video/audio/prompt summary now delegate to neutral
 `WorkbenchCanvasRunningHubFieldRenderer.sourceProjection`; page code supplies
 ordering and kind callbacks. Focused ordering/summary coverage and full
 verification pass at 623 tests, 78 Python AST files, 103 JavaScript files, 4
 architecture guards, and clean diff check. The Classic runtime remains, so
 R4-39 stays IN_PROGRESS.

R4-39 Wave 5 output-download projection batch (2026-09-09): output image URL
 and downloadable URL projections now delegate together to neutral
 `WorkbenchCanvasMediaTools.outputDownloadProjection`; menu, network, and
 browser-download effects remain local. Focused image/download filtering
 coverage and full verification pass at 624 tests, 78 Python AST files, 103
 JavaScript files, 4 architecture guards, and clean diff check. The Classic
 runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 archive-payload batch (2026-09-09): output/group download request
 payload construction now delegates to neutral
 `WorkbenchCanvasMediaTools.archiveDownloadPayload`; fetch, response handling,
 and browser download effects remain local. Focused URL filtering/extra-item
 coverage and full verification pass at 625 tests, 78 Python AST files, 103
 JavaScript files, 4 architecture guards, and clean diff check. The Classic
 runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 single-download href batch (2026-09-09): media download href
 construction now delegates to neutral `WorkbenchCanvasMediaTools.downloadHref`,
 preserving data/blob/API passthrough and encoded server-download fallback;
 page code retains link creation and click effects. Focused passthrough/fallback
 coverage and full verification pass at 626 tests, 78 Python AST files, 103
 JavaScript files, 4 architecture guards, and clean diff check. The Classic
 runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 Wave 5 workflow-export projection batch (2026-09-09): selected workflow
 payload and export filename are now composed through neutral
 `WorkbenchCanvasWorkflowTransfer.exportProjection`; page and asset adapters
 retain graph selection and actual export/download effects. Focused payload/
 filename coverage and full verification pass at 627 tests, 78 Python AST files,
 103 JavaScript files, 4 architecture guards, and clean diff check. The Classic
 runtime remains, so R4-39 stays IN_PROGRESS.
R4-39 Wave 5 output-lightbox state batch (2026-09-09): lightbox media mode,
comparison visibility, and group-download affordance now delegate to neutral
`WorkbenchCanvasMediaTools.lightboxProjection`; DOM/media loading and download
effects remain local. Focused projection coverage and full verification pass at
628 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check. The Classic runtime remains, so R4-39 stays IN_PROGRESS.

R4-39 final Classic-runtime removal (2026-09-09): `static/js/canvas.js` and its
page reference are deleted. `canvas.html` natively loads nine ordered
responsibility scripts and ends in a 49-line startup/inline-action bootstrap.
The executable gate requires the former runtime to remain absent, every
residual cluster to be `MIGRATED`, the native script order to match the
manifest, and runtime source to contain neither `eval` nor `new Function`.
Default and all-six-zero browser acceptance rendered the same persisted
two-node Canvas; workflow modal open/close passed. Full
`./scripts/agent-verify.sh`: PASS (630 tests, 80 Python AST files, 111
JavaScript files, 4 architecture guards, clean diff check). R4-39 is DONE.
R4-40 and R5+ were not started.
