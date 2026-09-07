# R4 Classic Execution Compatibility

Owner: card R4-33. Characterizes how the retained pre-R8 Classic execution path
owns Canvas lifecycle/state, and establishes a bounded host seam so execution
no longer owns Canvas directly. This is a characterization + narrow-seam
deliverable — it does **not** implement an ExecutionRuntime (R8), and it keeps
the actual provider/API/transport page-side as compatibility.

## Disposition vocabulary

- **seamed** — the entry point already routes through the shared
  `WorkbenchCanvasExecutionCompatibility.run` wrapper (a prior card).
- **host-cutover** — the entry point's Canvas lifecycle/state writes now go
  through `WorkbenchCanvasClassicExecutionHost` (this card).
- **host-candidate** — page-owned Canvas writes remain; characterized here,
  cut over in a follow-on card (the surface is enumerated so the work is
  bounded, not deferred silently).
- **transport-only** — no Canvas write; pure transport/queueing, stays
  page-owned compatibility.
- **flag-only** — read/flag only (no durable Canvas mutation), stays
  page-owned.

## The Canvas-lifecycle/state ownership surface

Across the retained Classic execution path, the following Canvas-side
operations are performed directly by page code (this is what "execution owns
Canvas" means):

1. **Node state writes** — `node.running`, `node.outputText`, `node.runStatus`,
   `node.runError`, `node._cascadeFailed`, `node._cascadeIdx`,
   `node.generatedOutputs`, `node._activeLoopCtx`.
2. **Cascade context flags** — `cascadeRunningIds`, `cascadeStopIds`,
   `cascadeSerialIds`, `cascadeContexts`, `loopContext`.
3. **Persist/render** — `refreshNodes(...)`, `scheduleSave()`, `saveCanvas()`.
4. **Feedback** — `alert(...)`.

## Host seam (this card)

`static/js/workbench/canvas/classic-execution-host.js` exposes
`window.WorkbenchCanvasClassicExecutionHost.create(host)` — a frozen, validated
host handle. The Classic page injects its concrete Canvas operations; execution
functions call the handle instead of touching Canvas state directly. The module
is product-neutral (no Classic adapter detail) and owns no Canvas state.

Host operations (the minimal required R4 compatibility surface):

- `markRunning(node, running)` — set/clear a node's running state.
- `writeOutputText(node, text)` — write a prompt node's LLM text result.
- `setRunStatus(node, status, error)` — set a node's run status + error.
- `render(node)` — re-render a node's card.
- `save()` — persist the canvas.
- `notifyError(message)` — surface a run error.

Cut over this card: `runLLMNode` (the simplest, self-contained Classic
execution entry — no cascade orchestration, no output-node materialization, no
connection mutation). The remaining entry points are characterized below and
remain host-candidates.

## Inventory

| Entry point | Disposition | Canvas ownership (direct page writes) |
|---|---|---|
| `runCanvasGenerate` | seamed | wraps `runCanvasGenerateLegacy` via `WorkbenchCanvasExecutionCompatibility.run` |
| `runCanvasGenerateLegacy` | host-candidate | guard read (`node.running`, `cascadeRunningIds`) then dispatches `runCascadeNodeByType` |
| `runLLMNode` | host-cutover | `node.running`; `node.outputText`; `node.runStatus`/`node.runError`; `refreshNodes`; `scheduleSave`; `alert` |
| `runCascadeNodeByType` | host-candidate | dispatches per node type (`runGenerator`/`runMidjourneyNode`/`runMsGenNode`/`runComfyNode`/`runLTXDirectorNode`/`runLLMNode`/`runVideoNode`/`runRhNode`/`runMiniMaxNode`) |
| `runCascadeNodeWithLoopContext` | host-candidate | `loopContext` global; `node._activeLoopCtx`; delegates `runCascadeNodeByType` |
| `runLimitedCascadeRounds` | host-candidate | worker-pool scheduling (no Canvas write) |
| `computeCascadeOrder` | flag-only | graph read (topological order) |
| `computeConnectedWorkflowOrder` | flag-only | graph read |
| `runNodeCascade` | host-candidate | `beginCascade`; `node.generatedOutputs`/`runStatus`/`_cascadeIdx`; `refreshNodes`; `loopContext`; `finalizeCascade` |
| `runOneCascadePass` | host-candidate | `node.runStatus`/`runError`/`_cascadeFailed`; per-type dispatch; `refreshNodes` |
| `retryNodeAndDownstream` | host-candidate | `beginCascade`; `runOneCascadePass`; `finalizeCascade` |
| `beginCascade` | host-candidate | `cascadeRunningIds`/`cascadeSerialIds`/`cascadeContexts` flags |
| `finalizeCascade` | host-candidate | context teardown; `clearCascadeNodeState`; `refreshNodes` |
| `requestCascadeStop` | flag-only | `cascadeStopIds` flag + context abort (no durable write) |
| `cancelCascade` | flag-only | delegates `requestCascadeStop` |

Out of scope (R8, not re-implemented): `ExecutorRegistry`, `ExecutionRuntime`,
`Provider`/`Model` registry, and the provider/API transport itself.

## Evidence manifest

Machine-readable; anchored by `tests/test_classic_execution_compatibility.py`.

```json
{
  "source": "static/js/canvas.js",
  "entry_points": [
    {"id": "canvas-generate", "function": "runCanvasGenerate", "disposition": "seamed", "evidence": ["runCanvasGenerateLegacy"]},
    {"id": "canvas-generate-legacy", "function": "runCanvasGenerateLegacy", "disposition": "host-candidate", "evidence": ["runCascadeNodeByType"]},
    {"id": "llm-node", "function": "runLLMNode", "disposition": "host-cutover", "evidence": ["callCanvasLLM", "llmInputText"]},
    {"id": "cascade-by-type", "function": "runCascadeNodeByType", "disposition": "host-candidate", "evidence": ["runGenerator", "runComfyNode"]},
    {"id": "cascade-loop-context", "function": "runCascadeNodeWithLoopContext", "disposition": "host-candidate", "evidence": ["runCascadeNodeByType"]},
    {"id": "cascade-limited-rounds", "function": "runLimitedCascadeRounds", "disposition": "host-candidate", "evidence": ["cascadeParallelLimit"]},
    {"id": "cascade-order", "function": "computeCascadeOrder", "disposition": "flag-only", "evidence": ["resolveCascadeLoop"]},
    {"id": "workflow-order", "function": "computeConnectedWorkflowOrder", "disposition": "flag-only", "evidence": ["canvasWorkflowEdges"]},
    {"id": "node-cascade", "function": "runNodeCascade", "disposition": "host-candidate", "evidence": ["beginCascade", "finalizeCascade"]},
    {"id": "one-cascade-pass", "function": "runOneCascadePass", "disposition": "host-candidate", "evidence": ["runGenerator", "runLLMNode"]},
    {"id": "retry-downstream", "function": "retryNodeAndDownstream", "disposition": "host-candidate", "evidence": ["runOneCascadePass", "beginCascade"]},
    {"id": "begin-cascade", "function": "beginCascade", "disposition": "host-candidate", "evidence": ["createCascadeContext"]},
    {"id": "finalize-cascade", "function": "finalizeCascade", "disposition": "host-candidate", "evidence": ["queueCascadeCleanup", "clearCascadeNodeState"]},
    {"id": "cascade-stop", "function": "requestCascadeStop", "disposition": "flag-only", "evidence": ["ensureCascadeActive"]},
    {"id": "cancel-cascade", "function": "cancelCascade", "disposition": "flag-only", "evidence": ["requestCascadeStop"]}
  ]
}
```
