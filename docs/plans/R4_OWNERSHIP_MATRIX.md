# R4 Unified Canvas — Runtime Ownership Matrix

> 本文件由 Codex 在本地项目执行 R4 时持续维护。
>
> 目标不是统计 shared helper，而是确认每一项产品 Runtime responsibility 的唯一 Owner。

## 状态定义

```text
UNIFIED      = Unified runtime 已拥有完整产品责任
PARTIAL      = 有 shared seam/helper，但 Legacy 仍拥有主流程
CLASSIC      = Classic 独立拥有
SMART        = Smart 独立拥有
COMPAT_ONLY  = 仅 Legacy compatibility 仍需要
REMOVE       = 可删除/待删除
```

---

## Ownership Matrix

| Responsibility | Classic | Smart | Unified | Status | Final owner | Required action | Evidence |
|---|---|---|---|---|---|---|---|
| Canvas entry | compatibility handoff | compatibility page | `canvas.html` | PARTIAL | Unified | Remove retained Smart deep-link handoff after Smart record rendering is native. | `canvas-entry-compatibility.js`; status U6 |
| Canvas persistence | adapter client | adapter client | SQLite `CanvasRecord` | UNIFIED | Unified | Keep Legacy JSON only as import/rollback; repository selection goes only through the explicit authority policy seam. | status R3/R4 acceptance; R4-03 split-brain guard |
| revision/CAS | none | none | API/application service; canonical transport + browser save client read/increment/409 logical revision | UNIFIED | Unified | Keep conflict coverage; migrate remote-sync/polling callers onto the revision (R4-07). | `tests/test_canvas_nodes_runtime.py`; `tests/test_canonical_canvas_api.py`; `tests/test_frontend_workbench_modules.py` |
| remote/version polling | interval/merge policy; revision-ordered version probes on default path | interval/merge policy; revision-ordered version probes on default path | transport-neutral coordinator with revision ordering (timestamp fallback) | PARTIAL | Unified | Move polling policy/state into the product runtime. | `canvas-remote-sync.js`; save/merge characterization below |
| viewport state | page load/swap adopt through one seam; interaction commits and mirror read from runtime | page load/swap adopt through one seam; interaction commits and mirror read from runtime | `CanvasRuntime` viewport authority with adapter adopt/reset seam | PARTIAL | Unified | Migrate remaining pan/zoom/minimap DOM and persistence lifecycle on top of the authoritative state. | `canvas.js`, `smart-canvas.js`, `runtime-state.js`; canvas-state-swap contract |
| pan | page DOM/save shell; shared viewport pan session on default path | page DOM/save shell; shared viewport pan session on default path | CanvasRuntime command plus shared pan session | PARTIAL | Unified | Migrate remaining DOM/persistence lifecycle. | `runtime-state.js`; pan-session contract |
| zoom | page preview/minimap shell; shared wheel-scale, centering and default preview-exit commits | page preview/minimap shell; shared wheel-scale, centering and default preview-exit commits | CanvasRuntime command plus shared viewport policy | PARTIAL | Unified | Migrate remaining DOM/minimap/persistence lifecycle. | `runtime-state.js`; viewport interaction contracts |
| semantic zoom | adapter enablement/iteration; shared DOM application on default path | adapter enablement/iteration; shared DOM application on default path | shared policy plus `WorkbenchSemanticZoomApply` indicator/presentation apply+reset owner | PARTIAL | Unified | Move remaining enablement/call timing with renderer ownership. | `semantic-zoom.js`; `semantic-zoom-apply.js` |
| selection | page state machine, except NodeShell and box-selection completion | page state machine, except NodeShell/box completion, media-thumbnail, upload-target and group-menu selection | runtime command primitive plus migrated completion transitions | PARTIAL | Unified | Migrate remaining selection lifecycle. | `runtime-state.js`; NodeShell/box/media-thumbnail/upload-target/group-menu contracts |
| multi-selection | page state machine | page state machine | runtime command primitive | PARTIAL | Unified | Migrate selection lifecycle. | same |
| drag | adapter collection/product semantics; shared drag session on default path | adapter collection/product semantics; shared drag session on default path | NodeShell intent plus `createNodeDragSession` position projection | PARTIAL | Unified | Migrate remaining drag commit/DOM lifecycle and group move. | `runtime-state.js`; NodeShell intent adapters; drag-session contract |
| resize | adapter clamps/product branches; shared resize proposal on default path | adapter clamps/product branches; shared resize proposal on default path | NodeShell intent plus `createNodeResizeSession` size proposal | PARTIAL | Unified | Migrate remaining resize commit/size-mutation lifecycle. | `runtime-state.js`; NodeShell intent adapters; resize-session contract |
| keyboard handling | page handlers | page handlers | editable-target helper | PARTIAL | Unified | Migrate key command lifecycle. | `interaction-targets.js` |
| connection start | page port drag | page port drag | shared command/geometry | PARTIAL | Unified | Migrate port-drag lifecycle. | `graph-interaction.js` |
| connection hover | page hover logic | page hover logic | compatibility helper | PARTIAL | Unified | Migrate hover lifecycle. | status U2 |
| port compatibility | adapter invocation | adapter invocation | shared compatibility contract | PARTIAL | Unified | Route one interaction runtime through it. | `port-compatibility.js` |
| connection mutation | GraphMutationService/API for supported connected Group/Image/Prompt/default Loop creation; page mutation otherwise | GraphMutationService/API for supported connected creation; page mutation otherwise | GraphMutationService/API available | PARTIAL | Unified | Migrate normal connect to service. | graph API tests; save/merge characterization below records the side-effect blocker |
| graph geometry | adapter invocation | adapter invocation | shared geometry algorithms | PARTIAL | Unified | Move graph lifecycle owner. | `graph-geometry.js` |
| group membership | adapter mutation | adapter mutation | shared membership algorithms | PARTIAL | Unified | Migrate group interaction owner. | `group-membership.js` |
| group move | page behavior | page behavior | shared `createNodeDragSession` position projection available | CLASSIC/SMART | Unified | Migrate onto the shared drag session. | `runtime-state.js`; adapter drag code |
| group render | Classic DOM | Smart DOM | partial NodeShell adapter | PARTIAL | Unified | Finish shared renderer before page deletion. | NodeShell mounts |
| node shell | adapter supplies records/intent | adapter supplies records/intent | NodeShell/host | PARTIAL | Unified | Make Unified renderer select and mount all normal cards. | `unified-render-host.js` |
| renderer resolution | Classic policy projection | Smart policy projection | RendererRegistry/host plus RendererAdmission | PARTIAL | Unified | Unified evaluates declared admission; retain page product policy until card parity is explicit. | `renderer-admission.js`; frontend renderer-admission contract |
| generic node rendering | Legacy DOM | Legacy DOM | lossless Legacy renderer | PARTIAL | Unified | Migrate product-relevant card renderers. | `legacy-renderer.js` |
| media rendering | adapter mount/lifecycle | adapter mount/lifecycle | MediaRenderer | PARTIAL | Unified | Move mount/lifecycle ownership. | `media-renderer.js` |
| media lifecycle | adapter re-render/transplant | adapter re-render/transplant | playback helpers | PARTIAL | Unified | Move re-render lifecycle. | `media-playback-state.js` |
| media playback preservation | adapter invocation | adapter invocation | shared state contract | PARTIAL | Unified | Fold into Unified media lifecycle. | `media-playback-state.js` |
| creation catalog | menu adapter | menu adapter | command/catalog definitions | PARTIAL | Unified | Replace page constructors for normal creation. | `command-registry.js` |
| node creation | fallback constructors for unsupported/historical and file-drop paths; shared top-level/connected result commits | fallback constructors for unsupported/historical and file-drop paths; shared top-level/connected result commits | NodeCreationService/GraphMutationService APIs plus shared node/graph result commits | PARTIAL | Unified | Migrate file-drop lifecycle and remaining adapter request projection; retain only bounded compatibility. | `node-creation-client.js`; default-on/Smart-shape/node-and-graph-result contracts |
| node deletion | versioned mutation for standalone blank Image/Prompt/default Loop/empty Output/empty Group; compatibility for configured/content/connected/group-member/other nodes | versioned mutation for standalone blank Smart Image/Prompt/empty Smart Group/default Smart Loop; compatibility for media/group/history/dependent nodes | NodeMutationService/API | PARTIAL | Unified | Migrate remaining deletion contracts only after group/media parity is explicit. | Canvas-node route tests; Classic/Smart versioned-delete contracts |
| node mutation | versioned position update for standalone blank Image/Prompt/default Loop/empty Output/empty Group; compatibility for configured/richer/group-member moves/edits | versioned position update for standalone blank Smart Image/Prompt/empty Smart Group/default Smart Loop; compatibility for richer moves/edits | NodeMutationService/API with backend blank-shape enforcement | PARTIAL | Unified | Migrate resize/group/media and other edit contracts only after parity is explicit. | Canvas-node route tests; Classic/Smart versioned-position contracts; backend unsupported-shape rejection contract |
| context-menu creation | fallback constructors for unsupported/group-member paths; shared top-level and connected result commits | fallback constructors for group-member paths; shared top-level and connected result commits | catalog/API plus shared node/graph result commit for migrated top-level and connected creation | PARTIAL | Unified | Centralize remaining page request projection; retain only bounded compatibility. | `node-creation-client.js`; node-and-graph-result contract |
| file-drop creation | adapter media/layout/save; shared DataTransfer and upload transport | adapter media/layout/save; shared DataTransfer and upload transport | shared DataTransfer traversal/payload resolution/multipart upload; adapter-owned result materialization | PARTIAL | Unified | Migrate result materialization only after media/group parity is explicit. | `media-drop-payload.js`; payload-and-upload contract |
| clipboard copy | adapter selection/UI | adapter selection/UI | graph fragment + clipboard helper | PARTIAL | Unified | Move selection/UI lifecycle. | `canvas-clipboard.js` |
| clipboard paste | adapter placement/UI | adapter placement/UI | graph fragment + clipboard helper | PARTIAL | Unified | Move placement/UI lifecycle. | `canvas-graph-fragment.js` |
| selected subgraph | adapter selection | adapter selection | graph fragment | PARTIAL | Unified | Move selection lifecycle. | same |
| workflow import | adapter format/UI | adapter format/UI | transfer client + graph fragment | PARTIAL | Unified | Retain format compatibility; migrate product flow. | `workflow-transfer-client.js` |
| workflow export | adapter format/UI | adapter format/UI | transfer client | PARTIAL | Unified | Retain format compatibility; migrate product flow. | same |
| result normalization | Classic traversal policy | Smart traversal policy | shared normalizer | PARTIAL | compatibility until R8 | Keep provider behavior; continue compatibility-only decoupling. | `media-result-normalizer.js` |
| result placement | adapter behavior | adapter behavior | generation intent seam | PARTIAL | compatibility seam | Do not introduce R8 executor runtime. | `generation-intent.js` |
| execution trigger | adapter/provider behavior | adapter/provider behavior | none | CLASSIC/SMART | compatibility until R8 | Keep compatibility-only in R4. | adapters |
| minimap | page DOM/event/save shell; shared pointer projection and world-point viewport centering on default path | page DOM/event/save shell; shared pointer projection and world-point viewport centering on default path | CanvasRuntime command plus shared minimap projection/viewport-centering policy | PARTIAL | Unified | Migrate remaining render/persistence lifecycle. | `runtime-state.js`; minimap interaction contract |
| screen-space controls | n/a | Smart application | shared policy | PARTIAL | Unified | Move DOM application with renderer ownership. | `screen-space-controls.js` |
| normal navigation | retained entry adapter | retained entry adapter | normal URL resolver | PARTIAL | Unified | Remove Smart branch when records render natively. | `canvas-entry-compatibility.js` |
| Smart handoff | initiates retained handoff | destination runtime | compatibility module | COMPAT_ONLY | REMOVE | Remove only after Smart product runtime is retired. | status U6/U7 |
| Classic product runtime | full adapter | n/a | partial shared seams | CLASSIC | REMOVE | Migrate interaction, creation and render lifecycle. | `canvas.js` |
| Smart product runtime | n/a | full adapter | partial shared seams | SMART | REMOVE | Migrate Composer, group/media lifecycle, interaction and creation. | `smart-canvas.js` |

