# CARD R9-05 — Asset Search and Filter

- Round: R9
- Priority: P1
- Status: DONE — independent Review PASS; archived 2026-09-13
- Depends on: R9-04 (DONE, independent Review PASS)

## Goal

Search/filter assets by type/project/source/tags/metadata.

## Before Owner

basic asset browsing

## After Owner

asset query service + UI

## In Scope

- Add indexed/queryable metadata.
- Implement search/filter UI.
- Paginate for large libraries.

## Out of Scope

- No semantic vector search requirement.

## Compatibility / Migration

- Preserve existing behavior and data unless the card explicitly authorizes a migration.
- The legacy per-category browse tree, its own item search inputs and
  `data/asset_library.json` stay page-owned compatibility and are deliberately
  untouched: this card adds a canonical query surface beside them, it does not
  rewrite the retained managers.
- `migrate()` only ever adds (new `asset_tags` projection table plus four
  `CREATE INDEX IF NOT EXISTS` statements), so an existing database is extended
  in place and no stored asset row is rewritten. Assets are immutable and
  append-only through the repository, so the tag projection cannot drift.

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

- [x] Users can find assets without browsing Canvas.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: assets could only be browsed by walking the legacy per-category tree in
`static/asset-manager.js` over `data/asset_library.json`; the only narrowing was
a per-category client-side substring match on `name` / `url` / kind, there was
no way to filter by type, source, status or tag, no paging, and nothing read the
canonical Asset store at all. `SqliteAssetRepository` could only `list_assets`
for one project and load one asset by id.

After: `AssetService.query(AssetQuery, actor_id=...)`
(`workbench/application/asset_service.py`) is the single application boundary
for searching assets; `AssetQuery` / `AssetQueryPage`
(`workbench/application/asset_query.py`) own the validated, frozen filter and
page contract; `SqliteAssetRepository.query_assets` owns the SQL;
`GET /api/v1/assets/query` is the canonical transport; and
`WorkbenchAssetQueryPanel` (`static/js/workbench/canvas/asset-query-panel.js`)
owns the query state, the request shape and the pure rendering of one result
page, mounted by `static/asset-manager.js` into `#assetQueryPanel`.

Duplicate owner removed: none — the legacy browse tree is a different surface
(it browses one category of the legacy store), and retiring it is not authorized
by this card. The new surface is the canonical one: it is the only path that
reads the canonical Asset store, and the page no longer has to reach into the
legacy tree to answer "which assets match this filter".

## Developer Verification

- Focused `tests/test_asset_query.py`: **14 tests PASS** — project scoping,
  type/source/status/text filters, tag intersection answered by the
  `asset_tags` index (row contents, index existence and query plan asserted),
  paging with the unpaged total, rejection of vocabulary outside the domain's
  closed sets, normalization/de-duplication, `has_more` semantics, service
  authorization against the query's own project, the canonical API envelope
  (401 without an actor, 403 for a non-member, 200 page, 422 for a value the
  domain rejects), the composition root actually registering
  `/api/v1/assets/query` as its own path beside `/{asset_id}`, the frozen
  query/page records, and the two 422 sources staying distinguishable — in the
  isolated router app and in the shipped validation handler.
- Focused `tests/test_asset_query_panel.py`: **7 tests PASS** — query-state
  validation and window reset, one canonical request per page with the
  `X-User-ID` actor header and normalized reply, panel rendering of filters /
  results / paging / empty / loading / error states, the page mounting the panel
  as its single query surface while owning every event, the module's purity
  (no legacy store, no `localStorage`, no `document`), `node --check`, and the
  panel's filter vocabulary pinned against the domain's own closed sets.
- `./scripts/agent-verify.sh`: **PASS — 1219 tests**, 246 Python AST files,
  148 JavaScript files, 4 architecture guards, clean `git diff --check`.
