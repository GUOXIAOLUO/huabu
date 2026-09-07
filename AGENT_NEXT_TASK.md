# Agent Next Task

> This file is the single task-selection authority for coding agents.
> It does not replace `docs/status/CURRENT_EXECUTION_STATUS.md`.

## Active Task

- `R4-38` — `IN_PROGRESS` (umbrella shrink; multi-wave; closes only
  when canvas.js is bootstrap/compat-only). Card:
  `docs/tasks/active/R4-38-shrink-classic-runtime.md`. Activated
  2026-09-07T15:30+08:00 (after R4-37 close, with Owner authorization
  via in-conversation "提交并开发下一任务"). Goal: shrink the Classic
  runtime (`canvas.js`, 17 001 lines) so it no longer owns Canvas
  product runtime responsibilities. The R4-31 inventory's 13 Classic
  capabilities partition into a 12-wave shrink plan (each wave = one
  focused migration of one inventory capability into the corresponding
  shared seam / bounded compat). **Wave 1 done** 2026-09-07T15:33+08:00
  (comfy-result-normalization MIGRATED: deleted `comfyResultOutputs` /
  `resultMediaUrls` wrappers in canvas.js, inlined 6 call sites through
  `window.WorkbenchCanvasMediaResultNormalizer.extract`, focused test
  `test_classic_editor_inlines_execution_result_extraction_through_the_shared_seam`
  +1 → 344 tests PASS). **Wave 2 done** 2026-09-07T15:55+08:00
  (provider-node-creation MIGRATED: new host seam
  `static/js/workbench/canvas/classic-node-factories.js`
  (`WorkbenchCanvasClassicNodeFactories.create({addNode, uid,
  defaultPoint, imageApiProviders, allImageModels,
  defaultApiImageResolution, resolveMidjourneyProviderId,
  modelscopeImageModels})` returns frozen `{addGenerator, addMidjourney,
  addMsGen}`); canvas.js deleted the three local factory function
  definitions and re-routes its `createNodeByType` dispatcher through
  `ensureClassicNodeFactories().addXxx({point})`; canvas.html loads the
  seam between `provider-controls.js` and `classic-execution-host.js`;
  focused test
  `test_classic_editor_routes_provider_node_creation_through_classic_node_factories_seam`
  drives the seam in a vm sandbox with mock host, asserts exact addNode
  records, iterates 8 required host ops for TypeError-on-missing, pins
  canvas.html load order + canvas.js wrapper-deletion + dispatcher
  seam-call shapes; inventory `provider-node-creation` row updated
  disposition `MIGRATE → MIGRATED` + new schema field
  `evidence_target` pointing at the seam module — +1 → 345 tests PASS).
  **Wave 3 done** 2026-09-07T16:05+08:00 (video-node-creation MIGRATED:
  seam extended with 4 new REQUIRED host ops
  `videoApiProviders` / `providerVideoModels` / `videoModels` /
  `defaultVideoModels` (8 → 12) + new `addVideo({point})` method;
  canvas.js deletes `function addVideoNode` (-26 LOC); `'video'`
  dispatch re-routed through `ensureClassicNodeFactories().addVideo({point})`;
  inventory's `video-player` row SPLIT into `video-node-creation`
  MIGRATED + `video-card-body` COMPAT/R8; Wave 2 test extended for
  full 12-op REQUIRED coverage; new focused test
  `test_classic_editor_routes_video_node_creation_through_classic_node_factories_seam`
  drives addVideo + asserts exact record shape + source-contracts
  wrapper-deletion + dispatcher seam-call + host injection of the 4
  new ops including `defaultVideoModels: () => DEFAULT_VIDEO_MODELS`
  const-returning closure — +1 → 346 tests PASS). **Wave 4 done**
  2026-09-07T16:13+08:00 (output-node-creation MIGRATED: seam extended
  with `addOutput({point})` method only — no new REQUIRED ops; canvas.js
  deletes `function addOutputNode` (-6 LOC, trivial factory body);
  `'output'` dispatch re-routed through
  `ensureClassicNodeFactories().addOutput({point})`; inventory's
  `output-node` row SPLIT into `output-node-creation` MIGRATED +
  `output-grid-renderer` COMPAT/R8; new focused test
  `test_classic_editor_routes_output_node_creation_through_classic_node_factories_seam`
  drives addOutput + asserts exact record shape `(type:'output',
  id:'out-test', x:444, y:555, images:[])` + source-contracts
  wrapper-deletion + dispatcher seam-call; inventory test
  `test_classification_is_meaningful_across_dispositions` loosened to
  COMPAT+DEFER-R8 invariants with MIGRATE=0+MIGRATED≥1 healthy
  terminal state — +1 → 347 tests PASS). **Wave 5 done**
  2026-09-07T16:30+08:00 (provider-card-body COMPAT seam: new bounded
  compat seam `static/js/workbench/canvas/classic-card-body-renderer.js`
  (`WorkbenchCanvasClassicCardBodyRenderer.create({host})` returns
  frozen `{renderLLM, renderGenerator, renderMidjourney, renderMsGen}`);
  canvas.js deletes the four large page-side body builders
  (`renderLLMBody` / `renderGeneratorBody` / `renderMidjourneyBody` /
  `renderMsGenBody`, ~904 LOC) and re-routes its `createNodeByType`
  dispatcher through `ensureClassicCardBodyRenderer().renderXxx({node})`;
  seam consumes `ensureProviderControls` via host injection so the
  canvas.html load order is pinned
  `provider-controls → card-body → canvas.js`. Host injects all 49
  REQUIRED page-local helpers (escapeHtml / tr / provider + model
  resolvers / image helpers / MsGen catalog / renderImageInputList /
  renderPromptPreview / cascadeBtnHtml / retryBarHtml /
  bindCascadeButtons / scheduleSave / render / runCanvasGenerate /
  ensureProviderControls, etc.). The R4-31 inventory's
  `provider-card-body` row gains `evidence_target =
  static/js/workbench/canvas/classic-card-body-renderer.js` so the
  inventory's evidence-grounding test now looks for the four
  `renderXxxBody` names in the seam module. New focused test drives all
  four render methods in a vm sandbox with a stub document and asserts
  each runs without throwing, exercises the full 49-op
  missing-host-op TypeError loop, source-contracts the four
  wrapper-deletions + dispatcher seam-call shapes + canvas.html load
  order. Pre-existing
  `test_provider_controls_is_loaded_before_the_classic_page_and_llm_body_uses_it`
  updated to target the seam module for the LLM-body assertions (since
  renderLLMBody moved there) and to pin the new load-order chain —
  +1 → 348 tests PASS).