---

# Legacy Capability Review

## Classic-only

| Capability | Keep/Migrate/Compat/Remove | Target | Evidence |
|---|---|---|---|
| Legacy provider/execution cards | Compat | bounded Legacy renderer/execution seam | provider behavior unchanged; R8 owns runtime replacement |
| Classic upload/file-drop | Migrate | Unified creation/mutation runtime | direct local node construction remains page-owned |

## Smart-only

| Capability | Keep/Migrate/Compat/Remove | Target | Evidence |
|---|---|---|---|
| Composer | Migrate | Unified card/render and creation runtime | `updateComposer()` remains Smart-page-owned |
| Smart group behavior | Migrate | Unified interaction/renderer | Smart membership/move/resize policy remains page-owned |
| upload | Migrate | Unified creation/mutation runtime | Smart direct `createNode()` remains page-owned |
| video workflow | Compat | Legacy renderer/execution seam | R8 owns runtime replacement |
| Smart media layout | Migrate | Unified media renderer lifecycle | layout math is shared; DOM lifecycle remains Smart-owned |
| MiniMax compatibility | Compat | Legacy renderer/execution seam | must remain readable; not an R8 implementation |

---

# Feature Flag Lifecycle

| Flag | Introduced | Purpose | Current default | Removal gate | Status |
|---|---|---|---|---|---|
| versioned_nodes | R3/R4 | canonical normal blank creation rollback | on | R4 PASS | `versioned_nodes=0` retains adapter constructors during U7 |
| unified_canvas | R2/R4 | bounded U7 rollback | on | R4 PASS | retain until one runtime evidence |
| node_shell | R3/R4 | bounded U7 rollback | on | R4 PASS | retain until one renderer evidence |
| legacy_renderer | R3/R4 | bounded Legacy payload renderer rollback | on | R4 PASS | retain until migrated card parity |
| media_renderer | R3/R4 | bounded media renderer rollback | on | R4 PASS | retain until lifecycle parity |
| semantic_zoom | R3/R4 | bounded semantic zoom rollback | on | R4 PASS | retain until renderer ownership |
| screen_space_controls | R3/R4 | bounded Smart controls rollback | on | R4 PASS | retain until renderer ownership |

---

# Acceptance Evidence

## Unit / contract

```text
2026-09-05 inventory baseline: python -m unittest tests.test_frontend_workbench_modules
PASS (76 tests). This characterizes shared-module seams only; it is not R4 Gate evidence.

2026-09-05 normal blank-creation authority cutover: loopback defaults to the existing `NodeCreationService` route for supported Classic and Smart top-level commands; `versioned_nodes=0` is the bounded rollback. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest tests.test_frontend_workbench_modules tests.test_canvas_nodes_runtime`: PASS (89 tests).

