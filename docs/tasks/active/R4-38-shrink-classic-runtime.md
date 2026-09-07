# CARD R4-38 — Reduce canvas.js to Bootstrap/Compatibility Only

- Round: R4
- Priority: P0
- Status: IN_PROGRESS (umbrella shrink card; multi-wave; closes only when canvas.js is bootstrap/compat-only)
- Activated: 2026-09-07T15:30+08:00
- Wave 1 done: 2026-09-07T15:33+08:00
- Wave 2 done: 2026-09-07T15:55+08:00
- Closed: (not yet — 11 of 13 Classic capabilities still need shrink waves)
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
| 3 | video-player (addVideoNode + renderVideoBody) | MIGRATE → MIGRATED | creation routed through creation boundary + video body delegated to MediaRenderer. |
| 4 | output-node (addOutputNode + result grid family) | MIGRATE → MIGRATED | addOutputNode → creation boundary; output grid family to MediaRenderer shared lifecycle. |
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
- [ ] Wave 3: video-player MIGRATED.
- [ ] Wave 4: output-node MIGRATED.
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

## Recommended Next Card (after this card itself closes)

`R4-39 — Remove Legacy canvas.js Product Runtime`
(`docs/tasks/backlog/R4-39-remove-classic-runtime.md`)

Within R4-38 itself, the next wave after Wave 2 is **Wave 3:
video-player MIGRATE** (`addVideoNode` + `renderVideoBody` — creation
boundary + Video body delegated to MediaRenderer or a dedicated
`classic-video-factory.js` host seam).

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
