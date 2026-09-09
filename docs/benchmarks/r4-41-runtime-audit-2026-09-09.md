# R4-41 Runtime Listener / Timer Audit — 2026-09-09

This is a local worktree audit for the R4-41 acceptance attempt. It is not a
merged Integration Owner Gate result.

## Deterministic source audit

The audit scans the native Canvas responsibility modules for global event
registrations, repeating timers, and observer constructors.

| Surface | Result |
|---|---|
| `canvas-app-interaction.js` global listeners | `dragend`, `drop`, `paste`, one `blur` |
| `canvas-app-records.js` global listeners | one `mousedown`, two distinct `resize` callbacks consolidated into one, one theme callback |
| `canvas-app-output-ui.js` global pointer listeners | one guarded `mousemove` + one guarded `mouseup`; preview/compare element initialization is also idempotent; touch lifecycle remains separate |
| `canvas-remote-sync.js` repeating timers | one guarded interval per controller; repeated `start()` is idempotent |
| `canvas-app-state.js` repeating timers | one output interval, cleared when no pending outputs remain |
| Observer constructors in native app modules | none found |

Focused regression coverage verifies the output pointer pair and remote-sync
start/stop idempotence. The full local verifier passes 637 tests, 81 Python AST
files, 112 JavaScript files, 4 architecture guards, and `git diff --check`.

## Disposable browser memory observation

The read-only performance harness was run against the disposable 300-node
Canvas record with `memory_cycles=5`. Chromium exposed
`performance.memory.usedJSHeapSize`; five confirmed Canvas `render()` passes
held the observed heap at 24,905,516 bytes before and after the passes (delta:
0 bytes). The same run rendered 300 nodes / 8,895 DOM elements and passed
zoom, pan, and minimap visual updates (16.600 / 45.100 / 21.400 ms).

This is a single local diagnostic sample, not a release threshold or a merged
acceptance result. The harness reports `UNSUPPORTED` instead of inventing a
value when a browser does not expose the heap metric.

The formal checklist still requires the same inspection against merged code,
plus 100/300-node acceptance and duplicate-resource evidence. Those
requirements remain open until the current implementation is merged and
re-evaluated by the Integration Owner.
