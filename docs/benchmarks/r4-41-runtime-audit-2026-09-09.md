# R4-41 Merged Runtime Resource and Performance Acceptance — 2026-09-09

## Scope and method

This local-`main` acceptance run uses two disposable SQLite Canvas records
(100 and 300 prompt nodes) and the read-only
`static/canvas-performance-harness.html`. The harness loads the actual
`canvas.html` runtime in a browser iframe, verifies the rendered node count,
executes zoom/pan/minimap visual updates, then calls the runtime's real
`render()` ten times.

The resource baseline is taken only after two animation frames have settled
initial icon hydration. Taking a baseline immediately after iframe readiness
includes one-off icon replacement and falsely reports it as rerender growth.
The warm baseline is therefore part of the harness contract, not an exclusion
from the observation.

## Browser acceptance results

| Check | 100 nodes | 300 nodes | Result |
|---|---:|---:|---|
| Rendered nodes | 100 | 300 | PASS |
| Initial rendered DOM elements | 3,495 | 8,895 | PASS |
| Actual `render()` passes | 10 | 10 | PASS |
| Settled DOM before / after | 3,594 / 3,594 | 9,194 / 9,194 | PASS (delta 0) |
| Chromium `usedJSHeapSize` before / after | 19,233,165 / 19,233,165 | 24,840,940 / 24,840,940 | PASS (delta 0) |
| Zoom visual update | 16.4 ms | 13.8 ms | PASS |
| Pan visual update | 16.9 ms | 50.0 ms | PASS |
| Minimap refresh | 33.0 ms | 16.7 ms | PASS |

Both browser runs returned `RESULT: PASS`, `renderer_flags=stable`, and
`target_visibility=offscreen`. The 300-node largest observed interaction was
the 50.0 ms pan update, below the local 120 ms visual-settle alert in the
existing canvas payload baseline. These are local acceptance values, not a
cross-device performance promise.

`performance.memory` is Chromium-specific. The harness reports `UNSUPPORTED`
rather than inventing a heap value in a browser without it; the zero deltas
above are observed evidence for this browser/run, not a proof that no possible
long-lived leak exists.

## Duplicate-resource audit

| Resource class | Owner and result |
|---|---|
| Global interaction listeners | `canvas-app-interaction.js`: `dragend`, `drop`, `paste`, one `blur`; cleanup shares the global listener rather than adding one per node. |
| Canvas metadata listeners | `canvas-app-records.js`: one `mousedown`, one consolidated resize lifecycle, and one theme callback. |
| Preview/compare pointers | `canvas-app-output-ui.js`: one guarded `mousemove`/`mouseup` pair; element initialization is idempotent. Touch remains a separate touch lifecycle. |
| Repeating remote polling | `canvas-remote-sync.js`: one guarded interval per controller; repeated `start()` and `stop()` are idempotent. |
| Output polling | `canvas-app-state.js`: one interval and cleanup when no pending output remains. |
| Observers | No `MutationObserver`, `ResizeObserver`, or `IntersectionObserver` constructor in the native Canvas application modules. |

The focused behavior suite includes explicit pointer-pair and remote-sync
idempotence tests. Combined with the two live browser rerender observations,
this closes the DOM/listener/timer/observer/heap inspection required by Gate K.

## Reproduction

Start the application against a disposable database and open, once for each
prepared 100/300-node Canvas id:

```text
/static/canvas-performance-harness.html?id=<canvas-id>&expected=<100-or-300>&interactions=1&memory_cycles=10
```

The result must show the expected node count, ten render passes,
`memory_dom_delta=0`, `memory_delta_bytes=0` when Chromium exposes heap data,
and `interaction_result=PASS`.