2026-09-05 NodeShell selection ownership: Classic NodeShell select/focus/menu now dispatches through `CanvasRuntime` on the default path, with local state only as the `unified_canvas=0` rollback. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -q`: PASS (241 tests).

2026-09-05 box-selection ownership: both adapters retain their existing coordinate/overlap policy, then commit completed selection through `CanvasRuntime` on the default path; `unified_canvas=0` retains the local state fallback. Focused API/frontend regression: PASS (90 tests); full regression: PASS (242 tests).

2026-09-05 Classic standalone blank-Image deletion: the default loopback path calls `NodeMutationService`; successful API response projects the revision locally, while stale/rejected requests do not fall through to a raw adapter save. Focused regression: PASS (103 tests); full regression: PASS (243 tests).

2026-09-06 Classic standalone blank-Image position: a single non-Alt, non-grouped blank Image drag calls `NodeMutationService` on completion; stale/rejected writes restore its original visual position and do not issue a raw Canvas save. Focused regression: PASS (104 tests); full regression: PASS (244 tests).

2026-09-06 Smart standalone blank-Image deletion: the default loopback path calls `NodeMutationService` only for an ungrouped, media-free, idle `smart-image` without history or dependent input references. The repository preserves Smart's `title` field; stale/rejected requests do not fall through to a raw adapter save. Focused regression: PASS (106 tests); full regression: PASS (246 tests).

2026-09-06 Smart standalone blank-Image position: a single non-Alt/non-Ctrl, non-thumbnail-drag, non-grouped blank Smart Image drag calls `NodeMutationService` on completion; rejected or stale writes restore its original visual position and do not issue a raw Canvas save. Focused regression: PASS (107 tests); full regression: PASS (247 tests).

2026-09-06 Smart blank-Image creation projection: the Legacy persistence adapter writes a NodeCreationService-created Image as `smart-image` with Smart `title` and empty `images` when the target Canvas is Smart. Reload no longer depends on local type projection for this normal creation path. Focused regression: PASS (108 tests); full regression: PASS (248 tests).

2026-09-06 Smart connected creation transaction: supported connected Image/Group/Prompt/Loop/MiniMax creation persists its new node, edge, and target `inputNodeIds` in the one GraphMutationService transaction. The local projection no longer schedules a raw Canvas save after that successful API response. Focused regression: PASS (104 tests); full regression: PASS (248 tests).

2026-09-06 Classic connected blank-Image creation: the normal supported Classic Image connection now creates the blank Image and edge through GraphMutationService, using the same transaction-persisted input relationship and no raw Canvas save. Focused regression: PASS (106 tests); full regression: PASS (250 tests).

2026-09-06 Smart Canvas-node route coverage: the mounted local API creates the durable Smart Image shape and updates/deletes it through the same expected-revision contract. Focused regression: PASS (116 tests); full regression: PASS (252 tests).

2026-09-06 shared pan interaction: Classic and Smart default paths delegate pointer delta, viewport origin and their preserved movement threshold (Classic Euclidean, Smart Manhattan) to `WorkbenchCanvasRuntime.createViewportPanSession`; `unified_canvas=0` retains the page-local calculation. Focused regression: PASS (103 tests); full regression: PASS (253 tests).

2026-09-06 shared zoom interaction: Classic and Smart default wheel paths delegate scale calculation to `WorkbenchCanvasRuntime.viewportScaleForWheel`, preserving Classic's step factors and Smart's clamped exponential policy; `unified_canvas=0` retains the page-local formula. Focused regression: PASS (98 tests); full regression: PASS (253 tests).

2026-09-06 minimap viewport-centering interaction: Classic and Smart default minimap paths delegate the world-point-to-centered-viewport calculation and `CanvasRuntime` viewport command to `WorkbenchCanvasRuntime.viewportCenteredOnWorldPoint`; their minimap DOM, event binding and save lifecycles remain page-owned, while `unified_canvas=0` retains the page-local formula. Focused regression: PASS (98 tests); full regression: PASS (253 tests).

2026-09-06 minimap pointer projection: Classic and Smart default minimap paths delegate client-pointer-to-world-point projection to `WorkbenchCanvasRuntime.worldPointFromMinimapPointer`, retaining each adapter's bounds, offsets and scale inputs; their minimap DOM, event binding and save lifecycles remain page-owned, while `unified_canvas=0` retains the page-local formula. Focused regression: PASS (98 tests); full regression: PASS (253 tests).

2026-09-06 fitted/recovered viewport commit: Classic's shared recovery fit and Smart's normal, corrupt-camera and visible-node recovery fits now dispatch their resulting viewport through CanvasRuntime by default. Adapter-specific fit inputs/fallbacks, recovery eligibility, DOM application and persistence remain page-owned; `unified_canvas=0` retains direct assignment. Focused regression: PASS (98 tests); full regression: PASS (253 tests).

2026-09-06 zoom-preview exit viewport commit: Classic and Smart default preview exits, including readable node focus, compute their retained preview-specific scale and then restore/center through CanvasRuntime. Preview mode, adapter scale rules, DOM application and persistence remain page-owned; `unified_canvas=0` retains direct assignment. Focused regression: PASS (98 tests); full regression: PASS (253 tests).

2026-09-06 Smart media-thumbnail selection: Smart's media thumbnail single-click and preview/double-click selection paths now commit their node selection through `applySmartNodeSelection` and CanvasRuntime by default. Smart retains its media focal item, preview, Composer and video behavior; `unified_canvas=0` retains direct selection state. Focused regression: PASS (98 tests); full regression: PASS (253 tests).

2026-09-06 Smart upload-target selection: Smart's node upload entry now commits its target-node selection through `applySmartNodeSelection` and CanvasRuntime by default before opening the existing file picker. Upload target, file picker, media focal state and Composer behavior remain adapter-owned; `unified_canvas=0` retains direct selection state. Focused regression: PASS (98 tests); full regression: PASS (253 tests).

2026-09-06 Smart group-menu selection: Smart's group right-click menu now commits its target-node selection through `applySmartNodeSelection` and CanvasRuntime by default before opening the existing group menu. Group/menu/creation behavior remains adapter-owned; `unified_canvas=0` retains direct selection state. Focused regression: PASS (98 tests); full regression: PASS (253 tests).

2026-09-06 blank-Image creation result commit: Classic and Smart default blank-Image menu creation now route the API success result through `WorkbenchNodeClient.applyCreationResult`, which appends the projected node, records the undo snapshot and applies the authoritative Canvas revision. Adapters retain their distinct node shape, Smart selection and render feedback; unsupported/group-member creation remains compatibility. Focused regression: PASS (99 tests); full regression: PASS (254 tests).

2026-09-06 blank-Prompt creation result commit: Classic and Smart default blank-Prompt menu creation now use the same `WorkbenchNodeClient.applyCreationResult` commit. The shared path owns append/undo/revision; adapters retain their Prompt card shape, Smart selection and render feedback, while connected/group-member and unsupported creation remain compatibility. Focused regression: PASS (99 tests); full regression: PASS (254 tests).

2026-09-06 blank-Loop creation result commit: Classic and Smart default blank-Loop menu creation now use that same shared success-result commit. The shared path owns append/undo/revision; adapters retain Loop card shape, Smart selection and render feedback, while connected/group-member and unsupported creation remain compatibility. Focused regression: PASS (99 tests); full regression: PASS (254 tests).

2026-09-06 blank-Group creation result commit: Classic and Smart default blank-Group menu creation now use that same shared success-result commit. The shared path owns append/undo/revision; adapters retain their group card shape, Smart selection and render feedback, while group-member editing, connected creation and media behavior remain compatibility. Focused regression: PASS (99 tests); full regression: PASS (254 tests).

2026-09-06 Classic blank-Output creation result commit: Classic default blank-Output menu creation now uses `WorkbenchNodeClient.applyCreationResult`. The shared path owns append/undo/revision; Classic retains Output card shape and render feedback, while connected creation and unsupported paths remain compatibility. Focused regression: PASS (99 tests); full regression: PASS (254 tests).

2026-09-06 Smart blank-MiniMax creation result commit: Smart default MiniMax menu creation now uses `WorkbenchNodeClient.applyCreationResult`. Its adapter-owned node projection still initializes the existing timeline segment before the shared append/undo/revision/selection commit; all MiniMax media, timeline and execution interaction remains compatibility. Focused regression: PASS (99 tests); full regression: PASS (254 tests).

2026-09-06 connected creation result commit: Classic connected Group/Image and Smart connected Group/Prompt/Loop/Image/MiniMax now route their already-atomic GraphMutationService result through `WorkbenchNodeClient.applyGraphCreationResult`. The shared path validates/projects the node and edge, commits node/edge/undo/revision/selection, and (where requested) updates the graph's generic input relationship. Adapters retain only card projection, Classic post-connection sync, and Smart product feedback; file-drop, unsupported and group-member creation remain compatibility. Focused regression: PASS (99 tests); full regression: PASS (254 tests).

2026-09-06 connected-result browser read smoke: local `127.0.0.1:3000` loaded the existing Classic fixture with six nodes and `100% · 完整 · 6 节点`, and the historical Smart fixture with Group/Input/Output ports, upload and Prompt cards and `65% · 摘要 · 2 节点`. The check was read-only: no creation, save or execution was invoked.

2026-09-06 file-drop traversal ownership: Classic and Smart now delegate DataTransfer directory traversal and supported-file filtering to `WorkbenchCanvasMediaDrop`. Their upload endpoints, media type handling, target selection, group layout and Canvas save scheduling remain adapter-owned. Focused regression: PASS (100 tests); full regression: PASS (255 tests).

2026-09-06 file-drop browser read smoke: local `127.0.0.1:3000` loaded both existing fixtures with the new media-drop runtime script order. Classic retained six ready cards and `100% · 完整 · 6 节点`; Smart retained Composer and `65% · 摘要 · 2 节点`. The check was read-only: no upload, creation, save or execution was invoked.

2026-09-06 file-drop payload resolution: Classic and Smart now delegate files/directories/local paths/remote URL payload precedence to `WorkbenchCanvasMediaDrop`; Classic retains its existing directory-fallback eligibility. Upload API, media policy, target selection, group layout and Canvas save remain adapter-owned. Focused regression: PASS (100 tests); full regression: PASS (255 tests).

2026-09-06 file-drop payload browser read smoke: local `127.0.0.1:3000` loaded both fixtures using the new payload-resolution script version. Classic retained its six ready cards and `100% · 完整 · 6 节点`; Smart retained Composer, Group/Input/Output, upload and Prompt cards, and `65% · 摘要 · 2 节点`. The check was read-only: no upload, creation, save or execution was invoked.

2026-09-06 file-drop upload transport: Classic and Smart now delegate `/api/ai/upload` multipart transport and response file-list extraction to `WorkbenchCanvasMediaDrop`. Classic retains its existing JSON failure semantics; Smart retains named multipart files, readable error text and media-kind projection. Adapter-owned media handling, target selection, group layout and Canvas save remain unchanged. Focused regression: PASS (100 tests); full regression: PASS (255 tests).

2026-09-06 file-drop upload browser read smoke: local `127.0.0.1:3000` loaded both fixtures using the shared upload-transport script version. Classic retained its six ready cards and `100% · 完整 · 6 节点`; Smart retained Composer, Group/Input/Output, upload and Prompt cards, and `65% · 摘要 · 2 节点`. The check was read-only: no upload, creation, save or execution was invoked.

2026-09-06 Classic standalone blank-Prompt mutation: the Legacy mutation repository now accepts the durable `prompt` shape. A Classic Prompt with empty text, no links and no group membership updates position or deletes through NodeMutationService; rejected writes do not fall through to raw save. Content-bearing, connected or grouped Prompts remain compatibility. Focused regression: PASS (116 tests); full regression: PASS (257 tests).

2026-09-06 Classic blank-Prompt browser read smoke: local `127.0.0.1:3000` loaded the existing Classic fixture using the new mutation script version, retaining six ready cards and `100% · 完整 · 6 节点`. The check was read-only: no Prompt move/delete, save or execution was invoked.

2026-09-06 Classic standalone default-Loop mutation: the Legacy mutation repository now accepts the durable `loop` shape. Only a Classic Loop with its default serial/count/start/batch configuration, no prompt or media inputs, no links and no group membership updates position or deletes through NodeMutationService; rejected writes do not fall through to raw save. Configured, connected or grouped Loops remain compatibility. Focused regression: PASS (118 tests); full regression: PASS (259 tests).

2026-09-06 Classic standalone empty-Output mutation: the Legacy mutation repository now accepts the durable `output` shape. Only a Classic Output with no images, pending tasks, comparison state, links or group membership updates position or deletes through NodeMutationService; rejected writes do not fall through to raw save. Output clearing, execution results, configured, connected or grouped Outputs remain compatibility. Focused regression: PASS (120 tests); full regression: PASS (261 tests).

2026-09-06 Classic standalone empty-Group mutation: the Legacy mutation repository now accepts the durable `group` shape. Only a Classic Group with no members, links or nesting membership updates position or deletes through NodeMutationService; rejected writes do not fall through to raw save. Group-member movement, membership changes, resize and graph behavior remain compatibility. Focused regression: PASS (122 tests); full regression: PASS (263 tests).

2026-09-06 Smart standalone empty-Group mutation: the Legacy mutation repository now accepts the durable `smart-group` shape. Only a Smart Group with no members, media, input references, links or nesting membership updates position or deletes through NodeMutationService; rejected writes do not fall through to raw save. Smart group media, history, membership, resize and Composer behavior remain compatibility. Focused regression: PASS (124 tests); full regression: PASS (265 tests).

2026-09-06 Smart standalone default-Loop mutation: the Legacy mutation repository now accepts the durable `smart-loop` shape. Only a single-round serial Smart Loop with no prompt/image input, variable prompt, input references, links or group membership updates position or deletes through NodeMutationService; rejected writes do not fall through to raw save. Workflow, connected, grouped and configured Smart Loops remain compatibility. Focused regression: PASS (20 adapter tests); full regression: PASS (266 tests).

2026-09-06 Smart standalone blank-Prompt mutation: the Legacy mutation repository now accepts the durable `smart-prompt` shape. Only a Smart Prompt without text/result, stale-result marker, LLM activation/instruction, attachments, input references, links or group membership updates position or deletes through NodeMutationService; rejected writes do not fall through to raw save. Content-bearing, connected, grouped and configured Prompts remain compatibility. Focused regression: PASS (111 tests); full regression: PASS (272 tests).

2026-09-06 Classic connected blank Prompt/default Loop creation: normal port-menu creation now persists the new node, edge and target input relationship through one GraphMutationService transaction. The page retains only node projection and post-connection compatibility refresh; provider/execution nodes and configured paths remain adapter-owned. Focused API/frontend regression: PASS (16 API tests); full regression: PASS (274 tests).
```