Next wave (recommended successor inside the same card): **Wave 6 —
Comfy workflow/field controls COMPAT seam** (`addComfyNode` +
`renderComfyBody` + `renderComfySettings` + `updateComfyField` +
`comfyWorkflowOptions` as bounded compat per R4-31; the card-body
seam pattern from Wave 5 applies — extract the body builders to
`static/js/workbench/canvas/classic-comfy-controls.js`, page injects
the host ops the body needs).

## Completed Tasks

- `R4-37` — `DONE` 2026-09-07T15:23+08:00. Card:
  `docs/tasks/active/R4-37-remove-smart-runtime.md`. Pre-empted by R4-36
  (accounting close): `static/js/smart-canvas.js` was `git rm`'d by R4-36
  (commit `a4552ee R4-36: delete smart-canvas product page`) after
  R4-28/29/30/32/33/34/35 had migrated every retained Smart behavior behind
  a named bounded seam (Composer `composer.js`, media-tools
  `media-tools.js`, execution-host `execution-host.js`, provider-controls,
  classic-execution-host, native entry on `canvas.js`, handoff removal in
  `canvas-entry-compatibility.js`); by the time R4-37 was activated the
  Smart product runtime was already absent from the working tree. R4-37
  verifies the documented DoD, pins regression parity, and forwards to
  R4-38. Verification at activation (2026-09-07T15:23+08:00): full-repo
  grep for `smart-canvas\.(html|js|css)` against `*.{js,html,css,py}`
  returns zero functional hits (only historical comments remain in
  `canvas-list.js`, `media-tools.js`, `canvas-entry-compatibility.js` and
  the board-row CSS class identifier `smart-canvas` in `canvas.js`,
  which is a class name for Smart-kind rows, not a file reference); the
  `tests/fixtures/canvas/smart-v0.json` Smart payload fixture is retained
  as a historical test input (deleting it would break the R4-25 legacy
  graph-policy behavioral tests that load it — out of scope on this
  card). Ownership matrix `Smart product runtime` row already records
  "(retired)" since R4-36; not re-touched on this card (no new
  ownership move). `./scripts/agent-verify.sh` PASS at 343 tests (was
  343 after R4-36; unchanged — confirms pre-emption), PASS Python AST
  parse (76 files), PASS JavaScript syntax (71 files), PASS Architecture
  guards (4), PASS `git diff --check`. `AGENT VERIFY: PASS`.

- `R4-36` — `DONE` 2026-09-07T15:09+08:00. Card:
  `docs/tasks/active/R4-36-remove-smart-page.md`. Implementer evidence
  (independent review pending): the Smart product page is deleted.
  `static/smart-canvas.html`, `static/js/smart-canvas.js`,
  `static/css/smart-canvas.css`, `static/js/i18n/smart-canvas.js` and
  `tests/test_smart_capability_inventory.py` are removed via `git rm`.
  `static/js/i18n.js` and `static/js/i18n/validate-i18n.js` drop the
  Smart i18n entry; the historical "mirrors smart-canvas.js" comments in
  `canvas-list.js`, `composer.js` and `media-tools.js` are updated to
  record the retirement. `tests/test_frontend_workbench_modules.py`:
  18 dual-iteration sites refactored to single-iteration; 63
  Smart-page-specific test methods removed (every test that read the
  deleted files or asserted Smart-page behavior). `test_canvas_entry.py`
  drops `smart-canvas.js` from the R4-35 routing scan;
  `test_canvas_runtime_state.py` drops the Smart halves of its two
  dual-adapter tests; `test_repository_independence.py` drops the Smart
  page from the GitHub-hosting scan. The R4-27 inventory doc is
  annotated as a frozen historical snapshot; the R4-34 native-entry and
  R4-35 handoff-removal docs are annotated. Ownership matrix gains a
  `Canvas page surface` row recording the sole page; the `Smart product
  runtime` row's evidence pointer is replaced with "(retired)".
  `./scripts/agent-verify.sh` PASS at 343 tests (was 412; -69 from the
  -6 inventory test file and the -63 Smart-specific frontend workbench
  methods).

