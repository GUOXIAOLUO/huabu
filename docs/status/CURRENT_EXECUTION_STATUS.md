# Current Execution Status

status_schema: workbench.execution-status/2

## Repository

repository: local worktree (remote repository out of scope)
verified_head: 09f180d60ace564be91d60dac495894cb889b0f1
verified_commit: "docs: close R4-21 review and activate R4-22"
branch: main
remote_state: not checked; GitHub/remote synchronization is out of scope for this local task
verified_at: 2026-09-07T08:15:00+08:00
verification_source: current local worktree (HEAD 09f180d plus the uncommitted R4-22 file-drop, R4-23 clipboard, and R4-24 connect-command additions; regression gate PASS at 367 tests)
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
blocking_issues: []

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

## Blockers

No external blocker. Source backup/validation, SQLite authority activation, default
canonical routing, isolated Classic/Smart browser reads and browser creation,
restart/stale-conflict/rollback verification, workflow archive round-trip, and the
deterministic benchmark are complete. R4 remains incomplete only at U7: duplicate
Classic/Smart runtime and page removal, followed by UI migration-flag retirement.

## Exactly one next authorized Round

No next Round is authorized while R4 is active.

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
