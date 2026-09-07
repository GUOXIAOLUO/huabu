# CARD R4-38 — Reduce canvas.js to Bootstrap/Compatibility Only

- Round: R4
- Priority: P0
- Status: IN_PROGRESS (umbrella shrink card; multi-wave; closes only when canvas.js is bootstrap/compat-only)
- Activated: 2026-09-07T15:30+08:00
- Wave 1 done: 2026-09-07T15:33+08:00
- Wave 2 done: 2026-09-07T15:55+08:00
- Wave 3 done: 2026-09-07T16:05+08:00
- Wave 4 done: 2026-09-07T16:13+08:00
- Closed: (not yet — 11 of 15 Classic capabilities still need shrink waves;
  inventory grew from 13 → 14 (Wave 3) → 15 (Wave 4) as video-player and
  output-node were split into factory-half MIGRATE + body-half COMPAT.)
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

The 13 Classic capabilities from the R4-31 inventory partition into the
following shrink waves. Each wave is one focused commit (+0..1 new tests
per focused contract change). The card stays open across all waves and
closes once every wave is DONE.

| Wave | Capability | Disposition | Action |
|---|---|---|---|
| **1 (done)** | comfy-result-normalization | MIGRATED | inline `resultMediaUrls` / `comfyResultOutputs` call sites through `media-result-normalizer.js`; delete the two wrapper function definitions in canvas.js. |
| **2 (done)** | provider-node-creation (addGeneratorNode / addMidjourneyNode / addMsGenNode) | MIGRATED | new host seam `static/js/workbench/canvas/classic-node-factories.js` (`window.WorkbenchCanvasClassicNodeFactories.create(host)` returns frozen `{addGenerator, addMidjourney, addMsGen}`); canvas.js deletes the local `function addGeneratorNode / addMidjourneyNode / addMsGenNode` definitions and re-routes its `createNodeByType` dispatcher through `ensureClassicNodeFactories().addXxx({point})`. |
| **3 (done)** | video-node-creation (addVideoNode factory half) | MIGRATED | extend `classic-node-factories.js` with 4 new required host ops (`videoApiProviders` / `providerVideoModels` / `videoModels` / `defaultVideoModels`) and the `addVideo({point})` method; canvas.js deletes `function addVideoNode` and re-routes the `'video'` dispatch through `ensureClassicNodeFactories().addVideo({point})`. R4-31 inventory's `video-player` row split into `video-node-creation` (MIGRATED) + `video-card-body` (COMPAT, R8; `renderVideoBody` stays page-side as a provider card body — same disposition as `provider-card-body`). |
| **4 (done)** | output-node-creation (addOutputNode factory half) | MIGRATED | extend `classic-node-factories.js` with a new `addOutput({point})` method (no new REQUIRED ops needed — `addOutputNode` only used `addNode` / `uid` / `defaultPoint`); canvas.js deletes `function addOutputNode` (3-line factory) and re-routes the `'output'` dispatch through `ensureClassicNodeFactories().addOutput({point})`. R4-31 inventory's `output-node` row split into `output-node-creation` (MIGRATED) + `output-grid-renderer` (COMPAT, target = Unified media renderer / render runtime; evidence = `refreshOutputNodeContent` / `renderOutputGrid` / `bindOutputWrap`, ~250 LOC of grid+media lifecycle that stays page-side per the inventory evidence and the COMPAT/R8 boundary). Inventory test `test_classification_is_meaningful_across_dispositions` loosened to allow MIGRATE=0 + MIGRATED≥1 as a healthy terminal state (R4-38 has wound down all four MIGRATE rows). |
| 5–11 | 7 retained COMPAT capabilities (Comfy / RunningHub / MiniMax / LTX controls, video params, generation log, cascade orchestrators) | COMPAT (R8) | bounded compat seam modules per cluster (no runtime replacement in R4) — see R4-25/R4-30 host-seam pattern. |
| 12 | asset-library | DEFER-R8 | out of R4 scope (Asset/Collection runtime forbidden in R4). |
| 13 (final) | shrink-to-bootstrap | — | after waves 1–12, the remaining ~14 kloc in canvas.js becomes a small compat shell: imageApiProviders / videoApiProviders / provider resolvers, save scheduler wiring, the few DOM event handlers that touch page-specific UI, and the canvas-bootstrap sequence. |

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
- [ ] Wave 5: provider-card-body COMPAT seam (largest COMPAT row,
      batches `renderLLMBody` + `renderGeneratorBody` +
      `renderMidjourneyBody` + `renderMsGenBody` as bounded compat per
      R4-31 — R8 owns the real executor-driven body rendering).
- [ ] Wave 5–12: each COMPAT capability either stays canvas-owned behind
      a bounded compat seam module or stays page-side per the R4-31
      inventory's documented per-row reasons; no new R4 COMPAT seams
      that bypass an existing seam.
- [ ] canvas.js size below bounded bootstrap-only threshold (target:
      <= 2 kloc of glue + per-COMPAT deltas) before R4-38 can close.

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

## Recommended Next Card (after this card itself closes)

`R4-39 — Remove Legacy canvas.js Product Runtime`
(`docs/tasks/backlog/R4-39-remove-classic-runtime.md`)

Within R4-38 itself, the next wave after Wave 4 is **Wave 5:
provider-card-body COMPAT seam** (largest COMPAT row, batches
`renderLLMBody` + `renderGeneratorBody` + `renderMidjourneyBody` +
`renderMsGenBody` as bounded compat per R4-31 — R8 owns the real
executor-driven body rendering).

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