- `R4-35` — `DONE` 2026-09-07T14:54+08:00. Card:
  `docs/tasks/active/R4-35-remove-smart-handoff.md`. Implementer evidence
  (independent review pending): the Smart product-page handoff surface is
  retired from `WorkbenchCanvasEntryCompatibility`. `requiresLegacySmartHandoff`
  and `legacySmartCanvasUrl` (plus the only `/static/smart-canvas.html` URL
  string) are removed from `static/js/workbench/canvas/canvas-entry-compatibility.js`;
  the module keeps the four-function normal surface (`normalCanvasUrl`,
  `rememberCanvasListProject`, `rememberedCanvasListProject`,
  `canvasListUrl`) used by `canvas.js`, `canvas-list.js`, `asset-manager.js`
  and `smart-canvas.js`. The `smart-canvas.html` / `smart-canvas.js` product
  page stays on disk (out of scope: `R4-36` retires it). A static-JS audit
  finds zero hits for the routable `/static/smart-canvas.html` string
  across `static/js/**/*.js` and `static/js/*.js` — the DoD "No Smart
  product page routing remains" is satisfied at the source level. Two
  pre-existing contracts in `tests/test_canvas_entry.py` updated
  (`test_entry_compatibility_keeps_one_normal_entry_and_scopes_smart_handoff`
  → `..._with_no_handoff_surface`; `test_product_openers_confine_smart_page_urls_..._boundary`
  → `test_no_smart_product_page_routing_remains_in_static_js`); net test
  delta +0 (R4-35 strengthens/renames existing contracts rather than
  adding new redundant ones). Ownership matrix `Smart handoff` row
  retired. `./scripts/agent-verify.sh` PASS at 412 tests (unchanged).

- `R4-34` — `DONE` 2026-09-07T14:40+08:00. Card:
  `docs/tasks/active/R4-34-smart-native-canvas.md`. Implementer evidence
  (independent review pending): `canvas.html` is now the single entry that
  opens a historical Smart record natively, without redirecting to
  `smart-canvas.html`. `canvas.js` `openCanvas` no longer branches on kind
  (the `requiresLegacySmartHandoff` redirect is removed); `createCanvas`'s
  Smart branch navigates a freshly created Smart-kind record to `canvas.html`
  via the shared `WorkbenchCanvasEntryCompatibility.normalCanvasUrl(id, project)`
  helper (consistent with the list entry URL); with both call sites gone,
  `openSmartCanvasPage` is dead code and removed. `canvas.html` loads the
  two Smart-compatibility shared seams (`composer.js` + `media-tools.js`)
  ahead of `canvas.js`, so the unified page has the Composer shell lifecycle
  and media-edit geometry available for Smart node types. The Smart product
  runtime files stay on disk (out of scope: `R4-36` retires them); the
  `WorkbenchCanvasEntryCompatibility` handoff helpers stay exported (out of
  scope: `R4-35` retires the module). Two focused tests in
  `tests/test_frontend_workbench_modules.py` (vm-sandbox behavioral route +
  source-contract redirect removal / seam load order); two pre-existing
  contracts in `tests/test_canvas_entry.py` updated to pin the unified open
  contract. Ownership matrix `normal navigation` row updated to "one entry"
  and `Smart handoff` row annotated for the R4-35 retirement.
  `./scripts/agent-verify.sh` PASS at 412 tests (was 410; +2).

- `R4-33` — `DONE` 2026-09-07T12:41+08:00. Card:
  `docs/tasks/active/R4-33-classic-execution-compat.md`. Implementer evidence
  (independent review pending): characterization + narrow host seam. New
  `docs/plans/R4_CLASSIC_EXECUTION_COMPATIBILITY.md` characterizes the retained
  pre-R8 Classic execution path's Canvas-lifecycle/state ownership across 15
  entry points (seamed/host-cutover/host-candidate/flag-only + embedded JSON
  manifest). New `static/js/workbench/canvas/classic-execution-host.js` exposes
  `window.WorkbenchCanvasClassicExecutionHost.create(host)` (frozen validated
  handle: `markRunning`/`writeOutputText`/`setRunStatus`/`render`/`save`/
  `notifyError`; no ExecutorRegistry/ExecutionRuntime). Loaded ahead of
  `canvas.js`; Classic adds `ensureClassicExecutionHost()` and cuts over
  `runLLMNode` to route its Canvas lifecycle/state side-effects through the
  handle (old direct `node.running`/`node.outputText`/`node.runStatus`/
  `node.runError` writes + inline `refreshNodes`/`scheduleSave`/`alert`
  removed). `callCanvasLLM` and the cascade orchestrators stay host-candidates
  (characterized); transport stays page-side compatibility. Three focused tests
  (+3, 407→410). Ownership matrix `Classic-only` table gains an "LLM node
  execution" row. `./scripts/agent-verify.sh` PASS at 410 tests.

- `R4-32` — `DONE` 2026-09-07T12:55+08:00. Card:
  `docs/tasks/active/R4-32-classic-provider-compat.md`. Implementer evidence
  (independent review pending): the retained Classic provider-card controls no
  longer own Canvas lifecycle/state for the LLM provider body. New
  `static/js/workbench/canvas/provider-controls.js` exposes
  `window.WorkbenchCanvasProviderControls.create(host)` (frozen validated
  handle: `setField`/`save`/`render`; no R7 registry). Loaded ahead of
  `canvas.js`; Classic adds `ensureProviderControls()` and cuts over
  `renderLLMBody`'s five control handlers (provider/model/system/mode) to route
  Canvas side-effects through the handle, removing the old direct node writes +
  inline `render()`/`scheduleSave()`. Provider/model resolution + body
  presentation stay page-side; other provider bodies remain page-owned
  compatibility. Two focused tests (+2, 405→407). Ownership matrix
  `Classic-only` table gains a "Provider-card controls (LLM body)" row.
  `./scripts/agent-verify.sh` PASS at 407 tests.

