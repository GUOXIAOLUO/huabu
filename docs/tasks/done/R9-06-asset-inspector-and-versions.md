# CARD R9-06 — Asset Inspector and Versions

- Round: R9
- Priority: P1
- Status: DONE — independent Review PASS
- Depends on: R9-05 (DONE, independent Review PASS)

## Goal

Show preview, metadata, versions, provenance and usage references.

## Before Owner

legacy asset panels

## After Owner

Asset Inspector

## In Scope

- Render current version/history.
- Show used-by references where available.
- Expose drag/open/version actions.

## Out of Scope

- No approval semantics.

## Compatibility / Migration

- Preserve existing behavior and data unless the card explicitly authorizes a migration.
- No migration. `SqliteAssetRepository.migrate()` is unchanged by this card: no
  new table, no new column, no new index. The version-history read uses the
  `asset_versions` table R9-03 already created, so an existing database is read
  as-is and no stored row is rewritten.
- The legacy per-category detail panels (`renderAssetDetail`,
  `renderCanvasAssetDetail`, `renderLocalDetail`, `renderWorkflowDetail`) and
  `data/asset_library.json` stay page-owned compatibility and are deliberately
  untouched: this card adds the canonical Asset Inspector beside them, exactly as
  R9-05 added the canonical query beside the legacy browse tree.
- `R9-05`'s `asset-query-panel.js` gains one additive thing — a result row is now
  a button carrying `data-asset-query-select` / `aria-pressed` — because an
  inspector needs something to select. The query state, the request shape, the
  filter vocabulary and every existing assertion are unchanged.

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

- Add/run the smallest behavioral tests that prove this card's goal.
- Run `./scripts/agent-verify.sh`.

## Definition of Done

- [x] Asset versions are understandable and traceable.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

`legacy asset panels`. One asset's versions could not be seen at all. The
canonical read surface exposed `version_ids` as bare ids and a single version
only by `(asset_id, version_id)`, so nothing listed an asset's *history*: "which
version is current", "what changed between v2 and v3", "where did this version
come from and when" had no answer anywhere in the product. The only detail panes
that existed (`renderAssetDetail`, `renderCanvasAssetDetail`, `renderLocalDetail`,
`renderWorkflowDetail`) read one mutable row of the legacy
`data/asset_library.json`, which has no version concept at all — so the legacy
panels were the owner of "what an asset is" for a store that cannot express
history, while the canonical store that *does* express history had no presenter.

After:

`Asset Inspector`. One chain, one owner per layer:

- `workbench/application/asset_versions.py` owns `AssetVersionHistory` — the
  versions of one asset in ordinal order with the end of the sequence named as
  the current version. Ordering and "current" are *derived* from the ordinals and
  never stored as a flag, so the sequence has exactly one owner; a duplicate or
  gapped ordinal is rejected rather than rendered.
- `SqliteAssetRepository.list_versions` owns the SQL, and the shared
  `_version_from_row` mapping owns the row→record projection.
- `AssetService.history` owns the read boundary and authorizes against the
  *asset's own* project, so a caller cannot widen the read.
- `GET /api/v1/assets/{asset_id}/versions` owns the transport and names
  `current_version_id` in the reply, so a client does not re-derive it.
- `WorkbenchAssetInspector` (`static/js/workbench/canvas/asset-inspector.js`)
  owns the presentation of one canonical asset — preview, metadata, version
  history, provenance, usage, and the open/drag/version actions — mounted by
  `static/asset-manager.js` into `#assetInspector`.

Duplicate owner removed:

Not on the legacy side, and deliberately so: the legacy detail panels present a
different store's items and retiring them is not authorized by this card — the
same call R9-05 made for the legacy browse tree. What this card *did* remove are
two duplicate owners it would otherwise have created inside the new code:

- `_version_from_row` replaces the row→record mapping that `load_version` held
  alone; `list_versions` answers the same question at a wider width, and two
  copies of that mapping would have drifted the first time a version column was
  added.