### 2026-09-06 backend mutation safety boundary and canonical data repair

```text
2026-09-06 backend blank-shape mutation boundary: the Legacy mutation repository no longer trusts the
frontend eligibility gate. Inside the same canvas lock that performs the mutation, it now rejects
content-bearing, grouped, history-linked, input-referenced, and (except the characterized Image edge
cleanup) connected nodes for both update and delete with `NodeMutationUnsupportedError`
(`unsupported_node_shape`, HTTP 422), while stale revisions still fail with 409 and supported blank
shapes keep their existing contracts. New adapter tests cover rich update/delete rejection, group-member
rejection, dependent-input-reference rejection, connected-Prompt rejection, adapter-level stale
rejection, and unchanged blank contracts; a route test pins the 422 mapping and the unchanged payload.
Focused regression: PASS; full regression: PASS (280 tests). Python AST (33 files) and JS syntax checks
pass. This closes the audited gap where a direct API caller could delete a group-linked, referenced, or
content-bearing node because the repository gated only on `node.type`.

2026-09-06 canonical data-integrity repair: a legacy-routed (rollback) server session on 2026-09-06
morning produced a verified split-brain — one orphan Canvas (`b489247e…`, created 07:41 through the
versioned API with JSONL audit evidence) existed only in Legacy JSON, sixteen active Canvases carried
list-board position drift, and the SQLite `canvases` table contained a `revision`/`baseline` row leaked
by an older `tests/test_repository_baseline.py` run before that test gained its routing patch. Repair:
pre-repair snapshot `data/canvas-source-backups/r4-repair-20260906T091748/` (23 payload files plus the
purged row's recovered JSON), the stale `7ed83bf5…` rollback file was refreshed from its newer canonical
payload, the orphan and board-only drifts were converged through the tested migration import path
(`tools/migrate_project_canvas.py`), and the test-artifact row was purged through
`purge_canvas_payload` with audit. Post-repair report `data/r4-repair-migration-report.json`: authority
`sqlite`, 23 imported, 0 skipped, 23 comparisons, 0 differences; SQLite rows 23 == Legacy files 23 with
zero divergent payloads and the orphan's two nodes present. R4 Gate items
`source_count == canonical_count` / `skipped == 0` / `differences == 0` are re-established as of this
repair; the general prohibition on running legacy-routed servers while SQLite authority is active is
recorded in CURRENT_EXECUTION_STATUS.md. An isolated restart read on `127.0.0.1:3012` then listed 17
active Canvases with no phantom `baseline` row, read the imported orphan with its two nodes and merged
board position, and read the repaired Classic record's canonical metadata; the temporary service was
stopped after the read-only check.

2026-09-06 SQLite-path mutation boundary coverage: the same blank-shape update/delete contracts,
`unsupported_node_shape` rejection (content-bearing and grouped nodes), and stale-revision rejection now
have focused tests through the `SqliteCanvasCompatibilityRepository`, pinning that the backend boundary
holds identically on the canonical store rather than only on the Legacy JSON path. Focused regression:
PASS (8 tests); full regression: PASS (283 tests).

Assessed and deferred (2026-09-06): normal-connect service migration remains blocked because both
adapters couple the edge commit with page-owned side effects on the same raw save (Smart mutates target
execution config and `inputNodeIds`; Classic adds group membership and generator/output sync), so a
service split today would force double writes or a premature rich-mutation API. Keyboard command
lifecycle migration is likewise deferred: the two adapters own genuinely different command maps and
selection models, so unification requires the command-registry step, not a bounded move. Polling
ownership assessment (2026-09-06, after save-coordinator units 1–4): `WorkbenchCanvasRemoteSync` already
owns the interval timer, in-flight checking guard, version comparison and metadata fetch for both
adapters; the remaining divergence is policy-only — Classic/Smart keep their characterized intervalMs
(2500/8000), eligibility predicates (apply-in-progress/hidden vs in-flight/drag/selection) and `onNewer`
apply actions (replace vs merge), which are the same adapter-owned conflict/apply policies recorded for
unit (4) and depend on the viewport/selection state rows. No bounded migration remains in the polling
row until those state rows move; no ownership was reduced by these assessments; they are recorded to
prevent re-deriving the same blockers.

2026-09-06 canvas authority split-brain guard (R4-03): Canvas repository selection moved from the
bare routing-flag branch to one explicit authority policy seam — `workbench/application/
canvas_authority_policy.py` (`resolve_canvas_authority` plus a tolerant read-only `authority_state`
reader). `main.canvas_repository()` now consults the policy on every call, and startup
(`startup_event`, the module-level node-API wiring, and the `__main__` entry) fails fast with
`CanvasAuthoritySplitBrainError` when SQLite authority is active while canonical routing is
disabled, instead of silently routing writable traffic to Legacy JSON — the exact legacy-routed
hazard behind the morning split-brain. Recovery remains explicit: legacy routing still works when
authority is `legacy_json` or unavailable (missing/temporary database), and the migration
import/compare tool plus the tested lossless rollback export are untouched. Five legacy-routed test
fixtures gained a temporary-database patch so simulated legacy routing no longer implies the real
authority state. Live check: default routing returns `SqliteCanvasCompatibilityRepository` over 23
payloads; with `WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED=false` the process refuses with exit 1
and the database stays byte-identical (sha256 `3cca0054…`). Focused regression: PASS (11 new
tests); full regression: PASS (308 tests).

2026-09-06 canonical Canvas transport API (R4-05): logical-revision transport
ownership moved from the legacy-shaped `/api/canvases` endpoints to a canonical
seam — `workbench/api/canvases.py` (`/api/v1/canvases/{canvas_id}` GET/PUT,
registered inside the loopback-gated versioned API block). GET returns the
payload plus `revision`/`updated_at`/`deleted` from the canonical record; PUT
performs full-payload CAS via `replace_canvas_payload` with `expected_revision`;
stale writes return explicit 409 conflict information
(`expected_revision`/`current_revision`/`current_updated_at`); 503 with an
explicit error while authority is not `sqlite` (no silent legacy fallback); 404
for unknown canvases; 403 on authorization failure. The legacy transport keeps
its characterized shape (no `revision` key; `base_updated_at` semantics) and
remains the compatibility path until browser callers migrate (R4-06/R4-07).
Ownership matrix revision/CAS row updated. Focused regression: PASS (6 new
tests); full regression: PASS (319 tests).

2026-09-06 browser persistence uses logical revision (R4-06): normal browser
save concurrency moved from the updated_at/base_updated_at cursor to the
logical Canvas revision inside one bounded seam — the shared persistence
client (`canvas-persistence-client.js`). It now owns a revision cursor fed by
canonical load/save responses and by `adoptRevision` after versioned writes;
`savingCanvasNow`-style saves go canonical-first (`PUT /api/v1/canvases/{id}`
with `expected_revision` and the payload minus transport fields) and the client
falls back to the legacy `updated_at` transport only when the canonical API
reports 503 or no revision cursor exists (legacy-loaded state). The canonical
409 conflict now carries the current payload, preserving Classic's
apply-remote and Smart's merge-then-reschedule recovery semantics, and the
canonical PUT stamps `payload.updated_at` server-side so it stays
display/compat metadata only. Adapter save/load handlers are unchanged; the
remote-sync comparison paths (still timestamp-based) belong to R4-07.
Ownership matrix revision/CAS row updated. Focused regression: PASS (4 new
sandbox tests + 1 HTTP round-trip test); full regression: PASS (323 tests).

2026-09-06 remote sync uses revision (R4-07): remote/window version ordering
moved from timestamps to the logical Canvas revision. The canonical transport
gained a lightweight `GET /api/v1/canvases/{id}/meta` probe (revision without
payload) and its successful PUT now relays a `canvas_updated` WebSocket
message carrying `revision` + `client_id` through an injected broadcast (the
manager message shape gained an additive `revision` field; event contract
updated). `WorkbenchCanvasPersistence.metadata()` peeks canonical-first (503 →
legacy `/meta`) and never moves the save cursor; the client exposes
`revisionOf()` as the local baseline. `WorkbenchCanvasRemoteSync.check()` and
`WorkbenchCanvasUpdateMessage.newerForCanvas()` order by revision first with
the timestamp comparison retained as the bounded fallback for revision-less
(legacy) probes. Classic's polling flow is now peek-meta → compare → load →
apply-remote; both adapters feed `currentRevision` baselines. Deterministic
two-window semantics are pinned by sandbox tests: same/older revision never
re-applies even with a newer timestamp, revision-less probes keep timestamp
ordering, and own-client notifications stay filtered. Known limitation: the
node-API revision space still uses the compat updated_at cursor, so a
versioned write interleaved with canonical saves can cost one self-healing
409; unification is deferred. Focused regression: PASS (6 new tests + updated
event contract); full regression: PASS (329 tests).

2026-09-06 Unified RenderRuntime mounted-card lifecycle (R4-09): the render
runtime is now a real lifecycle owner rather than a facade —
`WorkbenchRenderRuntime.create({mount})` holds the per-node-id mounted-handle
registry, destroys the previous handle on same-id remount, destroys and
forgets on unmount, supports ordered batch mounting, and offers unmountAll.
Both adapters inject their existing `UnifiedRenderHost.mountAdapterCard` once
and route every card mount through the runtime; Classic deleteNode unmounts
the deleted node, Smart deleteNode unmounts every removed id (including
history groups), and both canvas loads unmountAll. Wiring contract test pins
one injected host mount per adapter, no remaining direct
`mountAdapterCards(entries)` calls, and script load order
(unified-render-host -> render-runtime -> adapter). Focused regression: PASS
(2 new tests; three mount-wiring assertions updated to the runtime contract);
full regression: PASS (332 tests).

2026-09-06 Group rendering cutover (R4-10): Group is the first family whose
complete mount contract is owned by the Unified RenderRuntime.
`WorkbenchRenderRuntime.mountGroupCard` assembles the group record (legacyNodeView
+ own/member media merged into output_refs), decides media vs legacy content
(`mediaEnabled:false` preserves the rollback path), executes the mount through
the keyed lifecycle, exposes the resolved shell view (`viewState`, `onIntent`)
plus `hasRenderableMedia`/`useLegacyContent` on the frozen result, and supports
an `mountEmptyState` hook for no-media groups. Classic's group branch
(`mountCanvasGroupShell`) and Smart's group batch delegate with only gates,
member-media extraction, intents, and control selectors; Smart's inline
record-selection ternary is gone and the old `smartGroupMediaRecord` remains
only inside the eligibility gate. Create/render/update/move/resize/reload/
delete behavior is unchanged (resize/member-sync/delete paths untouched; the
runtime destroys handles on delete and canvas loads). Focused regression: PASS
(behavioral `mountGroupCard` test + both-adapters cutover contract test); full
regression: PASS (334 tests).

2026-09-06 media rendering cutover (R4-11): media-state projection for
runtime-mounted cards moved from the page render sweeps into the Unified
RenderRuntime. `WorkbenchRenderRuntime.create` accepts `mediaState`
capture/restore callbacks (both adapters inject wrappers over
`WorkbenchCanvasMediaPlaybackState`); `unmount` captures playback state from
the outgoing shell element before destroy and `mount` restores it into the
fresh card, so remounts keep playback continuity without page bookkeeping.
`MediaRenderer` now stamps `dataset.url` on every created element, making
renderer-created media visible to the shared signature; `captureAll`/
`restoreAll` gained an `exclude` selector and both page-level sweeps exclude
`.node-shell-mounted`, so the pages project only the flags-off fallback DOM
while the runtime owns mounted media state. Load/error/select/reload paths
are unchanged (preview fallback, high-res, and versioned media tests pass
as-is). Focused regression: PASS (3 new tests: exclude selector, runtime
remount projection, renderer signature URL); full regression: PASS (337
tests).

2026-09-06 generic legacy card rendering cutover (R4-12): the Classic prompt
family is the first generic family whose cards no longer depend on
pre-rendered page DOM. `static/js/workbench/canvas/prompt-card-renderer.js`
self-registers a `prompt-card` renderer (priority 10) with the exposed
`NodeCardHost.registry`; resolution prefers it over source-payload (0) for
legacy prompt records, so `mountCanvasNodeShellForLegacy` mounts
renderer-owned DOM inside NodeShell with `preserveLegacyContent:false` for
prompts. The page keeps state and services behind rendererOptions callbacks
(`onPromptInput` writes the payload text and schedules save/generator sync,
`onOpenTemplate` opens the template modal, `templateActive` mirrors modal
state, counter limits and scroll binding are injected), and the pre-rendered
prompt markup survives verbatim as the `legacy_renderer=0` fallback
(`legacy_renderer` gate now skips it on the default path). Smart's
composer-owned smart-prompt card is intentionally not migrated. Behavioral
test drives the real NodeCardHost + NodeShell + registry pipeline with a fake
document (renderer id stamping, initial text, counter update, over-limit
class, callbacks, scroll binding); a wiring contract pins load order, the
conditional fallback branch, and the Smart page exclusion. Focused
regression: PASS (2 new tests); full regression: PASS (339 tests).
```

