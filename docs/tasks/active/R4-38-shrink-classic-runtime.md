# CARD R4-38 — Reduce canvas.js to Bootstrap/Compatibility Only

- Round: R4
- Priority: P0
- Status: IN_PROGRESS (umbrella shrink card; multi-wave; closes only when canvas.js is bootstrap/compat-only)
- Activated: 2026-09-07T15:30+08:00
- Wave 1 done: 2026-09-07T15:33+08:00
- Wave 2 done: 2026-09-07T15:55+08:00
- Wave 3 done: 2026-09-07T16:05+08:00
- Wave 4 done: 2026-09-07T16:13+08:00
- Wave 5 done: 2026-09-07T16:30+08:00
- Wave 6 done: 2026-09-07T16:52+08:00
- Closed: (not yet — 8 of 15 Classic capabilities still need shrink waves;
  inventory grew from 13 → 14 (Wave 3) → 15 (Wave 4) as video-player and
  output-node were split into factory-half MIGRATE + body-half COMPAT.
  4 MIGRATE rows are 100% done (Waves 1-4); Wave 5 closed provider-card-body
  COMPAT; Wave 6 closed comfy-controls COMPAT; 8 COMPAT rows + 1 DEFER-R8
  remain across Waves 7-15, plus Wave 16 (shrink-to-bootstrap) closes the
  card.)
- Depends on: R4-37

## Goal

Remove Canvas runtime ownership from the Classic monolith. The full
shrink decomposes into a sequence of focused migration waves (one
MIGRATE / MIGRATED capability per wave), each committed on top of the
last. The card closes once canvas.js is bootstrap/compat-only and is
ready for the eventual R4-39 deletion.

## Before Owner

canvas.js

## After Owner

Unified runtimes / bounded compatibility seams (per wave).

## Wave plan

The 15 Classic capabilities from the current R4-31 inventory (post
R4-38 Wave 3 + Wave 4 splits: `video-player` and `output-node` each
split into a MIGRATE/COMPAT pair) partition into the following shrink
waves. Each wave is one focused commit (+0..1 new tests per focused
contract change). The card stays open across all waves and closes once
every wave is DONE.