- Browser acceptance (headless Chrome + CDP against the real local server, on an
  isolated copy of the SQLite database with 30 seeded assets): the Resources
  page renders `#assetQueryPanel .asset-query` with all seven type chips and a
  `1-24 / 30` page; 下一页 moves to `25-30 / 30` and disables; the 视频 chip
  narrows to `1-10 / 10` with every row badged 视频; entering the `hero` tag and
  pressing Enter adds a `#hero` chip and narrows to `1-2 / 2`; 重置 restores
  `1-24 / 30` with no active chip; switching the rail to 提示词 removes the
  panel. The real `data/workbench.sqlite3` and `data/asset_library.json` were
  byte-identical (sha256) before and after.

## Independent Review Repair (2026-09-13)

The independent Review returned **CHANGES_REQUIRED** on two blocking items. Both
were *unpinned declarations*, not DoD or architecture defects: the DoD itself was
independently reproduced through a different mechanism (the real composition
root, an isolated database copy, separate OS processes, a raw-row read-back, and
a sha256 proof that the real data files were untouched — 24/24 checks).

- **F1 — the composition root mounting this card's canonical transport was
  unguarded.** Deleting the
  `include_router(create_canonical_assets_router(...))` line left the whole suite
  green. Every sibling card that adds a router (`test_result_selection`,
  `test_result_materialization`, `test_execution_branch`, `test_result_collection`)
  carries a `test_composition_root_registers_the_*` guard, each with a comment
  saying why; the assets router had none. Inherited from R9-03, which introduced
  the router — this card adds `/query` to it. **Fixed:** added
  `AssetQueryCompositionRootTests.test_composition_root_registers_the_canonical_query_route`,
  asserting `main.app.openapi()["paths"]` holds `/api/v1/assets/query` (GET) and
  `/api/v1/assets/{asset_id}` (GET) as distinct paths.
- **F2 — the panel's filter vocabulary was a second copy of the domain's closed
  sets, pinned only against itself.** Widening `AssetType` in the domain left the
  suite green while `asset-query-panel.js` kept the old vocabulary, so the
  canonical search UI would silently lose the ability to filter a canonical
  member. The existing assertion pinned the literals inside the JS source, which
  is tautological with respect to the domain. The repository already compares a
  derived artifact against its domain source for exact equality in
  `test_node_record.test_published_node_kinds_are_exactly_the_domain_closed_set`.
  **Fixed:** added
  `test_panel_filter_vocabulary_is_exactly_the_domain_closed_sets`, which reads
  `TYPES`/`SOURCES`/`STATUSES` out of the running module and asserts exact
  equality with `get_args(AssetType | AssetSource | AssetStatus)`, drives the
  text/tag bounds from the Python `MAX_TEXT_LENGTH` / `MAX_TAG_LENGTH` constants,
  and requires every offered page size to be one the server accepts.

Both guards were then proven load-bearing with a mutation harness (read bytes →
require a unique anchor → one rewrite → run the owning suite → restore → re-verify
sha256): F1 is now caught by the full suite (1216 tests) and F2 by the asset module
set (63 tests). The third probe (`AssetQuery` frozenness) is still a gap and is
listed below.

Non-blocking items the Review recorded and this repair did **not** address (out of
the authorized scope): `AssetQuery` frozenness is unguarded; the card asserts only
the 422 *status* and does not pin the response shape that distinguishes a framework
validation error (`detail` + `errors` list) from this seam's own error (`detail`
only); the text filter is one contiguous substring over the raw metadata JSON, so
`"probe 11"` does not find `"Probe asset 11"` and a metadata key name matches every
asset carrying it; `AGENT_NEXT_TASK.md` still reads
`Status: ACTIVE — dependency satisfied; implementation not started` while the same
file's `Recommended Successor` section and this card say implementation is complete;
and the panel's `DEFAULT_PAGE_SIZE` (24) shares a name with the server's (50).

## Truth Reconciliation (this run)

