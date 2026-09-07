# R4 Smart Execution Compatibility

Owner: card R4-30. Characterizes how the retained pre-R8 Smart execution path
owns Canvas lifecycle/state, and establishes a bounded host seam so execution
no longer owns Canvas directly. This is a characterization + narrow-seam
deliverable — it does **not** implement an ExecutionRuntime (R8), and it keeps
the actual provider/API/WebSocket transport page-side as compatibility.

## Disposition vocabulary

- **seamed** — the entry point already routes through the shared
  `WorkbenchCanvasExecutionCompatibility.run` wrapper (a prior card).
- **host-cutover** — the entry point's Canvas lifecycle/state writes now go
  through `WorkbenchCanvasExecutionHost` (this card).
- **host-candidate** — page-owned Canvas writes remain; characterized here,
  cut over in a follow-on card (the surface is enumerated so the work is
  bounded, not deferred silently).
- **transport-only** — no Canvas write; pure transport/queueing, stays
  page-owned compatibility.
- **flag-only** — read/flag only (no durable Canvas mutation), stays
  page-owned.

## The Canvas-lifecycle/state ownership surface

Across the retained execution path, the following Canvas-side operations are
performed directly by page code (this is what "execution owns Canvas" means):

1. **Node state writes** — `node.running`, `node.pending`, `node.pendingTasks`,
   `node.promptResult`, `node.promptResultOutdated`, `node.llmProvider`,
   `node.llmModel`, `node.images`, `node.runStartedAt`, `node.runTimerHidden`.
2. **Node materialization + connection** — `nodes.push(output)`,
   `nodes.filter(...)`, `addConnection(...)`, `connectInputNode(...)`,
   `canvas.connections.filter(...)`.
3. **Selection** — `selectedId`, `selectedImage`.
4. **Undo** — `pushUndo()`, `undoSuppressed`.
5. **Persist/render** — `render()`, `scheduleSave()`, `saveCanvas()`.
6. **Global settings** — `settings = {...}`.
7. **Feedback** — `addSmartGenerationLog(...)`, `toast(...)`,
   `clearPromptInput(...)`.

## Host seam (this card)

`static/js/workbench/canvas/execution-host.js` exposes
`window.WorkbenchCanvasExecutionHost.create(host)` — a frozen, validated host
handle. The Smart page injects its concrete Canvas operations; execution
functions call the handle instead of touching Canvas state directly. The module
is product-neutral (no Smart/Classic adapter detail) and owns no Canvas state.

Host operations (the minimal required R4 compatibility surface):

- `markRunning(node, running)` — set/clear a node's running state.
- `writePromptResult(node, result)` — write a prompt node's LLM result
  (`promptResult`, `promptResultOutdated`, `provider`, `model`).
- `save()` — persist the canvas.
- `render()` — re-render the canvas.
- `notifyError(message)` — surface a run error.

Cut over this card: `runPromptLLMNode` (the simplest, self-contained execution
entry — no cascade, no output-node materialization, no connection mutation).
The remaining entry points are characterized below and remain host-candidates.

## Inventory

| Entry point | Disposition | Canvas ownership (direct page writes) |
|---|---|---|
| `runGeneration` | seamed | wraps `runGenerationLegacy` via `WorkbenchCanvasExecutionCompatibility.run` |
| `runGenerationLegacy` | host-candidate | settings; `pushUndo`; `createPendingOutputFromSource` (`nodes.push` + connect + `selectedId`); `pendingNode.*`; `render`; `scheduleSave`; `saveCanvas`; `addSmartGenerationLog` |
| `runPromptLLMNode` | host-cutover | `node.running`; `node.promptResult`/`promptResultOutdated`/`llmProvider`/`llmModel`; `render`; `scheduleSave`; `toast` |
| `runSmartCascade` | host-candidate | output-node materialization + connect + `selectedId`; `render`; `scheduleSave` |
| `runCascadeStepIntoNode` | host-candidate | settings; `finalizePendingNode`; `render`; `scheduleSave` |
| `runQueuedSmartComfyGenerate` | transport-only | none (task create + wait) |
| `requestSmartCascadeStop` | flag-only | `smartCascadeRuns` stop flag (no durable write) |
| `activeSmartCascadeCount` | flag-only | reads `smartCascadeRuns.size` (no write) |

Out of scope (R8, not re-implemented): `ExecutorRegistry`, `ExecutionRuntime`,
`Provider`/`Model` registry, and the provider/API/WebSocket transport itself.

## Evidence manifest

Machine-readable; anchored by `tests/test_smart_execution_compatibility.py`.

```json
{
  "source": "static/js/smart-canvas.js",
  "entry_points": [
    {"id": "run-generation", "function": "runGeneration", "disposition": "seamed", "evidence": ["runGenerationLegacy"]},
    {"id": "run-generation-legacy", "function": "runGenerationLegacy", "disposition": "host-candidate", "evidence": ["buildPromptRequest", "createPendingOutputFromSource", "finalizePendingNode"]},
    {"id": "run-prompt-llm", "function": "runPromptLLMNode", "disposition": "host-cutover", "evidence": ["promptNodeLLMInputText", "resolveChatProviderId", "resolveChatModel"]},
    {"id": "run-cascade", "function": "runSmartCascade", "disposition": "host-candidate", "evidence": ["runCascadeStepIntoNode"]},
    {"id": "run-cascade-step", "function": "runCascadeStepIntoNode", "disposition": "host-candidate", "evidence": ["smartLoopRoundSettings", "finalizePendingNode"]},
    {"id": "run-comfy-queue", "function": "runQueuedSmartComfyGenerate", "disposition": "transport-only", "evidence": ["createSmartComfyTask", "waitSmartComfyTaskResult"]},
    {"id": "cascade-stop", "function": "requestSmartCascadeStop", "disposition": "flag-only", "evidence": ["activeSmartCascadeCount"]},
    {"id": "cascade-graph", "function": "resolveSmartCascadeLoop", "disposition": "flag-only", "evidence": ["smartCascadeGraphForTail"]}
  ]
}
```