- `_version_response` replaces the same projection in the transport: the single
  version read and the history read now share one projection of
  `AssetVersionResponse`.

Two rules that had no owner before now have exactly one, and the module declines
to own them a second time: **which version is current** (the service resolves it
from the sequence; the inspector renders the reply's answer and shows *no*
version rather than guessing when the reply names one its own list does not
contain), and **whether anything references the asset** (the host supplies the
verdict; "we did not look" and "we looked and found nothing" render differently,
so an unavailable reference index can never be shown as "unused").

## Developer Verification

- Focused `tests/test_asset_versions.py`: **18 tests PASS** — the history
  contract (ordering derived from ordinals rather than trusted, `current` as the
  end of the sequence, empty history has no current, lookup by id, rejection of a
  foreign asset's version, of duplicate ordinals and of a gapped sequence, the
  asset-id requirement, frozenness); the repository (`list_versions` in ordinal
  order, an asset with no versions as an empty list rather than an error, a
  missing asset as a not-found, every content/provenance field round-tripping,
  and the structural agreement `asset.version_ids == [v.id for v in versions]`);
  the service (authorization against the asset's own project, proven by an asset
  in a project the actor is not a member of, and a missing asset as a not-found
  rather than an empty history); the transport (401 without an actor, 403 for a
  non-member, 404 for an unknown asset, the 200 envelope with its exact key set
  and `current_version_id`, and `/versions` staying distinct from
  `/{asset_id}/versions/{version_id}`); and the composition root actually
  registering the version-history route.
- Focused `tests/test_asset_inspector.py`: **14 tests PASS** — preview kind from
  the version's own mime type; only a fetchable location ever reaching a `src`
  (with `file://`, `asset://`, protocol-relative and bare relative all refused and
  the address shown as text instead); which version is shown (the selection, else
  the reply's current one, and *nothing* when the reply names an unknown current
  version); the full render (preview, metadata, history rows with ordinal,
  checksum, mime, size and timestamp, provenance, the single current badge,
  actions); the usage verdict distinguishing unavailable from no-references; the
  drag payload's exact key set carrying no bytes or address; the client's one
  request and normalized reply; the label maps pinned against `get_args(...)`;
  the module's purity (no `document.`, no `localStorage`, no legacy store, no
  event listener, no `dataTransfer`); `node --check`; the page mounting the
  inspector and owning its events; and the query rows exposing the selection.
  The thirteenth drives the page's *lifecycle* instead of grepping for a call:
  the shipped lifecycle functions are extracted **verbatim** from
  `asset-manager.js` into a Node harness that stubs only the DOM elements, the
  two clients and the icon refresh, and it asserts that a reload landing on a
  page without the selected asset — by paging and by narrowing the search — hides
  the inspector rather than leaving the previous asset rendered. See
  *Defect found by independent Review* below for why that distinction matters.
  A fourteenth does the same for the switch between assets: selecting a second
  asset must load *that* asset's history, asserted on the version ids rather than
  merely the heading, the two fixtures differing in every field.