## Rendering ownership map (R4-08 characterization, 2026-09-06)

Pipeline facts (no behavior changed by this card). Both adapters are
throwaway-DOM renderers: every state change rebuilds node cards from HTML
strings, and continuity is preserved by state capture/transplant, not by
keeping DOM alive.

- Classic full reflow `render()` (`canvas.js:6084`): capture output scrolls and
  playback states, remove `.node` children except live-media nodes, rebuild via
  `renderNode` (`canvas.js:6100`), transplant live media (`canvas.js:6047`),
  restore states, rebind preview fallbacks and high-res sync, apply semantic
  zoom. Targeted path: `refreshNodes()` (`canvas.js:6123`, `replaceWith` per
  node) plus the keyed Output diff `refreshOutputNodeContent`
  (`canvas.js:6809`) — the only real targeted DOM updater.
- Smart has one full `render()` (`smart-canvas.js:8998`, one HTML string) plus
  style-only updaters: `updateNodeElementDuringResize` (`smart-canvas.js:7136`),
  `smartMinimaxSyncPlayerDom` (`smart-canvas.js:8128`), `refreshRunTimerPills`
  (`smart-canvas.js:8974`).
- DOM destruction is omission from the next render sweep in both adapters
  (Classic `canvas.js:6093`, Smart `smart-canvas.js:9063`); neither adapter ever
  invokes the mounted-card `destroy()` handle (zero `.destroy()` call sites in
  `canvas.js`/`smart-canvas.js`). Only the Classic LTX timeline editor has
  explicit teardown (`destroyLTXEditor`, `canvas.js:6277`).

| Family | Create | Update | Destroy | Listeners | Media state | Current owner | Target owner |
|---|---|---|---|---|---|---|---|
| Group (Classic `group`/`promptGroup`) | `addGroupNode` C2679 / promptGroup C15344; versioned C2631 | full render; group branch delegates to `mountCanvasGroupShell` C6438 | omission + `deleteNode` C13558 (versioned empty C13826) | body drag/dblclick C6637; shell intents once mounted | member images → runtime-built record | adapter HTML + RenderRuntime group mount (R4-10) | Unified RenderRuntime (card builder + lifecycle); adapter product controls compat |
| Group (Smart `smart-group`) | `createSmartGroupNode` S6844; versioned S1643/S1682 | full render; batch delegates to `mountGroupCard` S1559 | `deleteNode` S10595 (versioned S10784) | dblclick/toolbar S10269/S10327; shell owns ports/resize | member media → runtime-built record | adapter HTML + RenderRuntime group mount (R4-10) | Unified RenderRuntime; Smart group actions compat |
| Image (Classic) | `addImageNode` C2604; versioned C2527 | full render / `refreshNodes` | content-clear C13568 → versioned C13736 / `deleteNode` | body C6522; img guards C6553 | shared primitives; media state projected by the runtime (R4-11) | MediaRenderer DOM + runtime state projection; adapter HTML is flags-off fallback | Unified RenderRuntime; adapter video activation compat |
| Image (Smart `smart-image`) | `createNode` S6749; versioned S1764/S1802 | full render + `measureSmartNodeImages` S9136 | media-clear S10618 → versioned S10761 / `deleteNode` | thumbs/play/drag S10354–10533 | shared primitives; media state projected by the runtime (R4-11) | MediaRenderer DOM + runtime state projection; adapter HTML is flags-off fallback | Unified RenderRuntime; Smart media tools compat |
| Prompt (Classic) | `addPromptNode` C2608; versioned C2554 | renderer-owned DOM via `prompt-card` registry entry (R4-12) | versioned C13760 / `deleteNode` | renderer-bound textarea/template; page callbacks | n/a | `prompt-card` renderer + NodeShell; adapter markup is flags-off fallback | Unified RenderRuntime lifecycle |
| Prompt (Smart) | `createPromptNode` S6761; versioned S1613/S1723 | full render + `bindPromptNodeControls` S9241 | versioned S10820 / `deleteNode` | controls S9242 | n/a | adapter | Unified RenderRuntime lifecycle |
| Loop (Classic) | `addLoopNode` C2612; versioned C2579 | `renderLoopBody` C8127 | versioned C13782 / `deleteNode` | controls C8185 | none owned | adapter | Unified RenderRuntime lifecycle |
| Loop (Smart) | `createLoopNode` S6796; versioned S1629/S1741 | `smartLoopBodyHtml` + bind S9374 | versioned S10806 / `deleteNode` | S9374+ | none owned | adapter | Unified RenderRuntime lifecycle |
| Output (Classic only) | `addOutputNode` C3357; versioned C2655 | keyed grid diff `refreshOutputNodeContent` C6809 / full C14417 | content-clear C13580 → versioned C13804 / `deleteNode` | `bindOutputWrap` C6708 | preview video/audio C14397; scroll capture C6240 | adapter (only targeted DOM diff) | Unified RenderRuntime (diff moves into runtime); item actions compat |
| MiniMax (Classic) | `addMiniMaxNode` C2778 | `renderMiniMaxBody` C9434 | `deleteNode` | in-body | incidental shared playback-state | adapter | Unified RenderRuntime lifecycle |
| MiniMax (Smart) | `createMinimaxNode` S6805; versioned S1657 | in-place `smartMinimaxSyncPlayerDom` S8128 | `deleteNode` S10595 | `bindMinimaxNodeControls` S9522 | adapter player model (playhead/mute/volume) + stage transplant S7379 | adapter player state machine | Unified RenderRuntime lifecycle; player model Smart compat |
| Provider-shaped (Classic llm/generator/midjourney/msgen/video/comfy/rh/ltxDirector) | `addNode` C2516 via menu C3855 | full render per setting; run status `refreshRunNodes` C6155 | `deleteNode` C13558 (+LTX C13561) | per-body; `isNodeControl` C6274 | input refs via shared media-references C3929 | adapter bodies; shell adopts via `mountCanvasNodeShellForLegacy` C6446 | shell/registry shared; bodies stay provider compat |
| Smart legacy skill nodes | composer/creation flows | full render + per-family binders | `deleteNode` S10595 | per-family binders | n/a | adapter bodies adopted losslessly S1589 | Unified RenderRuntime lifecycle; bodies compat |

Legacy DOM adoption paths (all funnel through `UnifiedRenderHost`):
1. Classic Image/Group media cards: `mountCanvasNodeShellForMedia` (C6420) →
   `mountAdapterCard` (C6426); MediaRenderer when `canRender`, else adopted
   legacy content preserved or empty-group placeholder.
2. Classic Prompt/Loop/Output/LLM/Generator/MJ/MsGen/Video/Comfy/RH/LTX/
   MiniMax/PromptGroup: `mountCanvasNodeShellForLegacy` (C6446) with
   `preserveLegacyContent`; adapter head/ports/resize stripped post-mount
   (`CANVAS_NODE_SHELL_LEGACY_CONTROLS` C6416).