| Wave | Capability | Disposition | Action |
|---|---|---|---|
| **1 (done)** | comfy-result-normalization | MIGRATED | inline `resultMediaUrls` / `comfyResultOutputs` call sites through `media-result-normalizer.js`; delete the two wrapper function definitions in canvas.js. |
| **2 (done)** | provider-node-creation (addGeneratorNode / addMidjourneyNode / addMsGenNode) | MIGRATED | new host seam `static/js/workbench/canvas/classic-node-factories.js` (`window.WorkbenchCanvasClassicNodeFactories.create(host)` returns frozen `{addGenerator, addMidjourney, addMsGen}`); canvas.js deletes the local `function addGeneratorNode / addMidjourneyNode / addMsGenNode` definitions and re-routes its `createNodeByType` dispatcher through `ensureClassicNodeFactories().addXxx({point})`. |
| **3 (done)** | video-node-creation (addVideoNode factory half) | MIGRATED | extend `classic-node-factories.js` with 4 new required host ops (`videoApiProviders` / `providerVideoModels` / `videoModels` / `defaultVideoModels`) and the `addVideo({point})` method; canvas.js deletes `function addVideoNode` and re-routes the `'video'` dispatch through `ensureClassicNodeFactories().addVideo({point})`. R4-31 inventory's `video-player` row split into `video-node-creation` (MIGRATED) + `video-card-body` (COMPAT, R8; `renderVideoBody` stays page-side as a provider card body — same disposition as `provider-card-body`). |
| **4 (done)** | output-node-creation (addOutputNode factory half) | MIGRATED | extend `classic-node-factories.js` with a new `addOutput({point})` method (no new REQUIRED ops needed — `addOutputNode` only used `addNode` / `uid` / `defaultPoint`); canvas.js deletes `function addOutputNode` (3-line factory) and re-routes the `'output'` dispatch through `ensureClassicNodeFactories().addOutput({point})`. R4-31 inventory's `output-node` row split into `output-node-creation` (MIGRATED) + `output-grid-renderer` (COMPAT, target = Unified media renderer / render runtime; evidence = `refreshOutputNodeContent` / `renderOutputGrid` / `bindOutputWrap`, ~250 LOC of grid+media lifecycle that stays page-side per the inventory evidence and the COMPAT/R8 boundary). Inventory test `test_classification_is_meaningful_across_dispositions` loosened to allow MIGRATE=0 + MIGRATED≥1 as a healthy terminal state (R4-38 has wound down all four MIGRATE rows). |
| 5 | provider-card-body (renderLLMBody + renderGeneratorBody + renderMidjourneyBody + renderMsGenBody) | COMPAT | bounded compat seam module `static/js/workbench/canvas/classic-card-body-renderer.js` (`window.WorkbenchCanvasClassicCardBodyRenderer.create({host})` returns frozen `{renderLLM({node, container}), renderGenerator({node, container}), renderMidjourney({node, container}), renderMsGen({node, container})}`); canvas.js deletes the four `function renderXxxBody(...)` body definitions (each constructs `<div>` + provider/model dropdowns + ratio/resolution options + per-provider parameter controls) and re-routes every provider-card-body render site through the seam's renderer. The five control handlers inside `renderLLMBody` (provider select / model select / system toggle / system prompt / mode buttons) are already routed through R4-32's `provider-controls.js` seam, so the seam's `renderLLM` only owns the *static body construction* — the dynamic control handlers stay with `provider-controls.js`. |
| 6 | Comfy workflow/field controls (addComfyNode + renderComfyBody + renderComfySettings + updateComfyField + comfyWorkflowOptions) | COMPAT | bounded compat seam module `static/js/workbench/canvas/classic-comfy-controls.js` (frozen `{renderBody({node, container}), updateField({node, field, value}), getWorkflowOptions()}`); canvas.js deletes the five local function definitions and re-routes. |
| 7 | RunningHub workflow/params (addRhNode + renderRhBody + renderRhParams + runningHubProvider + currentRunningHubWorkflow + currentRunningHubWorkflowConfig) | COMPAT | bounded compat seam module `static/js/workbench/canvas/classic-runninghub-controls.js` (frozen `{renderBody, renderParams, getCurrentWorkflow, getCurrentWorkflowConfig, getProviderId}`); canvas.js deletes the six local definitions and re-routes. |
| 8 | MiniMax timeline/player/generation (addMiniMaxNode + renderMiniMaxBody + bindMiniMaxWorkbench + miniMaxEngine + miniMaxPlayerHtml + miniMaxSyncPlayerDom) | COMPAT | bounded compat seam module `static/js/workbench/canvas/classic-minimax-controls.js` (frozen `{renderBody, bindWorkbench, getEngine, buildPlayerHtml, syncPlayerDom}`); canvas.js deletes the six local definitions and re-routes. |
| 9 | LTX director timeline/relay (addLTXDirectorNode + renderLTXDirectorBody + destroyLTXEditor + ltxParseTimeline + ltxFlushTimelineToNode + ltxBuildContiguousRelay) | COMPAT | bounded compat seam module `static/js/workbench/canvas/classic-ltx-controls.js` (frozen `{renderBody, destroyEditor, parseTimeline, flushTimelineToNode, buildContiguousRelay}`); canvas.js deletes the six local definitions and re-routes. |
| 10 | video-card-body (renderVideoBody, split from R4-38 Wave 3 `video-player` row) | COMPAT | bounded compat seam module `static/js/workbench/canvas/classic-video-body.js` (frozen `{render({node, container})}`); canvas.js deletes `function renderVideoBody(...)` and re-routes the video-card render call. |
| 11 | video-provider/params (videoApiProviders + resolveVideoProviderId + providerVideoModels + renderVideoImageInputs) | COMPAT | bounded compat seam module `static/js/workbench/canvas/classic-video-providers.js` (frozen `{getApiProviders, resolveProviderId, getProviderModels, renderImageInputs({node, container})}`); canvas.js deletes the four local definitions and re-routes. Note: `videoApiProviders` + `providerVideoModels` are already host-injected into `classic-node-factories.js` from Wave 3 (REQUIRED host ops for the `addVideo` factory); the Wave 11 seam module is the *page-side resolver layer* (resolves the provider id + populates the provider/model dropdown + renders image inputs), not the *node-factory host ops*. |
| 12 | output-grid-renderer (refreshOutputNodeContent + renderOutputGrid + bindOutputWrap, split from R4-38 Wave 4 `output-node` row) | COMPAT | bounded compat seam module `static/js/workbench/canvas/classic-output-grid.js` (frozen `{refreshNodeContent({node, container}), renderGrid({node, container}), bindWrap({node, wrap})}`); canvas.js deletes the three local definitions and re-routes. |
| 13 | generation-log (addGenerationLog + renderCanvasLog) | COMPAT | bounded compat seam module `static/js/workbench/canvas/classic-generation-log.js` (frozen `{addLog({entry}), renderPanel({container})}`); canvas.js deletes the two local definitions and re-routes. |
| 14 | cascade-orchestrator (beginCascade + computeCascadeOrder + resolveCascadeLoop + bindCascadeButtons + runCascadeNodeByType + requestCascadeStop + finalizeCascade) | COMPAT | bounded compat seam module `static/js/workbench/canvas/classic-cascade-orchestrator.js` (frozen `{begin({canvas, startNodeId}), computeOrder({canvas, startNodeId}), resolveLoop({canvas}), bindButtons({container, canvas}), runNodeByType({canvas, nodeId, type}), requestStop(), finalize({canvas, results})}`); canvas.js deletes the seven local definitions and re-routes. Note: `callCanvasLLM` (transport) + `runNodeCascade` (entry) stay page-side as bounded compat transports (R4-33 already characterized). |
| 15 | asset-library / manager (revealCanvasAssetControls + renderCanvasAssetLibrary + toggleCanvasAssetLibrary + openAssetManager + renderAssetManager + mediaKindForUpload) | DEFER-R8 | out of R4 scope (Asset/Collection runtime forbidden in R4 per CURRENT_EXECUTION_STATUS.md "Forbidden next actions"). Bounded compat stays page-side; no R4 work besides confirming the DEFER-R8 marker is still valid. |
| 16 (final) | shrink-to-bootstrap | — | after waves 1–15, the remaining ~15 kloc in canvas.js becomes a small compat shell: imageApiProviders / videoApiProviders / provider resolvers, save scheduler wiring, the few DOM event handlers that touch page-specific UI, and the canvas-bootstrap sequence. Wave 16 sizes the residual canvas.js and tightens the bootstrap-only contract. After Wave 16, R4-38 closes and R4-39 (Remove Legacy canvas.js) can run. |