- `R4-31` — `DONE` 2026-09-07T12:40+08:00. Card:
  `docs/tasks/active/R4-31-classic-inventory.md`. Implementer evidence
  (independent review pending): characterization-only card (no code changed).
  Deliverable `docs/plans/R4_CLASSIC_CAPABILITY_INVENTORY.md` inventories 13
  Classic-only, product-relevant capabilities across 9 categories (provider
  cards, Comfy, RunningHub, MiniMax, LTX, video, output/log, asset,
  cascade/execution), each marked KEEP/MIGRATE/COMPAT/REMOVE/DEFER-R8 with a
  target owner and source-line evidence (56 function names). Split: MIGRATE 4
  (provider node creation, Comfy result normalization, video node/player,
  output node/grid), COMPAT 8 (provider card bodies, Comfy/RunningHub/MiniMax/
  LTX controls, video params, generation log, cascade), DEFER-R8 1 (asset
  library/manager). Ownership matrix `Classic-only` review table references the
  full inventory. Anchoring `tests/test_classic_capability_inventory.py`
  (6 tests) parses the document's evidence manifest and verifies valid
  dispositions, non-empty owners, every evidence function grounded in
  `canvas.js`, In-Scope coverage, and non-trivial classification. No product
  code changed. `./scripts/agent-verify.sh` PASS at 405 tests (was 399; +6).

- `R4-30` — `DONE` 2026-09-07T12:30+08:00. Card:
  `docs/tasks/active/R4-30-smart-execution-compat.md`. Implementer evidence
  (independent review pending): characterization + narrow host seam. New
  `docs/plans/R4_SMART_EXECUTION_COMPATIBILITY.md` characterizes the retained
  pre-R8 execution path's Canvas-lifecycle/state ownership across eight entry
  points (dispositions seamed/host-cutover/host-candidate/transport-only/
  flag-only + embedded JSON manifest). New
  `static/js/workbench/canvas/execution-host.js` exposes
  `window.WorkbenchCanvasExecutionHost.create(host)` (frozen validated handle:
  `markRunning`/`writePromptResult`/`save`/`render`/`notifyError`; no
  ExecutorRegistry/ExecutionRuntime). Loaded ahead of `smart-canvas.js`; Smart
  constructs `executionHost` and cuts over `runPromptLLMNode` to route its
  Canvas lifecycle/state side-effects through the handle (old direct writes
  removed). Generation/cascade stay host-candidates (characterized); transport
  stays page-side compatibility. Three focused tests (+3, 396→399), one
  pre-existing contract updated. Ownership matrix `execution trigger` row
  updated. `./scripts/agent-verify.sh` PASS at 399 tests.

- `R4-29` — `DONE` 2026-09-07T12:05+08:00. Card:
  `docs/tasks/active/R4-29-smart-media-tools.md`. Implementer evidence
  (independent review pending): the retained Smart crop/draw/grid/resize tool
  geometry is now a mountable compatibility capability. New
  `static/js/workbench/canvas/media-tools.js` exposes
  `window.WorkbenchCanvasMediaTools` (a frozen namespace of pure, stateless
  functions): `clampResizeScale`, `circledNumber`, `canvasPoint`,
  `gridSplitRects`/`gridSplitRectsCustom`, `parseCropRatio`,
  `fitCropRectToAspect`. Loaded by `smart-canvas.html` ahead of
  `smart-canvas.js`; Smart delegates `clampImageResizeScale`, `circledNumber`,
  `editDrawPoint`, `gridSplitRects`/`gridSplitRectsCustom`,
  `cropRatioFromPreset` and `fitCropRectToAspect` to a `mediaTools` handle,
  keeping the editor modal, canvas 2D rendering, mode/state and node mutation
  page-side (out of scope: build the Media Package; panorama stays Smart-owned).
  The module is product-neutral (zero Smart leak) and the page no longer owns
  the raw geometry bodies. Two focused tests (vm-sandbox behavioral + load
  order/delegation/zero-leak contract). Ownership matrix gains a "Media edit
  tools" row. `./scripts/agent-verify.sh` PASS at 396 tests (was 394; +2).

- `R4-28` — `DONE` 2026-09-07T11:40+08:00. Card:
  `docs/tasks/active/R4-28-smart-composer.md`. Implementer evidence
  (independent review pending): the Smart Composer shell lifecycle is now a
  mountable compatibility capability instead of Smart-page-owned. New
  `static/js/workbench/canvas/composer.js` exposes
  `window.WorkbenchCanvasComposer.create({container})` returning a frozen
  lifecycle handle (`setOpen`/`isOpen`/`positionForRect`/`cancelPending`/
  `scheduleUpdate`); the module owns the floating card's container, open/close
  state, node-relative centering position math (default 540px width, 14px gap)
  and the sequence-guarded debounced update scheduler. Loaded by
  `static/smart-canvas.html` ahead of `smart-canvas.js`; Smart delegates its
  Composer head to a `composerLifecycle` handle (`positionComposerForNode` →
  `positionForRect(nodeRect(node))`, `scheduleComposerUpdate` →
  `scheduleUpdate(delay, updateComposer)`, `updateComposer` →
  `cancelPending()` before resolving the node); the four `composer.classList`
  open/close sites route through `setOpen`/`isOpen`; the old
  `composerUpdateTimer`/`composerUpdateSeq` page state is removed. Subject
  resolution and dynamic provider/media/prompt parameter rendering stay
  Smart-owned per "do not redesign Composer"; the module has zero Smart leak.
  Two focused tests in `tests/test_frontend_workbench_modules.py` (vm-sandbox
  behavioral position/open/debounce test + load-order/delegation/zero-leak
  contract). Ownership matrix `Composer` row updated.
  `./scripts/agent-verify.sh` PASS at 394 tests (was 392; +2).