3. Classic media-without-shell (`node_shell=0`): `mountCanvasMediaRenderer`
   (C6459) → `mountAdapterContent`.
4. Smart Group batch: `mountNodeShellForSmartGroups` (S1549) — port/resize
   controls removed BEFORE mount so adapter handlers go dead first.
5. Smart Image batch: `mountNodeShellForSmartImages` (S1570).
6. Smart legacy skill nodes: `mountNodeShellForSmartLegacyNodes` (S1589) with
   `preserveLegacyContent` — listeners and form state stay adapter-owned.

Shared seams (load-order stable on both pages): renderer-registry (media
priority 100 > source-payload 0), renderer-admission (Classic type list C6321 /
Smart excludes image/group S1431 — per-family policy lives in the adapters
while the registry stays family-blind; note `LegacyRenderer.canRender` is
satisfied by every projected node, `records.js:40`), node-shell chrome and
intents, unified-render-host adoption/boundary stripping, media-kind /
media-url / preview-fallback / high-res / playback-state primitives,
semantic-zoom policy+apply, versioned node CRUD.

**Next migration unit (selected for R4-09): the mounted-card lifecycle.** All
six adoption paths above already go through `UnifiedRenderHost`, but adapters
never call the returned handle's `destroy()` — cards die by omission and
listeners die with the element. Making targeted refresh/delete route through
the host handle (destroy on delete, destroy+remount on targeted refresh),
starting from the three Smart batch mounts and the two Classic mounts, gives
the Unified RenderRuntime lifecycle ownership with the smallest possible seam
before family card builders move.

Completed by R4-09 (2026-09-06): `WorkbenchRenderRuntime`
(`static/js/workbench/canvas/render-runtime.js`) now owns the mounted-card
lifecycle — keyed mount bookkeeping, ordered destroy on
unmount/remount/batch, `unmountAll` on canvas load. All five adoption mounts
(two Classic, three Smart batch) plus both delete flows and both canvas-load
resets route through it; each adapter keeps exactly one injected
`UnifiedRenderHost.mountAdapterCard` (pinned by test), so page-side card
mount/destruction ownership is removed.

Extended by R4-10 (2026-09-06, Group cutover): `mountGroupCard` on the same
runtime now owns the Group family mount contract — record assembly from own +
member media, the media-vs-legacy-content decision (with `mediaEnabled:false`
rollback semantics), mount execution and lifecycle entry, the resolved shell
view on the result, and an `mountEmptyState` hook. Classic's group branch
(`mountCanvasGroupShell`) and Smart's group batch both delegate; pages retain
only flag gates, member-media extraction, intents, and control selectors.

Extended by R4-11 (2026-09-06, media cutover): the runtime also owns media
state projection for its mounted cards — `mediaState` capture/restore
callbacks wrap the shared playback-state module, `unmount` captures from the
outgoing shell element before destroy, and `mount` restores into the fresh
card. `MediaRenderer` stamps `dataset.url` on its created elements so the
shared signature recognizes renderer-created media, and the page-level
world sweeps exclude `.node-shell-mounted` cards, removing duplicate
projection ownership for mounted media.

Extended by R4-12 (2026-09-06, generic Prompt cutover): the Classic prompt
family moved from adopted pre-rendered DOM to registry-owned rendering —
`prompt-card-renderer.js` registers `prompt-card` (priority 10) with
`NodeCardHost.registry` and builds the editor DOM inside NodeShell; the page
keeps state and services behind `rendererOptions` callbacks (onPromptInput,
onOpenTemplate, templateActive, counter limits, scroll binding) and retains
the pre-rendered markup only as the flags-off fallback.

# Save/merge machinery characterization (U7 blocker analysis, 2026-09-06)

This table characterizes the two adapter save state machines that block the polling, normal-connect,
and viewport ownership rows. It is the prerequisite for one shared save coordinator; it does not itself
migrate ownership.

| Concern | Classic (`canvas.js`) | Smart (`smart-canvas.js`) |
|---|---|---|
| Debounce | `scheduleSave` 500 ms | `scheduleSave` 450 ms |
| Dirty tracking | `localCanvasDirty` flag gates 409 recovery and remote apply deferral | none; any scheduled save sends the full current payload |
| In-flight coalescing | `savingCanvasNow` + `saveCanvasAgain` re-run loop | `canvasSyncInFlight` guard only |
| Payload projection | `serializableCanvasNodes()` | `canvasForStorage()` (media/run-settings stripping, settings projection, prompt-draft flush) |
| Base revision source | `lastCanvasUpdatedAt` (separate mirror; versioned writes update both it and `canvas.updated_at`) | `canvas.updated_at` directly (single source) |
| 409 conflict policy | dirty → adopt remote revision and retry; clean → replace-apply remote canvas | merge server canvas (node-list merge, image union, connection merge) then re-save after 300 ms — neither side is dropped |
| Remote-apply semantics | `applyRemoteCanvasData`: whole-canvas replace preserving local viewport + selection; deferred 1 s while dirty/saving | `applyMergedServerCanvas`: merge into local state, adopt title/revision, re-save if local cleanup recovered state; deferred 600 ms while dragging/selecting |
| Remote-read sync | `syncRemoteCanvasNow`: replace if remote >= local | `mergeReloadCanvasNow`: merge, with drag/selection deferral |
| Remote-sync poll eligibility | `!applyingRemoteCanvas && !document.hidden`, 2.5 s | `!canvasSyncInFlight && !dragState && !selectionState`, 8 s |
| WS update-message path | shared filter → cancel pending save timer, replace-apply | shared filter → skip while in-flight, schedule merge reload |

Design consequence: the two machines share debounce/coalescing/revision-bookkeeping/transport shape but
disagree on the two hard parts — conflict resolution (replace vs merge-union) and remote application.
The unified seam must therefore own scheduling, coalescing, dirty lifecycle, one authoritative revision
mirror, and 409 detection, while delegating conflict resolution and remote application to adapter-supplied
policies until the node-list merge semantics become a shared characterized module. Unifying Classic's
dual revision mirror onto the single authoritative revision is part of that seam's first migration unit.
Classic's replace semantics additionally depend on preserving local viewport and selection, which remain
page-owned state until the viewport row migrates.

Migration order derived from this table (each unit is independently testable with `unified_canvas=0`
rollback): (1) one revision-mirror owner; (2) shared schedule/debounce/coalesce/in-flight coordinator
with adapter payload projection; (3) shared 409 detection with adapter conflict policy; (4) shared
remote-apply scheduling with adapter apply policy; (5) only then, polling eligibility and normal-connect
commit can move without double writes.

Migration unit (1) complete (2026-09-06): `WorkbenchCanvasPersistence.adoptRevision` now owns the
versioned-write revision adoption chain (positive server revision, else keep current, else explicit
fallback). All 26 adoption sites delegate to it — Classic's 10 paired position/delete sites and 8
`onRevision` creation commits (which keep `lastCanvasUpdatedAt` and `canvas.updated_at` coherent through
the single owner), plus Smart's 4 position and 4 delete sites with their preserved per-site fallbacks
(`Date.now()` for position, `0` for delete). A sandbox test pins the adoption chain and source assertions
pin the exact call counts; JS syntax and the full regression (284 tests) pass. Read-only mutation-path
browser evidence is deferred to unit (2), which touches the save scheduling those paths exercise.

Migration unit (2) complete (2026-09-06): `WorkbenchCanvasSaveScheduler`
(`canvas-save-scheduler.js`, loaded by both editor pages before each adapter) now owns debounce,
in-flight coalescing, retry marking, cancel, and the in-flight observers. Classic's
`savingCanvasNow`/`saveCanvasAgain`/`saveTimer` and Smart's `canvasSyncInFlight`/`saveTimer` are removed;
adapters keep only payload projection, conflict policy (Classic replace/defer, Smart merge-and-resave),
dirty flag, and DOM/status effects, and commit through `schedule`/`flush`/`cancel`/`markAgain`. Classic
runs with coalescing (`allowOverlap` off, exact prior semantics including the 409 retry-with-dirty path
via `onRetry`); Smart runs with `allowOverlap: true`, preserving its characterized concurrent-save
behavior while its merge guards now read the shared in-flight state (whose window is marginally wider:
it starts at flush entry rather than after payload preparation). Characterized side fix: Classic's
`applyRemoteCanvasData` deferral condition read a stale `saveTimer` handle (never cleared after a
debounced fire except by a WS update message), so after any local save the poll-driven remote application
deferred forever in a 1-second reload loop; the scheduler's real `hasScheduled()` replaces it. Sandbox
tests cover debounce, coalesced retry (with `onRetry`), overlap mode, cancel, and the observers; source
assertions pin script order and the removal of all legacy state variables. Full regression: PASS (285
tests). Remaining in this seam: unit (3) shared 409 detection, unit (4) shared remote-apply scheduling.

Browser write smoke for units 1–2 (read-isolated, `127.0.0.1:3013`, process-local temporary data
directory, 2026-09-06): the Classic editor booted with all edited wiring (NodeShell-ready page,
`100% · 完整 · 0 节点`), a context-menu 上传节点 creation went through the versioned NodeCreationService
route, the page's revision mirror adopted the server revision (`lastCanvasUpdatedAt` ==
persisted `updated_at` == 1788661517529), the created `image` node with its idempotency request id was
found in the isolated canvas payload after reload (`100% · 完整 · 1 节点`, NodeShell-ready Image card),
and no runtime wiring errors surfaced. The in-editor back-navigation was not directly exercised in the
browser; its changed lines (`saveScheduler.cancel` / flush wrapper) are covered by the sandbox
behavioral tests.

Unit (3) assessment (2026-09-06): no migration remains — the 409 transport normalization (response
`canvas`/`updatedAt` extraction from the conflict body) is already owned by the shared persistence
client, and both adapters consume that shared contract; the divergent parts are the conflict policies
themselves, which stay adapter-owned by design. Remaining seam work is unit (4) only (shared
remote-apply scheduling: Classic's `remoteSyncTimer` deferral and Smart's `canvasSyncTimer` merge
deferral), which is deferred until its owning batch.