## In Scope

- Each wave: remove runtime ownership for its named capability; keep
  bounded compatibility in canvas.js where R4 inventory says COMPAT.
- Maintain the `MIGRATED` evidence-chain with the existing inventory tests
  in `tests/test_classic_capability_inventory.py` (post-migration
  evidence is the seam-call string still present in canvas.js so the
  `assertIn(name, canvas.js_source)` contract holds without schema
  change).
- Update the AGENT_NEXT_TASK / CURRENT_EXECUTION_STATUS.md evidence
  section after each wave.
- A focused source-contract test per wave (or per pair-of-waves when
  the seam already covers the contract).

## Out of Scope

- Do not let Classic 'win' as final runtime.
- Do not migrate COMPAT capabilities into a new R4 runtime owner
  (their real replacement is R8 per the R4-31 inventory).
- Do not delete canvas.js itself — that is R4-39.
- Do not silently rebind canvas.js event handlers to unified seams
  without an explicit migration wave plan (each handler rebinding
  needs its own focused change).

## Definition of Done

- [x] Wave 1: comfy-result-normalization MIGRATED, wrappers
      `comfyResultOutputs` / `resultMediaUrls` deleted from canvas.js,
      focused test
      `test_classic_editor_inlines_execution_result_extraction_through_the_shared_seam`
      in place.