The pre-change baseline gate was **red** on one contract:
`tests/test_current_fact_documentation.py` still asserted
`- Active Task: `R9-04`` and `| `R9-04` | R9 | P0 | ACTIVE |` — stale from the
R9-04 close/activation, exactly the class of drift R9-04's own run repaired.
(Verified directly on the pre-change tree: 1197 tests with that one failure —
the post-change 1214 minus this card's 17 new tests.)

Real repository fact: `docs/tasks/done/R9-04-resource-library-shell.md` records
`Status: DONE — independent Review PASS`, and `AGENT_NEXT_TASK.md`,
`docs/tasks/TASK_INDEX.md` and this file's R9-04 section all name `R9-05` as the
sole ACTIVE card. Corrections applied: the contract now pins `R9-05`; the
R9-05 card's own `Status: BACKLOG` line and its `Depends on` line were corrected
to the real state; and the stale `verified_commit` / `verification_source`
header narrative in `docs/status/CURRENT_EXECUTION_STATUS.md` (which still said
R9-04's independent Review was pending) was corrected and extended. No
production behavior changed.

Bookkeeping drift still open (unchanged, not authorized by this card):
`docs/tasks/README.md` says `active/` is where `AGENT_NEXT_TASK.md` points, while
R9-03, R9-04 and R9-05 were all activated in `backlog/`; this card stays where
the pointer names it.

## Independent Review

- **PASS** — the card DoD, the architecture constraints and the declared ownership
  change are satisfied, and the card is archived.
- The first pass returned **CHANGES_REQUIRED** on two *unpinned declarations* — not
  DoD, architecture or ownership defects: the composition root mounting the
  canonical transport, and the panel's filter vocabulary being a second copy of the
  domain's closed sets pinned only against itself. Both were repaired; see
  `## Independent Review Repair` above.
- The re-review reproduced the DoD **24/24** through a mechanism the card's own tests
  do not use (real composition root, isolated database copy, three separate OS
  processes, raw-row read-back, sha256 proof the real data files were untouched),
  and added an axis the card's guard does not cover: `/api/v1/assets/query` is
  registered under all four supported bind modes (`127.0.0.1`, `0.0.0.0`, `::`,
  `localhost`), and the guard's `skipTest` branch is unreachable because
  `canonical_api_is_enabled_for_host` is `bool(host.strip())`.
- All six guards were then proven load-bearing with a mutation harness (read bytes →
  require a unique anchor → one rewrite → run the owning suite → restore → re-verify
  sha256): **6/6 caught**. The three collected after the PASS were the frozen
  query/page records, the 422 response shape, and the `AGENT_NEXT_TASK.md` status
  line — the last is now pinned by
  `tests/test_current_fact_documentation.py::test_active_task_pointer_status_does_not_contradict_the_card`,
  which compares the pointer's `Status:` line against the card's own instead of
  pinning a literal, so the drift cannot recur on the next card.
- Gate after the repair and the collection: **PASS — 1219 tests**, 246 Python AST
  files, 148 JavaScript files, 4 architecture guards, clean `git diff --check`.

## Not carried into the archive

Two non-blocking items the Review recorded and this card deliberately left open, for
`R9-06` to pick up if it needs them: the text filter is a single contiguous substring
over the raw metadata JSON (`"probe 11"` does not find `"Probe asset 11"`, and a
metadata key name matches every asset carrying it); and the panel's
`DEFAULT_PAGE_SIZE` (24) shares a name with the server's (50).

One test-hygiene hazard found while probing, worth knowing before any card drives the
real app: `TestClient(main.app)` **as a context manager** runs the startup hook, which
executes `migrate_asset_library_into_dirs` against the real `data/` tree. The shipped
422-shape guard therefore pins the registered `RequestValidationError` handler directly
rather than driving `main.app` through its lifespan.

## Next Recommended Card

`R9-06`

Do not execute the next card in the same Agent run.