- `R4-27` — `DONE` 2026-09-07T11:05+08:00. Card:
  `docs/tasks/active/R4-27-smart-inventory.md`. Implementer evidence
  (independent review pending): characterization-only card — classified every
  Smart-only, product-relevant capability before the Smart runtime is retired.
  Deliverable `docs/plans/R4_SMART_CAPABILITY_INVENTORY.md` inventories 31
  capabilities across 7 categories (Composer; prompt presets/templates/skills;
  asset UX; media edit/crop/draw/panorama; Smart group actions;
  cascade/execution; provider/media/MiniMax dynamic controls), each marked
  KEEP/MIGRATE/COMPAT/REMOVE/DEFER-R8 with a target owner and source-line
  evidence. Split: MIGRATE 18 (prompt registry/card, media edit, group actions,
  composer shell, video player, asset mention/drag), COMPAT 13 (execution /
  provider / media controls whose real replacement is R8), DEFER-R8 5
  (asset/collection runtime, forbidden in R4). Ownership matrix `Smart-only`
  review table references the full inventory. Anchoring
  `tests/test_smart_capability_inventory.py` (6 tests) parses the document's
  evidence manifest and verifies dispositions are valid, target owners present,
  every evidence function is grounded in `smart-canvas.js`, In-Scope coverage,
  and non-trivial classification. No product code changed.
  `./scripts/agent-verify.sh` PASS at 392 tests (was 386; +6).

- `R4-26` — `DONE` 2026-09-07T10:53+08:00. Card:
  `docs/tasks/active/R4-26-group-mutation.md`. Implementer evidence
  (independent review pending): group membership (the legacy `items` list on
  a `group` / `smart-group` node) now has one authoritative application
  mutation boundary. New `workbench/application/group_mutation.py`
  (`GroupMembershipService.set_membership` + `GroupMembershipCommand` /
  `GroupMembershipPersistence` / `GroupMembershipChangedAuditEvent`) validates
  fields, enforces `expected_revision >= 1`, rejects self-membership, checks
  `authorizer.can_edit`, then delegates to the repository and appends an audit
  event. `LegacyJsonGroupMembershipRepository.set_group_membership`
  (`workbench/repositories/legacy_json_node_repository.py`) mutates the legacy
  `items` list atomically under the canvas `mutate_if_current` lock. HTTP route
  `POST /api/v1/canvases/{canvas_id}/graph/group-membership` maps
  `GroupMutationError` → 403/422 and `StaleCanvasRevisionError` → 409.
  `WorkbenchNodeClient.setGroupMembership(canvasId, command, actorId)` is the
  single versioned client entry point. Smart
  `addSmartGroupMemberVersioned(groupId, memberId)` routes the drag-in single
  non-image/non-group member add through it with a `scheduleSave()` fallback;
  image absorption, group-merge and ungroup stay page-side compatibility, and
  Classic `updateGroupMembership` remains page-owned (no versioned path yet).
  Core is industry-neutral (zero `smart-loop` / `imageInput` / `showPrompt` /
  `syncLatestGeneratedOutput` / `inputNodeIds` in `group_mutation.py`). Tests:
  `tests/test_group_membership.py` (5 service + 4 repository), three HTTP-route
  tests in `tests/test_canvas_nodes_api.py`, and one wiring contract in
  `tests/test_frontend_workbench_modules.py`. Ownership matrix `group
  membership` row updated. `./scripts/agent-verify.sh` PASS at 386 tests
  (was 373; +13).

- `R4-25` — `DONE` 2026-09-07T09:45+08:00. Card:
  `docs/tasks/active/R4-25-legacy-graph-policy.md`. Implementer evidence
  (independent review: PASS 2026-09-07T09:52+08:00): the Classic / Smart historical connect
  side-effect RULES were duplicated as inline branches in the two page
  runtimes and now have a single named owner — new module
  `static/js/workbench/canvas/legacy-graph-compatibility.js` exposing
  `window.WorkbenchLegacyGraphCompatibility.create(...)` with
  `applyClassicConnect(...)` → `{groupAddMember, addedNodeIds,
  shouldSyncOutput, shouldSyncGeneratorInputs}` and
  `prepareSmartConnect(...)` → `{shouldConnect, loopTouched, flipImageInput,
  flipShowPrompt, fit, toImageInput, toShowPrompt, appendInputNodeId}`.
  Classic `applyClassicConnectionSideEffects` (`static/js/canvas.js`) and
  Smart `connectInputNodeVersioned` (`static/js/smart-canvas.js`) now ask
  the policy through lazy accessors and apply the returned projection; the
  module is loaded by `static/canvas.html` and `static/smart-canvas.html`
  ahead of the editor script. `workbench/application/graph_mutation.py` is
  untouched and stays industry-neutral (zero `smart-loop` / `imageInput` /
  `showPrompt` / `syncLatestGeneratedOutput` / `group.items` /
  `inputNodeIds` references). Historical quirks preserved rather than
  "cleaned up": Classic output/generator syncs stay unconditional; Smart
  `loopTouched` follows `looksImage || looksPrompt` and not the flips;
  Smart `canImage`/`canPrompt` are evaluated after the flips. Three focused
  tests added to `tests/test_frontend_workbench_modules.py`:
  `test_legacy_graph_compatibility_policy_owns_connect_side_effects`
  (single owner, both helpers delegate, no adapter rule literal survives,
  Core zero leak),
  `test_legacy_graph_compatibility_policy_matches_classic_smart_history`
  (behavioral — real policy in a vm sandbox over representative node
  pairs) and
  `test_classic_connect_side_effects_apply_the_policy_projection`
  (behavioral — the REAL page function with page-shaped mocks: membership
  added once, idempotent, command-gate suppressed, both syncs per commit).
  R4-24's end-to-end test now also loads the real policy into its Smart
  sandbox. Three pre-existing contracts that pinned the old inline forms
  were updated to pin the new owner. Ownership matrix `connection
  mutation` row updated: final owner is `GraphMutationService`
  connect-nodes plus `legacy-graph-compatibility.js` for the side-effect
  rules. `./scripts/agent-verify.sh` PASS at 373 tests (was 370; +3 from
  this card).