Migration unit (4) complete (2026-09-06): shared deferred remote-apply scheduling now has one owner —
`WorkbenchCanvasSaveScheduler.createRemoteApply` — replacing both pages' raw deferral timer state.
Classic's `remoteSyncTimer` is removed; its two scheduling sites keep their exact delays (1000 ms
dirty/saving deferral in `applyRemoteCanvasData`; 700/120 ms WS-update path) through `remoteApplyTimer`.
Smart's `canvasSyncTimer` and the `scheduleCanvasMergeReload` wrapper are removed; its two scheduling
sites keep their exact delays (600 ms drag/selection self-deferral; 200 ms WS-update path) through
`mergeReloadTimer`, while the poll path still applies directly without a timer. Sandbox tests pin the
shared single-slot replace semantics (clear-then-set), default/fallback delay, cancel, and per-adapter
scheduling-site counts; JS syntax and the full regression (286 tests) pass. With this unit the
characterized seam migration order is complete (revision mirror → schedule/coalesce → 409-detection
assessment → remote-apply scheduling), so the polling interval/eligibility ownership row is no longer
blocked on this seam. Both adapters' apply actions, deferral conditions, and conflict policies remain
adapter-owned by design.
2026-09-06 shared semantic-zoom DOM application: Classic and Smart default paths now delegate indicator
construction and NodeShell/Legacy presentation apply+reset to `WorkbenchSemanticZoomApply`
(`semantic-zoom-apply.js`). Adapters keep enablement policy, node/selectors iteration and call timing,
including Smart's floating-menu, hint and smart-actions extras and both adapters' disabled-path resets;
the shared owner applies one computed `WorkbenchSemanticZoom.viewModel` model so Classic's
`model.showSummary` and Smart's `presentation === 'summary'` status rule stay equivalent. Sandbox
behavior tests pin shell/legacy apply+reset, indicator build/update, and page script order; source
assertions pin the delegation sites and the removal of the duplicated per-page apply code. Focused
regression: PASS (101 tests); full regression: PASS (287 tests).
2026-09-06 shared node-drag position projection: Classic's main-and-children drag and Smart's group
drag (including the media-thumbnail detach drag) now delegate pointer-to-world delta, live-scale
conversion and member-origin position projection to `WorkbenchCanvasRuntime.createNodeDragSession` on
the default path. Adapters keep member collection (Classic alt-copy/recursive group/multi-select
collection; Smart group expansion), alt/ctrl product semantics, DOM application, runtime mirrors and
commit policies; `unified_canvas=0` retains the page-local calculation. Sandbox tests pin multi-member
projection, per-move scale override, invalid-member filtering and frozen results; source assertions pin
the three delegation sites and rollback retention. Focused regression: PASS (102 tests); full
regression: PASS (288 tests).
2026-09-06 shared node-resize size proposal: Classic's node resize and Smart's node resize now delegate
pointer-delta-to-world-delta conversion and the raw start-size proposal to
`WorkbenchCanvasRuntime.createNodeResizeSession` on the default path. Smart's three resize branches
(direct, image-group, smart-group member zoom) consume one unified `proposedW/proposedH` pair; Classic
keeps its `min(min.w, 220)`/96 clamp policy and Smart keeps its per-type clamps, group member-zoom
algorithm, LLM-instruction height resize, DOM application and commit lifecycle; `unified_canvas=0`
retains the page-local calculation. Sandbox tests pin delta/proposal projection, per-move scale
override, default-scale fallback and frozen results; source assertions pin both delegation sites, the
proposed-size consumption, and the removal of the duplicated `Math.round(startW + dx)` expressions.
Focused regression: PASS (103 tests); full regression: PASS (289 tests).
2026-09-06 clipboard/subgraph parity acceptance and smart-group paste fix (isolated `127.0.0.1:3018`,
process-local SQLite copy): on the Classic fixture, all six nodes selected through the runtime command,
page `copySelectedNodes` captured a 6-node/6-connection fragment with an identical type multiset, and
page `pasteNodes` appended exactly six remapped-id copies with six new connections, preserved relative
geometry, and auto-selection. On the Smart fixture the same page flow round-tripped a Prompt card with
a remapped id. The run exposed a real pre-existing gap: Smart's paste remapped `inputNodeIds` and
`sourceNodeId` but kept a pasted smart-group's `items` pointing at the at-copy-time member ids. Fixed by
remapping items through the shared materializer id map, keeping refs to pre-existing nodes, and dropping
dangling ids (the filter must also check the not-yet-pushed copies). Browser-verified three scenarios:
group+member remap with the pasted group resolving its pasted member, original-ref retention when the
member was not copied, and dangling-id drop. Focused regression: PASS (104 tests); full regression:
PASS (294 tests).
```

## Browser — new Canvas

```text
Not yet run in this task. Existing status records read-only acceptance only.
```

## Browser — Legacy Classic

```text
2026-09-05 read-only isolated `127.0.0.1:3012`: normal `canvas.html` URL rendered Classic fixture `7ed83bf56f234d77a9e67ae1f6496577` with six ready NodeShell cards, ports, media controls and workflow controls. No Canvas mutation or execution was invoked.

2026-09-06 read-only local `127.0.0.1:3000/static/canvas.html`: Classic fixture `7ed83bf56f234d77a9e67ae1f6496577` rendered six nodes, link controls and the default semantic indicator `100% · 完整 · 6 节点`. No Canvas mutation or execution was invoked.

2026-09-06 read-only local post-connected-result smoke: the same Classic fixture rendered six nodes, link controls and `100% · 完整 · 6 节点`. No Canvas mutation, creation or execution was invoked.

2026-09-06 read-only local post-file-drop-runtime smoke: the same Classic fixture rendered its six ready cards and `100% · 完整 · 6 节点` after loading `media-drop-payload.js`. No upload, Canvas mutation, creation or execution was invoked.

2026-09-06 read-only local post-file-drop-payload smoke: the same Classic fixture rendered its six ready cards and `100% · 完整 · 6 节点` after loading the new payload-resolution script version. No upload, Canvas mutation, creation or execution was invoked.

2026-09-06 read-only local post-file-drop-upload smoke: the same Classic fixture rendered its six ready cards and `100% · 完整 · 6 节点` after loading the shared upload-transport script version. No upload, Canvas mutation, creation or execution was invoked.

2026-09-06 read-only local post-blank-Prompt-mutation smoke: the same Classic fixture rendered its six ready cards and `100% · 完整 · 6 节点` after loading the new mutation script version. No Prompt move/delete, Canvas mutation, creation or execution was invoked.

2026-09-06 read-only local post-default-Loop-mutation smoke: the same Classic fixture rendered its six ready cards and `100% · 完整 · 6 节点` after loading the new mutation script version. No Loop move/delete, Canvas mutation, creation or execution was invoked.

2026-09-06 read-only local post-empty-Output-mutation smoke: the same Classic fixture rendered its six ready cards and `100% · 完整 · 6 节点` after loading the new mutation script version. No Output move/delete, Canvas mutation, creation or execution was invoked.

2026-09-06 read-only local post-empty-Group-mutation smoke: the same Classic fixture rendered its six ready cards and `100% · 完整 · 6 节点` after loading the new mutation script version. No Group move/delete, Canvas mutation, creation or execution was invoked.
2026-09-06 isolated read/write smoke `127.0.0.1:3014` (process-local copy of the local SQLite database, canonical default routing): the Classic fixture `7ed83bf56f234d77a9e67ae1f6496577` rendered six NodeShell-mounted cards and `100% · 完整 · 6 节点` with `WorkbenchSemanticZoomApply`, `createNodeDragSession` and `createNodeResizeSession` present and `unified_canvas` default-on. A pointer drag of the `video-item` card moved it from (1018,237) to (1098,297) — exactly the +80/+60 screen delta through the shared drag session — and a resize-handle drag grew it from 252×376 to 301×414, exactly the +49/+38 proposal; the isolated database recorded the dragged position and resized box. No console errors surfaced; the temporary server and database copy were stopped and removed after the check.
```

## Browser — Legacy Smart

```text
2026-09-05 read-only isolated `127.0.0.1:3012`: the same normal `canvas.html` entry handed historical Smart fixture `ca914662f0dc4923bd5b60b29eb55b68` to its bounded compatibility adapter, which rendered Composer, Smart Group, upload node, ready NodeShell ports and workflow controls. No Canvas mutation or execution was invoked. The temporary server was stopped after verification.

2026-09-06 read-only local `127.0.0.1:3000/static/smart-canvas.html`: historical Smart fixture `ca914662f0dc4923bd5b60b29eb55b68` rendered Composer, Smart Group with Input/Output ports, upload node and the default semantic indicator `65% · 摘要 · 2 节点`. No Canvas mutation or execution was invoked.

2026-09-06 read-only local post-connected-result smoke: the same Smart fixture rendered Composer, Smart Group/Input/Output ports, upload and Prompt cards, plus `65% · 摘要 · 2 节点`. No Canvas mutation, creation or execution was invoked.

2026-09-06 read-only local post-file-drop-runtime smoke: the same Smart fixture rendered Composer and `65% · 摘要 · 2 节点` after loading `media-drop-payload.js`. No upload, Canvas mutation, creation or execution was invoked.

2026-09-06 read-only local post-file-drop-payload smoke: the same Smart fixture rendered Composer, Group/Input/Output, upload and Prompt cards and `65% · 摘要 · 2 节点` after loading the new payload-resolution script version. No upload, Canvas mutation, creation or execution was invoked.

2026-09-06 read-only local post-file-drop-upload smoke: the same Smart fixture rendered Composer, Group/Input/Output, upload and Prompt cards and `65% · 摘要 · 2 节点` after loading the shared upload-transport script version. No upload, Canvas mutation, creation or execution was invoked.