- [x] Wave 2: provider-node-creation MIGRATED. New host seam
      `static/js/workbench/canvas/classic-node-factories.js`
      (`WorkbenchCanvasClassicNodeFactories.create({addNode, uid,
      defaultPoint, imageApiProviders, allImageModels,
      defaultApiImageResolution, resolveMidjourneyProviderId,
      modelscopeImageModels})` returns frozen handle
      `{addGenerator, addMidjourney, addMsGen}`; canvas.js deletes the
      three local factory function definitions and re-routes its
      `createNodeByType` dispatcher through
      `ensureClassicNodeFactories().addXxx({point})`; canvas.html
      loads the seam before canvas.js; focused test
      `test_classic_editor_routes_provider_node_creation_through_classic_node_factories_seam`
      pins source-contract + behavioral drive + missing-host-op throws
      TypeError.
- [x] Wave 3: video-node-creation MIGRATED. `classic-node-factories.js`
      extended with 4 new required host ops + `addVideo({point})` method
      (model fallback chain `providerVideoModels(providerId)[0] ||
      videoModels()[0] || defaultVideoModels()[0]`, 11 typed fields,
      point helper default). canvas.js deletes `function addVideoNode`
      and re-routes the `'video'` dispatch through the seam. R4-31
      inventory's `video-player` row split into `video-node-creation`
      (MIGRATED, evidence = `addVideo(` in the seam module) +
      `video-card-body` (COMPAT, evidence = `renderVideoBody` in
      canvas.js, R8 owns the real replacement). Focused test
      `test_classic_editor_routes_video_node_creation_through_classic_node_factories_seam`
      — drives the seam's new addVideo, asserts the exact record shape,
      and source-contracts the canvas.js wrapper-deletion + dispatcher
      seam-call + host injection of the 4 new ops including
      `defaultVideoModels: () => DEFAULT_VIDEO_MODELS`. Wave 2's test
      updated to also exercise the 4 new REQUIRED host ops in the
      missing-host-op loop so the seam's REQUIRED validation stays
      strictly tested across all 12 host ops.
- [x] Wave 4: output-node-creation MIGRATED. `classic-node-factories.js`
      extended with a new `addOutput({point})` method (no new REQUIRED
      ops — `addOutputNode` only used `addNode` / `uid` /
      `defaultPoint`). canvas.js deletes `function addOutputNode` (3
      lines; trivial factory body: `{id:uid('out'), type:'output',
      x:p.x, y:p.y, images:[]}`) and re-routes the `'output'`
      dispatch through the seam. R4-31 inventory's `output-node` row
      split into `output-node-creation` (MIGRATED, evidence =
      `addOutput(` in the seam module) + `output-grid-renderer`
      (COMPAT, evidence = `refreshOutputNodeContent` /
      `renderOutputGrid` / `bindOutputWrap` in canvas.js; ~250 LOC
      of grid + media lifecycle that stays page-side per the COMPAT /
      R8 boundary). Focused test
      `test_classic_editor_routes_output_node_creation_through_classic_node_factories_seam`
      — drives `addOutput` with all 12 REQUIRED ops in mock host,
      asserts the exact `(type:'output', id:'out-test', x:444, y:555,
      images:[])` record, source-contracts the canvas.js
      wrapper-deletion + dispatcher seam-call. Inventory test
      `test_classification_is_meaningful_across_dispositions`
      loosened: required invariants are now COMPAT + DEFER-R8 (the
      R4-wide + R8-governance foundations); MIGRATE is optional (all
      four MIGRATE rows were promoted over Waves 1-4); when MIGRATE is
      present, MIGRATED must also be present (forward-driving).
- [ ] Wave 5: provider-card-body COMPAT seam (batches
      `renderLLMBody` + `renderGeneratorBody` + `renderMidjourneyBody` +
      `renderMsGenBody` as bounded compat per R4-31 — R8 owns the real
      executor-driven body rendering).
- [x] Wave 5: provider-card-body COMPAT seam done. New bounded compat
      seam `static/js/workbench/canvas/classic-card-body-renderer.js`
      (`window.WorkbenchCanvasClassicCardBodyRenderer.create(host)`
      returns frozen `{renderLLM({node}), renderGenerator({node}),
      renderMidjourney({node}), renderMsGen({node})}`); canvas.js
      deletes the four local body function definitions
      (renderLLMBody / renderGeneratorBody / renderMidjourneyBody /
      renderMsGenBody, ~904 LOC of body construction); canvas.js
      `createNodeByType` dispatcher routes the four kind branches
      through `ensureClassicCardBodyRenderer().renderXxx({node})`.
      The seam module owns the four function bodies (each receives
      node by reference and reads/mutates node state in place, same
      as the page-side originals); page injects the 49 REQUIRED host
      ops (escapeHtml / tr / provider + model resolvers / image
      helpers / MsGen catalog / renderImageInputList / renderPrompt
      Preview / cascadeBtnHtml / retryBarHtml / bindCascadeButtons /
      scheduleSave / render / runCanvasGenerate / ensureProviderControls,
      etc.) so all page-local knowledge stays on the page per the
      COMPAT/R8 boundary. Focused test
      `test_classic_editor_routes_provider_card_body_through_classic_card_body_renderer_seam`
      drives all four render methods in a vm sandbox with a stub
      document and asserts each runs without throwing, exercises the
      full 49-op missing-host-op TypeError loop, source-contracts the
      four wrapper-deletions + dispatcher seam-call shapes. Pre-existing
      `test_provider_controls_is_loaded_before_the_classic_page_and_llm_body_uses_it`
      updated: the five `providerControls.setField(...)` assertions now
      target the card-body seam module (where renderLLMBody lives since
      Wave 5), the canvas.html load-order assertion also pins the
      provider-controls → card-body → canvas.js dependency order, and
      the `ensureProviderControls` host-injection assertion stays on
      canvas.js (the page owns the host, the seam consumes it).
- [x] Wave 6: comfy-controls COMPAT seam done. New bounded compat
      seam `static/js/workbench/canvas/classic-comfy-controls.js`
      (`window.WorkbenchCanvasClassicComfyControls.create(host)` returns
      frozen `{addNode({point}), renderBody({node}), renderSettings
      ({container, node}), updateField({node, input, event}),
      getWorkflowOptions({selected})}`); canvas.js deletes the five
      local Comfy function definitions (addComfyNode / comfyWorkflow
      Options / renderComfyBody / renderComfySettings / updateComfyField,
      ~222 LOC of body + settings + field construction); canvas.js
      `createNodeByType` routes `'comfy'` through
      `ensureClassicComfyControls().addNode({point})`; body dispatcher
      routes `node.type === 'comfy'` through `comfy.renderBody({node})`
      (alongside the Wave 5 `cardBody.renderXxx({node})` pattern).
      The seam module owns the five function bodies; page injects the
      29 REQUIRED host ops (document / escapeHtml / tr / addNode / uid /
      defaultPoint / allImageModels / imageApiProviders /
      getModels: () => models / getComfyWorkflows: () => comfyWorkflows
      / generatorSources / orderedSources / imageRefsOnly /
      comfyFields / validComfyWorkflowName / hasComfyWorkflow /
      currentComfyWorkflow / comfyFieldKind / ensureComfyWorkflow /
      render / scheduleSave / runCanvasGenerate / renderPromptPreview /
      renderComfyImages / renderComfyCustomField / toggleComfyRandom /
      bindCascadeButtons / cascadeBtnHtml / retryBarHtml). The
      R4-31 inventory's `comfy-controls` row gains
      `evidence_target = static/js/workbench/canvas/classic-comfy-
      controls.js` so the inventory's evidence-grounding test now
      grounds the five Comfy function names in the seam module. Focused
      test
      `test_classic_editor_routes_comfy_workflow_field_controls_through_classic_comfy_controls_seam`
      drives `addNode` / `renderBody` / `renderSettings` in a vm
      sandbox with a stub document and asserts each runs without
      throwing, asserts `addNode` produces
      `(type:'comfy', id:'comfy-test', mode:'text', editModel:'test-comfy-model',
      comfyWorkflow:'')` exactly, asserts `getWorkflowOptions` lists the
      seeded workflows and the empty-list fallback option, exercises the
      full 29-op missing-host-op TypeError loop, source-contracts the
      five wrapper-deletions + `ensureClassicComfyControls().addNode({point})`
      factory shape + `comfy.renderBody({node})` body dispatcher shape.
- [ ] Waves 7–14: each remaining COMPAT capability (RunningHub /
      MiniMax / LTX controls, video-card-body, video-provider/params,
      output-grid-renderer, generation-log, cascade-orchestrator) either
      becomes a bounded compat seam module or stays page-side per the
      R4-31 inventory's documented per-row reasons; no new R4 COMPAT seams
      that bypass an existing seam.
- [ ] Wave 15: asset-library confirmed DEFER-R8 (Asset/Collection runtime
      forbidden in R4; bounded compat stays page-side; no R4 work besides
      re-validating the DEFER-R8 marker is still correct).
- [ ] Wave 16 (final): canvas.js size below bounded bootstrap-only
      threshold (target: ≤ 2 kloc of glue + per-COMPAT deltas) before
      R4-38 can close.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md` (R4-38 evidence section
appended at each wave closure).

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` whenever a wave moves an
ownership row.

Update `AGENT_NEXT_TASK.md` whenever the card's recommended-successor
pointer or its Multi-Wave-plan row changes.

## Final Ownership Evidence

(populated when the card closes — see `CURRENT_EXECUTION_STATUS.md`
for per-wave evidence so far.)

## Wave 1 evidence

- Files changed: `static/js/canvas.js` (3 `resultMediaUrls(` inline,
  3 `comfyResultOutputs(` inline, 6-line wrapper block deleted),
  `tests/test_frontend_workbench_modules.py` (new
  `test_classic_editor_inlines_execution_result_extraction_through_the_shared_seam`),
  `tests/test_classic_capability_inventory.py` (add `MIGRATED` to
  `ALLOWED_DISPOSITIONS` + strict pair-with-MIGRATE sanity),
  `docs/plans/R4_CLASSIC_CAPABILITY_INVENTORY.md` (comfy-result-normalization
  row now `MIGRATED`, evidence = `window.WorkbenchCanvasMediaResultNormalizer.extract`),
  `docs/plans/R4_OWNERSHIP_MATRIX.md` (disposition vocabulary note now
  includes `MIGRATED`).
- Regression: `./scripts/agent-verify.sh` PASS at 344 Python unit tests
  (was 343; +1 from Wave 1 focused test), PASS Python AST parse (76
  files), PASS JavaScript syntax (71 files), PASS Architecture guards
  (4), PASS `git diff --check`. `AGENT VERIFY: PASS`.

## Wave 2 evidence

- Files changed:
  - new `static/js/workbench/canvas/classic-node-factories.js`
    (~115 LOC: host-injected `addNode` / `uid` / `defaultPoint` /
    `imageApiProviders` / `allImageModels` /
    `defaultApiImageResolution` / `resolveMidjourneyProviderId` /
    `modelscopeImageModels`; frozen `addGenerator` / `addMidjourney`
    / `addMsGen` API; TypeError-on-missing-host guard).
  - `static/canvas.html`: `<script src=".../classic-node-factories.js?v=2026.09.07.1"></script>`
    inserted between `provider-controls.js` and
    `classic-execution-host.js`.
  - `static/js/canvas.js`: `function addGeneratorNode / addMidjourneyNode / addMsGenNode`
    function bodies deleted (-39 LOC of factory schema); `let classicNodeFactories = null;`
    + `function ensureClassicNodeFactories()` added next to the existing
    `ensureProviderControls` initializer; the 3 dispatch lines in
    `createNodeByType` (line ~3858-3860) rewritten to call the seam:
    `if(type === 'generator') return ensureClassicNodeFactories().addGenerator({point});`
    (and same for midjourney/msgen).
  - `tests/test_frontend_workbench_modules.py`: new focused test
    `test_classic_editor_routes_provider_node_creation_through_classic_node_factories_seam`
    — drives the seam in a vm sandbox with a mock host and asserts the
    three records land at `host.addNode` with the right `(type, id,
    apiProvider, model, msgenModel)`; iterates each of the 8 required
    host ops in turn to verify TypeError on missing; source-contracts
    pin canvas.html load order (seam before editor), the three
    wrapper-function-deletion markers, and the dispatcher seam-call
    shapes.
  - `tests/test_classic_capability_inventory.py`: schema extension —
    `evidence_target` per capability; defaults to
    `static/js/canvas.js` so legacy MIGRATE / COMPAT / DEFER-R8 entries
    don't need to migrate the manifest schema.
  - `docs/plans/R4_CLASSIC_CAPABILITY_INVENTORY.md`: `provider-node-creation`
    disposition `MIGRATE → MIGRATED`, target_owner kept (Unified
    creation/mutation boundary), `evidence_target` =
    `static/js/workbench/canvas/classic-node-factories.js`, evidence =
    `addGenerator(` / `addMidjourney(` / `addMsGen(` (substrings of the
    seam module).
- Regression: `./scripts/agent-verify.sh` PASS at 345 Python unit tests
  (was 344 after Wave 1; +1 from Wave 2's new focused test), PASS
  Python AST parse (76 files), PASS JavaScript syntax (72 files; +1
  for `classic-node-factories.js`), PASS Architecture guards (4), PASS
  `git diff --check`. `AGENT VERIFY: PASS`.

## Wave 3 evidence

- Files changed:
  - `static/js/workbench/canvas/classic-node-factories.js`: REQUIRED ops
    dict extended with `videoApiProviders` / `providerVideoModels` /
    `videoModels` / `defaultVideoModels` (8 → 12); new `addVideo({point})`
    method registered on the frozen handle. The method bodies out exactly
    the `function addVideoNode(point)` body it replaces: provider default
    `'comfly'`, model fallback chain
    `providerVideoModels(providerId)[0] || videoModels()[0] || defaultVideoModels()[0]`,
    11 typed fields (`duration:5`, `aspectRatio:'16:9'`, `resolution:''`,
    `enhancePrompt/enableUpsample/watermark/cameraFixed/generateAudio/useFrameRoles/multimodal: false`,
    `tempShLinks:[]`, `inputs:[]`, `running:false`).
  - `static/js/canvas.js`: `function addVideoNode(point)` deleted (~26
    LOC); `ensureClassicNodeFactories()` host injects 4 new host ops
    (`videoApiProviders`, `providerVideoModels`, `videoModels: () => videoModels`,
    `defaultVideoModels: () => DEFAULT_VIDEO_MODELS`); `createNodeByType`
    `'video'` dispatch rewritten from `addVideoNode(point)` to
    `ensureClassicNodeFactories().addVideo({point})`.
  - `tests/test_frontend_workbench_modules.py`: Wave 2's test extended
    with the 4 new ops in both the success-case host mock and the
    missing-host-op TypeError loop (so all 12 REQUIRED ops stay strictly
    tested). New focused test
    `test_classic_editor_routes_video_node_creation_through_classic_node_factories_seam`
    drives the seam's `addVideo` in a vm sandbox with a mock host
    covering all 12 REQUIRED ops; asserts the exact record shape
    (type='video', id='vid-test', apiProvider='test-vid',
    model='test-vid-model', duration=5, aspectRatio='16:9', x=222,
    y=333, inputs=[]); source-contracts the canvas.js wrapper-deletion
    (`function addVideoNode` absent) + dispatcher seam-call
    (`ensureClassicNodeFactories().addVideo({point})`) + the 4 host
    injections including the literal
    `defaultVideoModels: () => DEFAULT_VIDEO_MODELS` const-returning
    closure.
  - `docs/plans/R4_CLASSIC_CAPABILITY_INVENTORY.md`: R4-31's `video-player`
    row SPLIT — the factory half (this card) becomes `video-node-creation`
    MIGRATED (evidence_target =
    `static/js/workbench/canvas/classic-node-factories.js`, evidence =
    `addVideo(`); the body half becomes `video-card-body` COMPAT
    (evidence = `renderVideoBody`, default `evidence_target` =
    canvas.js). Inventory total grows 13 → 14 capabilities; Summary
    block adjusted (`MIGRATED: 3`, `MIGRATE: 1`, `COMPAT: 9`,
    `DEFER-R8: 1`).
- Regression: `./scripts/agent-verify.sh` PASS at 346 Python unit tests
  (was 345 after Wave 2; +1 from Wave 3's new focused test), PASS
  Python AST parse (76 files), PASS JavaScript syntax (72 files), PASS
  Architecture guards (4), PASS `git diff --check`.
  `AGENT VERIFY: PASS`.

## Wave 4 evidence

- Files changed:
  - `static/js/workbench/canvas/classic-node-factories.js`: new
    `addOutput({point})` method registered on the frozen handle (no new
    REQUIRED ops — `addOutputNode` only consumed the three already-
    required ops `addNode` / `uid` / `defaultPoint`). The method body
    mirrors the deleted `function addOutputNode(point)` exactly: 3-line
    factory
    (`{id:uid('out'), type:'output', x:p.x, y:p.y, images:[]}`) with
    `p = point || host.defaultPoint(260, 0)`.
  - `static/js/canvas.js`: `function addOutputNode(point)` deleted (-6
    LOC of factory schema). `createNodeByType` `'output'` dispatch
    rewritten from `addOutputNode(point)` to
    `ensureClassicNodeFactories().addOutput({point})`.
  - `tests/test_frontend_workbench_modules.py`: new focused test
    `test_classic_editor_routes_output_node_creation_through_classic_node_factories_seam`
    — drives the seam's `addOutput` in a vm sandbox with a mock host
    covering all 12 REQUIRED ops (cumulative across Waves 2-4); asserts
    the exact record shape `(type:'output', id:'out-test', x:444,
    y:555, images:[])`; source-contracts the canvas.js
    wrapper-deletion (`function addOutputNode` absent) + dispatcher
    seam-call (`ensureClassicNodeFactories().addOutput({point})`).
  - `tests/test_classic_capability_inventory.py`: loosened
    `test_classification_is_meaningful_across_dispositions` — required
    invariants are now COMPAT + DEFER-R8 (the R4-wide + R8-governance
    foundations); MIGRATE is optional (all four MIGRATE rows were
    promoted to MIGRATED over Waves 1-4); when MIGRATE is present,
    MIGRATED must also be present (forward-driving). This is the
    expected terminal state — once all MIGRATE rows have been
    promoted, MIGRATE=0 with MIGRATED≥1 is the healthy closing
    shape.
  - `docs/plans/R4_CLASSIC_CAPABILITY_INVENTORY.md`: R4-31's
    `output-node` row SPLIT — the factory half (this card) becomes
    `output-node-creation` MIGRATED (evidence_target =
    `static/js/workbench/canvas/classic-node-factories.js`, evidence =
    `addOutput(`); the grid/lifecycle half becomes
    `output-grid-renderer` COMPAT (evidence =
    `refreshOutputNodeContent` / `renderOutputGrid` /
    `bindOutputWrap`, default `evidence_target` = canvas.js; ~250 LOC
    of grid + media lifecycle that stays page-side per the COMPAT /
    R8 boundary). Inventory total grows 14 → 15 capabilities;
    Summary block adjusted (`MIGRATED: 4`, `MIGRATE: 0`,
    `COMPAT: 10`, `DEFER-R8: 1`).
- Regression: `./scripts/agent-verify.sh` PASS at 347 Python unit tests
  (was 346 after Wave 3; +1 from Wave 4's new focused test), PASS
  Python AST parse (76 files), PASS JavaScript syntax (72 files), PASS
  Architecture guards (4), PASS `git diff --check`.
  `AGENT VERIFY: PASS`.

## Wave 5 evidence

- Files changed:
  - `static/js/workbench/canvas/classic-card-body-renderer.js` (new,
    ~960 LOC: IIFE wrapper; REQUIRED_OPS list with 49 host ops;
    `create(host)` factory that validates every required op is present
    (TypeError-on-missing-host) and destructures them into module-scope
    `var` bindings; the four function bodies — `renderLLMBody`,
    `renderGeneratorBody`, `renderMidjourneyBody`, `renderMsGenBody`
    — copied verbatim from canvas.js with all helper references now
    pointing to host-injected locals; frozen handle with four `renderXxx`
    methods that forward to the function bodies; window export
    `WorkbenchCanvasClassicCardBodyRenderer = Object.freeze({create})`).
    The four render bodies are the largest single-purpose rendering
    surface in canvas.js (~904 LOC: 72 + 315 + 77 + 440) and are now
    reachable only through this seam module.
  - `static/canvas.html`: `<script src=".../classic-card-body-renderer.js?v=2026.09.07.1"></script>`
    inserted between `classic-execution-host.js` and `canvas.js`,
    AFTER `provider-controls.js` (the card-body seam consumes
    `ensureProviderControls` via host injection so the dependency
    order must hold).
  - `static/js/canvas.js`: `function renderLLMBody` /
    `renderGeneratorBody` / `renderMidjourneyBody` / `renderMsGenBody`
    function definitions deleted (-904 LOC of body construction,
    comprising the four large page-side renderers). `createNodeByType`'s
    4 kind-dispatch lines rewritten from `body.appendChild(renderXxxBody(node))`
    to `body.appendChild(cardBody.renderXxx({node}))` after a single
    `const cardBody = ensureClassicCardBodyRenderer();` line. New
    `let classicCardBodyRenderer = null;` + `function ensureClassicCardBodyRenderer()`
    next to the existing `ensureClassicNodeFactories`, injecting all
    49 REQUIRED host ops (escapeHtml / tr / provider + model
    resolvers / image helpers / MsGen catalog / renderImageInputList /
    renderPromptPreview / cascadeBtnHtml / retryBarHtml /
    bindCascadeButtons / scheduleSave / render / runCanvasGenerate /
    ensureProviderControls, etc.).
  - `tests/test_frontend_workbench_modules.py`: new focused test
    `test_classic_editor_routes_provider_card_body_through_classic_card_body_renderer_seam`
    — drives all four render methods in a vm sandbox with a stub
    `document.createElement` + minimal mock host (49 ops), asserts each
    runs without throwing (returns a frozen handle + DOM element);
    iterates all 49 host ops in turn to verify TypeError-on-missing-host
    (pin count 49 in `assertEqual(len(REQUIRED), 49)` to keep seam +
    test synchronized); source-contracts canvas.html load order
    (seam before editor), the four `function renderXxxBody`
    wrapper-deletions in canvas.js, and the four dispatcher seam-call
    shapes (`cardBody.renderXxx({node})`).
  - `tests/test_frontend_workbench_modules.py`: pre-existing
    `test_provider_controls_is_loaded_before_the_classic_page_and_llm_body_uses_it`
    updated for Wave 5 — the five `providerControls.setField(...)`
    assertions now target the card-body seam module (where
    `renderLLMBody` lives since Wave 5 moved it); the canvas.html
    load-order assertion also pins the
    `provider-controls → card-body → canvas.js` dependency order; the
    `ensureProviderControls` host-injection assertion stays on
    canvas.js (page owns the host, seam consumes it).
  - `docs/plans/R4_CLASSIC_CAPABILITY_INVENTORY.md`: `provider-card-body`
    manifest row gets `evidence_target =
    "static/js/workbench/canvas/classic-card-body-renderer.js"` so
    the `test_every_capability_evidence_is_grounded_in_source`
    inventory test now grounds the four renderXxxBody evidence names
    in the seam module instead of canvas.js.
- Regression: `./scripts/agent-verify.sh` PASS at 348 Python unit tests
  (was 347 after Wave 4; +1 from Wave 5's new focused test), PASS
  Python AST parse (76 files), PASS JavaScript syntax (73 files; +1 for
  the new seam module), PASS Architecture guards (4), PASS
  `git diff --check`. `AGENT VERIFY: PASS`.

## Wave 6 evidence

- Files changed:
  - `static/js/workbench/canvas/classic-comfy-controls.js` (new,
    ~325 LOC: IIFE wrapper; REQUIRED_OPS list with 29 host ops;
    `create(host)` factory that validates every required op is present
    (TypeError-on-missing-host) and destructures them into module-scope
    `var` bindings; the five function bodies — `addComfyNode`,
    `comfyWorkflowOptions`, `renderComfyBody`, `renderComfySettings`,
    `updateComfyField` — copied verbatim from canvas.js with all
    helper references now pointing to host-injected locals; frozen
    handle with five methods that forward to the function bodies;
    window export
    `WorkbenchCanvasClassicComfyControls = Object.freeze({create})`).
    The five Comfy bodies total ~222 LOC (32 + 4 + 64 + 80 + 42) and
    are now reachable only through this seam module.
  - `static/canvas.html`: `<script
    src=".../classic-comfy-controls.js?v=2026.09.07.1"></script>`
    inserted between `classic-card-body-renderer.js` and `canvas.js`,
    so the load order is now
    `provider-controls → card-body → comfy-controls → canvas.js`.
  - `static/js/canvas.js`: `function addComfyNode` /
    `comfyWorkflowOptions` / `renderComfyBody` / `renderComfySettings`
    / `updateComfyField` function definitions deleted (-222 LOC of
    Comfy body / settings / field construction). `createNodeByType`'s
    `'comfy'` dispatch rewritten from `return addComfyNode(point)` to
    `return ensureClassicComfyControls().addNode({point})`. The body
    dispatcher's `'comfy'` branch rewritten from
    `body.appendChild(renderComfyBody(node))` to
    `body.appendChild(comfy.renderBody({node}))` after a single
    `const comfy = ensureClassicComfyControls();` line alongside the
    Wave 5 `const cardBody = ensureClassicCardBodyRenderer();` line.
    New `let classicComfyControls = null;` + `function
    ensureClassicComfyControls()` next to the existing
    `ensureClassicCardBodyRenderer`, injecting all 29 REQUIRED host
    ops (document / escapeHtml / tr / addNode / uid / defaultPoint /
    allImageModels / imageApiProviders / getModels: () => models /
    getComfyWorkflows: () => comfyWorkflows / generatorSources /
    orderedSources / imageRefsOnly / comfyFields /
    validComfyWorkflowName / hasComfyWorkflow / currentComfyWorkflow /
    comfyFieldKind / ensureComfyWorkflow / render / scheduleSave /
    runCanvasGenerate / renderPromptPreview / renderComfyImages /
    renderComfyCustomField / toggleComfyRandom / bindCascadeButtons /
    cascadeBtnHtml / retryBarHtml). The two closure values
    (`getModels`, `getComfyWorkflows`) keep the seam's
    REQUIRED-all-function contract stable even though `models` is a
    const and `comfyWorkflows` is a `let`.
  - `tests/test_frontend_workbench_modules.py`: new focused test
    `test_classic_editor_routes_comfy_workflow_field_controls_through_classic_comfy_controls_seam`
    — drives `addNode` / `renderBody` / `renderSettings` in a vm
    sandbox with a stub `document.createElement` + minimal mock host
    (29 ops); asserts each runs without throwing; asserts `addNode`
    produces
    `(type:'comfy', id:'comfy-test', mode:'text', editModel:'test-comfy-model',
    comfyWorkflow:'')` exactly (the same record shape the page-side
    factory produced); asserts `getWorkflowOptions` lists the seeded
    workflows and the empty-list fallback option (`<option value="">
    canvas.comfyNoWorkflow</option>`); iterates all 29 host ops to
    verify TypeError-on-missing-host (with a
    `assertEqual(len(REQUIRED), 29)` count pin to keep seam + test
    synchronized); source-contracts the canvas.html seam load order
    (comfy-controls before canvas.js), the five `function` wrapper
    deletions in canvas.js, and the two dispatcher seam-call shapes
    (`ensureClassicComfyControls().addNode({point})` +
    `comfy.renderBody({node})`).
  - `docs/plans/R4_CLASSIC_CAPABILITY_INVENTORY.md`: `comfy-controls`
    manifest row gets `evidence_target =
    "static/js/workbench/canvas/classic-comfy-controls.js"` so the
    `test_every_capability_evidence_is_grounded_in_source` inventory
    test now grounds the five Comfy function names
    (`addComfyNode` / `renderComfyBody` / `renderComfySettings` /
    `updateComfyField` / `comfyWorkflowOptions`) in the seam module
    instead of canvas.js.
- Regression: `./scripts/agent-verify.sh` PASS at 349 Python unit
  tests (was 348 after Wave 5; +1 from Wave 6's new focused test),
  PASS Python AST parse (76 files), PASS JavaScript syntax (74
  files; +1 for the new seam module), PASS Architecture guards (4),
  PASS `git diff --check`. `AGENT VERIFY: PASS`.

## Recommended Next Card (after this card itself closes)

`R4-39 — Remove Legacy canvas.js Product Runtime`
(`docs/tasks/backlog/R4-39-remove-classic-runtime.md`)

Within R4-38 itself, the next wave after Wave 6 is **Wave 7:
RunningHub workflow/params COMPAT seam** (batches `addRhNode` +
`renderRhBody` + `renderRhParams` + `runningHubProvider` +
`currentRunningHubWorkflow` + `currentRunningHubWorkflowConfig` as
bounded compat per R4-31 — R8 owns the real executor-driven
RunningHub workflow rendering; the same seam pattern as Wave 5
card-body and Wave 6 comfy-controls applies — extract to
`static/js/workbench/canvas/classic-runninghub-controls.js`).

Do not execute waves in batch — each wave is its own focused commit
+ regression cycle.

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

Add or run the smallest behavioral tests that prove this card's exact goal.
Do not rely only on source-string checks when runtime behavior can be tested.

## Regression

Run:

```bash
./scripts/agent-verify.sh
```

## Definition of Done

- [ ] canvas.js no longer owns product runtime responsibilities.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-39`

Do not execute the next card in the same Agent run.