- `./scripts/agent-verify.sh`: **PASS — 1251 tests**, 249 Python AST files, 149
  JavaScript files, 4 architecture guards, clean `git diff --check`. The
  pre-change baseline on the same tree was **PASS — 1219 tests**, so the card adds
  exactly its own 32 (30 on delivery, plus the two lifecycle tests added when the
  Review's findings were closed).
- DoD probe, independent mechanism (the real composition root booted as a server
  on an isolated port, an isolated copy of the real `data/workbench.sqlite3`,
  **four separate OS processes** — write / serve / raw row read-back / browser
  module — and a sha256 digest of the whole real `data/` tree before and after):
  **59/59**. It proves 401/403/404, that the 404 is not a 200 with zero versions,
  that an asset in a project the actor is not in is refused, and that all three
  versions come back in ordinal order with the current one named — then compares
  *every* content and provenance field of all three versions against what the
  writer process stored, reads the raw `asset_versions` rows back in a third
  process, renders the fetched reply through the real `asset-inspector.js` in a
  fourth, and confirms the real `data/` tree was byte-identical afterwards.
- Mutation review: **17 probes, 17/17 caught**, every source restored
  byte-identical by sha256 after each probe and every run reporting the suite's
  real test count, so no probe was credited to a broken run. The set covers the
  composition-root registration, the reply naming the current version, the
  derived ordering, all three sequence assertions, the repository's ordering and
  not-found behaviour, the shared row mapping, the service's authorization, the
  domain-widening axis (a UI mirror of a closed set must follow `get_args`), the
  location servability rule, the usage honesty rule, the no-guessing rule, the
  drag payload's contents, and the page's sync and click wiring.

## Defect found by independent Review and fixed

The first independent Review (2026-09-13) found one blocking defect on an axis
none of those 17 probes covered. It is fixed on this card.

`loadAssetQuery()` re-rendered the query panel in its `finally` block but never
synced the inspector, and `syncAssetInspector()` was only ever called from
`render()` and from a row click. Every *incremental* query mutation reloads
through `loadAssetQuery()` without going through `render()` — paging, narrowing
the search, the type/source chips, removing a tag, changing the page size and
pressing Enter — so once any of them landed on a result page that no longer
contained the selected asset, the inspector kept rendering that asset's versions
while the results beside it no longer contained it. That contradicts the
invariant this card wrote into the page source: "Paging away from it hides the
inspector instead of showing another page's asset." Only the global refresh
self-healed, because `loadAll()` ends with `render()`.

Reproduced before the fix by driving the shipped lifecycle functions (extracted
verbatim, real presentation module): after paging away, and again after a
narrowed search, the inspector still held **2038 bytes** of the previous asset's
HTML. Fixed by one added `syncAssetInspector()` call in the reload's `finally`;
both scenarios then rendered **0 bytes**.

Why the suite had stayed green is worth recording: the page test asserted
`assertIn("syncAssetInspector();", page)`, which pins that the call exists
*somewhere in the file* and says nothing about which paths make it. The
replacement test drives the path instead of grepping for it, and reverting the
fix makes it fail on exactly that assertion.

## Independent Review (2026-09-14) — CHANGES_REQUIRED

Re-reviewed on axes disjoint from both the author's set and the first pass: the
changed path crossed with the error path and with overlapping requests.

Behavioural probes — all hold on the fixed code:

- A reload that still contains the selection does **not** refetch the history
  (one fetch on select, one after: no redundant request, no flicker).
- A *failed* query reload clears the inspector instead of leaving it stale, and
  the failure surfaces as the error message.
- Two overlapping reloads end consistent with the final page.
- Selecting a second asset shows that asset's history with no stale content from
  the first.

Mutation probes on the new axes:

- `selectedQueryAsset` ignoring the selection → **caught** by the lifecycle test.
- `renderAssetInspector` dropping its empty-asset branch → **caught** by the
  lifecycle test.
  Together these show the new test pins the *invariant* — the inspector must
  reflect the current page — rather than merely pinning that one call exists.
- **`syncAssetInspector` no longer resetting when the asset changes → GAP, now
  closed.** This was the one required change. The shipped code was *correct*:
  selecting a second asset did load that asset's history (probed directly). But
  the guard that drops the previous asset's history is reachable — clicking one
  result row then another is the panel's most ordinary interaction — and nothing
  pinned it. With it removed, the inspector renders the first asset's versions
  under the second asset's heading and never loads the second one's at all,
  because the "already have a history" short-circuit sees one. This card added
  that guard, so this card now pins it: the harness gained a switch scenario
  (select A, then select B) asserted on version ids rather than merely the
  heading, and re-running the probe now fails exactly that test.

Classified non-blocking in the same pass: `assetInspectorVisible` returning
`true` unconditionally survives every test. It only feeds the render signature,
and `renderAssetInspector` independently clears the DOM when no asset is
selected, so the observable invariant is already pinned — it is defence-in-depth.

## Next Recommended Card

`R9-07`

Do not execute the next card in the same Agent run.