- `R4-24` — `DONE` 2026-09-07T09:02+08:00. Card:
  `docs/tasks/active/R4-24-connect-command.md`. Implementer evidence
  (independent review: PASS 2026-09-07T09:52+08:00): the connect drop on both pages now
  creates the durable edge atomically with revision CAS through the
  application boundary — `GraphMutationService.connect_nodes` (backend
  service in `workbench/application/graph_mutation.py`) with
  `ConnectNodesCommand` / `ConnectNodesPersistence` /
  `NodesConnectedAuditEvent`; HTTP route
  `POST /api/v1/canvases/{canvas_id}/graph/connect-nodes` maps
  `GraphMutationError` → 403/422 and `StaleCanvasRevisionError` → 409;
  `WorkbenchNodeClient.connectNodes(canvasId, command, actorId)` is the
  single versioned client entry point gating on `requirePositiveRevision`;
  Legacy JSON repository implements `connect_nodes`; page-side
  `createVersionedConnection` (Classic) and `connectInputNodeVersioned`
  (Smart) route the connect drop through the new client method; the
  retained `commitClassicConnection` / `connectInputNode` legacy helpers
  stay as bounded fallback only. New behavioral test added to
  `tests/test_frontend_workbench_modules.py`:
  `test_versioned_connect_drops_land_at_the_application_command` —
  end-to-end vm-sandbox proof that the actual page-side helpers land at
  the versioned client with the right canvas id / project / expected
  revision / edge id / kind and the projected edge appears in
  `connections` / `canvas.connections` / target `inputNodeIds`. Combined
  with the foundation tests (`test_registered_graph_route_connects_two_existing_nodes_atomically`,
  `test_registered_graph_route_connects_smart_nodes_with_input_sync`,
  `test_connect_drops_route_through_the_graph_connect_command`) the DoD
  "atomic and revision-safe" is verified at four layers. Ownership matrix
  deferred-migration assessment for the connect drop already marked
  "Resolved for the drop path (2026-09-07, card R4-24)" — no further
  ownership move on this card. The remaining shared `connectInputNode`
  callers (auto-connect on drag, output flows, loop migration) stay
  deferred per the matrix and become the explicit scope of `R4-25`.
  `./scripts/agent-verify.sh` PASS at 370 tests (was 369; +1 from this
  card's new behavioral test).

- `R4-21.1` — `DONE` 2026-09-07T08:55+08:00. Card:
  `docs/tasks/active/R4-21.1-create-canvas-id-rectification.md`. Implementer
  evidence (independent review: PASS 2026-09-07T09:52+08:00): all ten R4-21 blank-create helpers
  (5 Classic in `static/js/canvas.js` — image L2525, prompt L2572, loop
  L2596, group L2647, output L2670; 5 Smart in `static/js/smart-canvas.js` —
  smart-prompt L1717, smart-loop L1736, smart-group L1755, smart-minimax
  L1777, smart-image L1923) now propagate `canvasId: canvas.id` into
  `CreationController.createNode({ ... })`; file-drop, clipboard and connected
  helpers were already correct and not touched. Two focused tests added to
  `tests/test_frontend_workbench_modules.py`:
  `test_blank_create_entry_points_propagate_canvas_id` (string-pin source
  contract mirroring the R4-23 clipboard pattern) and
  `test_blank_create_helpers_pass_canvas_id_to_controller_at_runtime`
  (behavioral — drives the real `createCreationController` factory with
  page-shaped mocks and verifies each `create(canvasId, ...)` lands with the
  page's `canvas.id` and every helper returns the projected node, not the
  `CreationController requires canvasId` TypeError). Pre-existing R4-21
  canvasId finding closed; ownership matrix unchanged (no move, no duplicate
  owner to remove). `./scripts/agent-verify.sh` PASS at 369 tests (was 367
  baseline; +2 from this card's new tests).

- `R4-23` — `DONE` 2026-09-07T07:35+08:00. Card:
  `docs/tasks/active/R4-23-clipboard.md`. Implementer evidence (independent
  review: PASS 2026-09-07T09:52+08:00; the card's earlier `Status: BACKLOG`
  / `backlog/` location was bookkeeping drift, corrected): single-node,
  connection-free clipboard paste of the
  losslessly persistable Legacy shapes (Classic image/prompt, Smart
  smart-prompt) now creates through `CreationController` +
  `NodeCreationService` with the explicit `clipboard` provenance source (new
  `NodeCreationSource.CLIPBOARD`); placement still comes from the shared
  center-anchored materialization; the versioned path adds revision CAS
  adoption and undo/selection projection and drops the raw append/save.
  Multi-node fragments, connections, groups, smart-image scale, non-default
  loops, content outputs, Alt-drag duplicate, target-node fill and asset-inbox
  paste remain adapter-owned compatibility (recorded). HTTP route test proves
  clipboard-sourced persistence/reload across legacy record types; wiring
  contract pins candidate gates, one `clipboard` source per adapter, canvasId
  propagation and the retained fragment fallback; envelope sandbox extended;
  regression 360 tests PASS.

- `R4-22` — `DONE` (card: `docs/tasks/active/R4-22-file-drop.md`;
  independent review: PASS 2026-09-07T09:52+08:00). Top-level
  supported file drops route created media nodes through the
  `CreationController`/`NodeCreationService` with the `file_drop` provenance
  source; target fill and group/media layout remain compatibility-owned;
  regression 358 tests PASS.

- `R4-21` — `DONE` 2026-09-07T06:12+08:00. Card:
  `docs/tasks/done/R4-21-creation-controller.md`. Independent review (2026-09-07):
  code DoD verified; verdict CHANGES_REQUIRED on review integrity — the tree
  contained implementer-written "Independent review: PASS" claims and a
  premature R4-22 activation before any independent review had occurred; both
  blockers rectified the same day and re-checked by the reviewer: PASS.
  Evidence:
  `createCreationController` owns the versioned command envelope; all ten
  blank-create entry points (both pages) route through controller singletons;
  zero direct client create calls for blank entries; inventory of remaining
  raw paths recorded; behavioral + wiring contract tests; regression 358
  tests PASS.

- `R4-20` — `DONE` 2026-09-07T00:15+08:00. Card:
  `docs/tasks/done/R4-20-connection-interaction.md`. Independent review: PASS. Evidence:
  `createConnectionGestureController` owns the port-drag gesture lifecycle
  (hover pipeline, drop/no-target/finish dispatch, cancel); Classic startLink
  and Smart port drag migrated, Smart dispatcher branches removed; controller
  has no persistence surface (pinned); behavioral + wiring contract tests;
  regression 356 tests PASS.

- `R4-19` — `DONE` 2026-09-06T23:58+08:00. Card:
  `docs/tasks/done/R4-19-keyboard-runtime.md`. Independent review: PASS. Evidence:
  `createKeyboardRuntime` owns the window keyboard listener pair (one per
  adapter) with ordered dispatch and short-circuit; Classic main
  keydown/keyup and Smart main keydown register with it; direct listener
  blocks removed; undo/redo and shortcut handlers unchanged; behavioral +
  wiring contract tests; regression 354 tests PASS.

- `R4-18` — `DONE` 2026-09-06T23:43+08:00. Card:
  `docs/tasks/done/R4-18-drag-resize.md`. Independent review: PASS. Evidence: drag/resize session
  factories on the InteractionController own session construction over the
  kernel; all five page session-creation sites (Classic drag/resize, Smart
  drag/thumb-drag/resize) cut over; behavioral + wiring contract tests;
  regression 352 tests PASS.

- `R4-17` — `DONE` 2026-09-06T23:29+08:00. Card:
  `docs/tasks/done/R4-17-minimap-cutover.md`. Independent review: PASS. Evidence:
  `createMinimapController` owns the minimap drag interaction (gated capture,
  project/apply callbacks, detach-on-mouseup); direct window-slot assignment
  removed; 100/300-node projection characterization test; regression 350
  tests PASS.

- `R4-16` — `DONE` 2026-09-06T23:18+08:00. Card:
  `docs/tasks/done/R4-16-viewport-cutover.md`. Independent review: PASS. Evidence:
  `createViewportController` owns viewport mutation dispatch over the
  runtime-state kernel; Classic board-pan session via InteractionController,
  wheel zoom + fit/restore/handoff/centering via the controller; duplicate
  page dispatch helper removed; behavioral + wiring contract tests; regression
  347 tests PASS.

- `R4-15` — `DONE` 2026-09-06T22:55+08:00. Card:
  `docs/tasks/done/R4-15-selection-cutover.md`. Independent review: PASS. Evidence:
  `createSelectionStore` selection authority on the interaction-controller
  module; Classic selection fully cut over (five direct reassignments and all
  mutations through the store); Smart dual-variable model deferred as a
  dedicated unit; behavioral + wiring contract tests; regression 345 tests
  PASS.

- `R4-14` — `DONE` 2026-09-06T22:23+08:00. Card:
  `docs/tasks/done/R4-14-interaction-controller.md`. Independent review: PASS (browser drag/resize smoke recorded). Evidence:
  `WorkbenchInteractionController` owns the pointer-session lifecycle
  (begin/move dispatch/mouseup end/programmatic end with supersede-on-begin
  semantics); Classic node-drag and node-resize sessions migrated, direct
  window assignments removed; behavioral + wiring contract tests; regression
  343 tests PASS.

- `R4-13` — `DONE` 2026-09-06T21:54+08:00. Card:
  `docs/tasks/done/R4-13-provider-compat-renderers.md`. Independent review: PASS. Evidence:
  `provider-compat` renderer (priority 5) adopts provider-shaped Classic bodies
  and carries per-card cleanup through the mounted-handle lifecycle; LTX
  teardown moved behind the runtime unmount boundary; both delete flows unmount
  through the runtime; behavioral + wiring contract tests; regression 341
  tests PASS.

- `R4-12` — `DONE` 2026-09-06T21:28+08:00. Card:
  `docs/tasks/done/R4-12-generic-rendering.md`. Evidence: Classic prompt
  family cut over to registry-owned rendering (`prompt-card` renderer builds
  the card DOM inside NodeShell; page state behind rendererOptions callbacks;
  flags-off fallback preserved); behavioral pipeline + wiring contract tests;
  regression 339 tests PASS.

- `R4-11` — `DONE` 2026-09-06T21:05+08:00. Card:
  `docs/tasks/done/R4-11-media-rendering.md`. Evidence: runtime-owned
  media-state projection (`mediaState` capture on unmount / restore on mount),
  MediaRenderer elements carry the signature URL, page sweeps exclude
  shell-mounted cards; behavioral tests for all three; regression 337 tests
  PASS.

- `R4-10` — `DONE` 2026-09-06T20:25+08:00. Card:
  `docs/tasks/done/R4-10-group-rendering.md`. Evidence:
  `WorkbenchRenderRuntime.mountGroupCard` owns the Group mount contract
  (record assembly, media/legacy decision with `mediaEnabled:false` rollback,
  lifecycle, resolved shell view, empty-state hook); Classic group branch and
  Smart group batch delegate; behavioral + cutover contract tests; regression
  334 tests PASS.

- `R4-09` — `DONE` 2026-09-06T19:33+08:00. Card:
  `docs/tasks/done/R4-09-render-runtime.md`. Evidence:
  `WorkbenchRenderRuntime` owns the mounted-card lifecycle (keyed registry,
  ordered destroy on remount/unmount, batch mounting, canvas-load reset); both
  adapters inject the host mount once and route all five adoption mounts +
  delete flows through it; behavioral + wiring contract tests; regression 332
  tests PASS.

- `R4-08` — `DONE` 2026-09-06T19:20+08:00. Card:
  `docs/tasks/done/R4-08-render-ownership-map.md`. Evidence: rendering
  ownership map in `docs/plans/R4_OWNERSHIP_MATRIX.md` (per-family
  create/update/destroy/listener/media-state owners with file:line evidence,
  six adoption paths, next migration unit = mounted-card lifecycle); anchored
  by a source-contract test; regression 330 tests PASS.

- `R4-07` — `DONE` 2026-09-06T19:00+08:00. Card:
  `docs/tasks/done/R4-07-remote-sync-revision.md`. Evidence: canonical meta
  probe + revision-bearing canvas_updated broadcast; remote-sync coordinator
  and update-message filter order by revision (timestamp fallback); adapters
  feed revisionOf() baselines; regression 329 tests PASS. Ownership matrix
  remote/version-polling row updated.

- `R4-06` — `DONE` 2026-09-06T18:40+08:00. Card:
  `docs/tasks/done/R4-06-browser-logical-revision.md`. Evidence: shared
  persistence client owns the logical-revision cursor and sends canonical CAS
  saves (`expected_revision`); sandbox tests prove load→save→conflict→recovery
  cursor chain and 503/legacy fallbacks; HTTP round-trip test proves CAS
  recovery; regression 323 tests PASS. Ownership matrix revision/CAS row
  updated.

- `R4-05` — `DONE` 2026-09-06T18:22+08:00. Card:
  `docs/tasks/done/R4-05-canonical-canvas-api.md`. Evidence: canonical
  transport `/api/v1/canvases/{canvas_id}` GET (revision/updated_at) + PUT
  (expected_revision CAS, explicit 409 conflict info, 503 without SQLite
  authority) in `workbench/api/canvases.py`; legacy transport shape pinned;
  regression 319 tests PASS. Ownership matrix revision/CAS row updated.

- `R4-04` — `DONE` 2026-09-06T18:10+08:00. Card:
  `docs/tasks/done/R4-04-split-brain-regression.md`. Evidence:
  `tests/test_split_brain_regression.py` — 5 incident-scenario tests (normal
  SQLite routing, refused disabled flag, legacy migration/read/write while
  inactive, restart-durable authority, one-store write isolation); regression
  313 tests PASS.

- `R4-03` — `DONE` 2026-09-06T17:59+08:00. Card:
  `docs/tasks/done/R4-03-split-brain-guard.md`. Evidence: explicit authority
  policy seam (`canvas_authority_policy.py`) + three-layer startup guard; live
  refusal of `WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED=false` under
  `authority_state=sqlite` with exit 1 and byte-identical database
  (sha256 `3cca0054…`); recovery paths verified available; regression 308
  tests PASS. Ownership matrix Canvas-persistence row updated.

- `R4-02` — `DONE` 2026-09-06T17:37+08:00. Card:
  `docs/tasks/done/R4-02-sqlite-legacy-reconcile.md`. Evidence: read-only
  reconciliation of `data/canvases` (23 files) vs `data/workbench.sqlite3`
  (23 rows, 17 active) — 0 legacy-only, 0 sqlite-only, 23/23 payload
  comparisons matched, 0 unexpected rows, authority `sqlite`, database
  byte-identical (sha256 `3cca0054…`) before/after; regression 297 tests PASS.
  Report: `data/r4-canvas-reconciliation-report.json`.

- `R4-01` — `DONE` 2026-09-06T17:07+08:00. Card archived at
  `docs/tasks/done/R4-01-local-truth.md`. Evidence: verified HEAD
  `f764ce134e9496ba753fcb60943a0bbbbc2c2558` on `main`; baseline 294 tests PASS;
  `./scripts/agent-verify.sh` PASS; recorded in
  `docs/status/CURRENT_EXECUTION_STATUS.md`.

## Required Reads

1. `AGENTS.md`
2. `.agent/AGENT_CONTRACT.md`
3. `docs/status/CURRENT_EXECUTION_STATUS.md`
4. `docs/tasks/active/R4-11-media-rendering.md`

Read architecture documents only as required by the card.

## Execution Rule

Execute **exactly this one card**.

Do not start the next task.

## Completion Rule

After implementation / verification:

1. update current status evidence;
2. update ownership matrix only if ownership changed;
3. set this card status to `DONE` only when its DoD is actually satisfied;
4. write the recommended next card here, but do **not** execute it;
5. stop.

## Recommended Successor

Expected successor after R4-37 close (not activated, not executed):

`R4-38 — Reduce canvas.js to Bootstrap/Compatibility Only` (`docs/tasks/backlog/R4-38-shrink-classic-runtime.md`)

Actual successor must still be checked against the repository's current verified state.