2026-09-06 read-only local post-default-Smart-Loop-mutation smoke: the same Smart fixture rendered Composer and `65% · 摘要 · 2 节点` after loading the new mutation script version. No Loop move/delete, Canvas mutation, creation or execution was invoked.

2026-09-06 media playback-state contract: shared capture/restore now has explicit transport- and persistence-neutral coverage for time, pause, rate, mute and volume; Classic/Smart player binding and fallback policy remain adapter-owned. Focused regression: PASS (95 tests); full regression: PASS (270 tests).

2026-09-06 Renderer Admission browser read smoke: local Classic fixture retained six rendered cards and `100% · 完整 · 6 节点`; historical Smart fixture retained Composer, Smart Group, upload and Prompt cards with `65% · 摘要 · 2 节点`. Both used the shared admission module; no mutation, creation, save or execution was invoked.

2026-09-06 Smart blank-Prompt mutation browser read smoke: local `127.0.0.1:3000` loaded historical Smart fixture `ca914662f0dc4923bd5b60b29eb55b68` after the cache-version update, retaining its Composer and `65% · 摘要 · 2 节点`. The check was read-only: no Prompt move/delete, save, creation or execution was invoked.

2026-09-06 Classic connected-creation browser read smoke: local `127.0.0.1:3000` loaded Classic fixture `7ed83bf56f234d77a9e67ae1f6496577` after the command cache update, retaining six ready cards, generic Input/Output ports, media controls, workflow controls, and `100% · 完整 · 6 节点`. The check was read-only: no connection, creation, save, deletion or execution was invoked.
2026-09-06 isolated read/write smoke on the same `127.0.0.1:3014` temporary server: the historical Smart fixture `ca914662f0dc4923bd5b60b29eb55b68` rendered its Composer, shell-mounted Group and Prompt cards, the retained empty node, and `65% · 摘要 · 2 节点`, with the shared semantic-zoom, drag and resize modules present and `unified_canvas` default-on. A pointer drag of the Prompt card at 65% zoom moved it by a world delta of +61.84/+46.38 — exactly the +40/+30 screen path divided by the live scale through the shared drag session — and the isolated database recorded the new position. No console errors surfaced; the temporary server was stopped and removed after the check.
2026-09-06 unified-runtime lifecycle authority: canvas state swaps now reset the unified runtime through
one seam per adapter — Classic `adoptCanvasRuntimeState` (openCanvas, create-canvas, remote
replace-apply, return-to-manager, delete-current) and Smart `adoptSmartRuntimeState` (loadCanvas). The
seam adopts the new viewport and drops the runtime so the next dispatch reseeds it from the new
canvas's viewport, geometry and selection; this removes the latent stale-base bug where an in-place
canvas switch left the previous runtime holding viewport/geometry/selection while wheel `VIEWPORT_ZOOM_AT`
computed against it. The save-path same-value viewport reassignment stays page-local; `unified_canvas=0`
behavior is unchanged. Source assertions pin the seam and all swap sites. Focused regression: PASS (104
tests); full regression: PASS (290 tests).

2026-09-06 isolated reseed browser smoke `127.0.0.1:3015` (process-local copy of the local SQLite
database): on the Classic editor, canvas B was zoomed to 1.08 through a real wheel event, then an
in-place `openCanvas` switch back to canvas A was verified to null the runtime, restore A's stored
viewport ({0,0,1}, not B's zoomed one), re-seed the runtime from A's state, and compute a subsequent
zoom-at exactly from the fresh base (anchor 300/200 → viewport {-24,-16} at scale 1.08). The Smart page
verified the same adopt→null→reseed cycle against its 65% camera. No console errors surfaced; the
temporary server and database copy were stopped and removed after the check.
```

## Persistence / restart

```text
2026-09-06 isolated restart durability check `127.0.0.1:3019` (process-local copy of the local SQLite
database): after the dual-writer conflict cycle below reached revision R2 (1788679108411) with the moved
`video-item` node at (1078,277), the server process was killed and restarted on the same database copy;
a fresh API read returned the identical revision and node position. The temporary server was stopped and
the database copy removed after the check.
```

## Stale conflict

```text
2026-09-06 isolated dual-writer conflict run `127.0.0.1:3019` (process-local SQLite copy, canonical
default routing), Classic fixture `7ed83bf56f234d77a9e67ae1f6496577`: (1) API level — a PUT with the
current base revision succeeded (200, R0→R1) and an immediate second PUT carrying the stale base R0 was
rejected with 409 and a conflict detail containing the authoritative canvas and updated_at; (2) browser
level — the loaded page (whose remote-read poll had already adopted R1) was deterministically set one
revision behind, a real pointer drag of `video-item` by exactly (+60,+40) scheduled a save with the
stale base, fetch instrumentation recorded the 409 followed 9 ms later by a successful retry (200), the
adapter adopted the authoritative revision (R2, 1788679108411) and the moved node position was confirmed
through a fresh API read. No console errors; the temporary server was stopped after the check.
```

## Rollback

```text
2026-09-06 isolated rollback-path check on the same temporary server: the Classic editor loaded with
`unified_canvas=0` (the bounded U7 rollback control) with the unified runtime confirmed null, rendered
its six NodeShell cards and `100% · 完整 · 6 节点` indicator, and a real pointer drag of `video-item`
moved it by exactly (+50,+35) through the page-local fallback math with a clean save. The temporary
server and database copy were stopped and removed after the check.
```

## Workflow import/export

```text
2026-09-06 isolated round-trip parity run `127.0.0.1:3017` (process-local copy of the local SQLite
database): on the Classic fixture `7ed83bf56f234d77a9e67ae1f6496577`, all six nodes were selected
through the migrated `applyCanvasRuntimeSelection` command, the page-owned `selectedWorkflowPayload`
projection produced a 6-node/6-connection workflow, and the shared transfer client exported it through
the real `/api/canvas-workflows/export` endpoint with resources (1,313-byte archive). The full page
import path (`importWorkflowFile` → shared import endpoint → `normalizeImported` → shared
`materializeImportedSubgraph` → append/render/save) then appended exactly 6 nodes and 6 connections
with an identical node-type multiset, remapped ids, auto-selection of the imported subgraph, and a
relative geometry exactly equal to the original bounding box under one uniform offset. After reload the
canvas persisted 12 nodes / 12 connections with all 12 cards NodeShell-rendered and the correct
semantic indicator. No console errors surfaced; the temporary server and database copy were stopped and
removed after the check. Smart retains no workflow transfer UI, so parity is a Classic/Unified surface.
```

## Architecture guards

```text
2026-09-06 automated guards added (`tests/test_architecture_guards.py`, source-scan based, negative-tested
with scratch violations): (1) core domain/application layers import no codex runtime or protocol modules,
with relative imports resolved so `from ..codex` cannot hide (AGENTS.md §15); (2) no core Python surface
imports or string-references a wholehouse package (§1); (3) product runtime sources — main.py, workbench
Python, static JS excluding vendored libraries, and editor pages — contain no raw/tree/codeload
git-hosting fetch URLs, while plain upstream repository page links remain allowed (§29). Focused: PASS
(4 tests); full regression: PASS (294 tests). Gate M items without automated coverage (provider-specific
Canvas branches, legacy-monolith business additions, duplicate runtime initialization) remain review/
inspection items.
```

## 100 nodes

```text
2026-09-06 visible-frame rerun on the current worktree (isolated server, disposable canonical records,
`node_shell=1&legacy_renderer=1`, harness `interactions=1&visible=1`): 100 media-free Legacy Prompt
nodes — render ready 265 ms, zoom 16.5 ms, pan 16.9 ms, minimap 33 ms, 3,645 target DOM elements,
PASS. See `docs/benchmarks/canvas-node-shell-rerun-2026-09-06.md` for the full table and the 2026-09-04
baseline comparison; all values are below the provisional 120 ms local alert.
```

## 300 nodes

```text
2026-09-06 visible-frame rerun on the current worktree (same capture as above): 300 media-free Legacy
Prompt nodes — render ready 191 ms, zoom 16.6 ms, pan 37.6 ms, minimap 28.9 ms, 9,445 target DOM
elements, PASS. No interaction regression from the shared interaction-session changes; the offscreen
minimap cadence P2 follow-up remains recorded.

2026-09-06 Gate-K duplication and memory inspection on the same worktree (isolated server, disposable
300-node canonical record): source-level scan found only two recurring `setInterval` sites in the
adapters, both guarded against re-registration (`outputTimer`, `runTimerInterval`), one shared
remote-sync poll instance per page, and one shared save scheduler; window-level handlers use assignment
semantics (`window.onmousemove/onmouseup`, 30+2 sites) so they cannot accumulate, and Smart's
`bindNodeEvents` binds only elements freshly created by each render pass, so discarded cards release
their listeners. A browser probe ran ten real zoom+pan interaction cycles on the 300-node record: the
DOM element count stayed exactly 9,744 in every cycle (no DOM duplication or growth) and
`usedJSHeapSize` went from 19 MB to 16 MB (no growth; transient garbage collected). See the benchmark
rerun above for the latency budget.
```

---

# Remaining Runtime Owners

## Classic

```text
Classic still owns product interaction state except NodeShell select/focus/menu and box completion, fallback node constructors, upload/file-drop creation, renderer lifecycle, all non-blank/group-linked deletion, rich move/edit behavior and Legacy execution behavior.
```

## Smart

```text
Smart still owns product interaction state, Composer, fallback node constructors, group/media/history/dependent-node deletion, group/media lifecycle, upload, MiniMax/video compatibility and execution behavior.
```

## Unified

```text
Unified owns SQLite CanvasRecord authority, CAS application services, the normal entry resolver, creation catalog, default-on supported blank creation, shared runtime primitives, NodeShell/renderer seams, graph/media/transfer algorithms and compatibility clients. These are not yet one product runtime.
```

---

# R4 Gate

```text
R4: NOT PASS
```

Change to `PASS` only when all requirements in `CODEX_EXECUTION_PLAN.md` are evidenced.
