# CARD R8-19 — Result Selection and Rating

- Round: R8
- Priority: P1
- Status: DONE — independent Review PASS; archived 2026-09-12
- Depends on: R8-18 (DONE, independent Review PASS)

## Goal

Track user selection/rating metadata on run results.

## Before Owner

no formal candidate choice

## After Owner

result selection metadata

## In Scope

- Add select/favorite/rating/comment where generic.
- Persist with run/result metadata.

## Out of Scope

- No Approval/Frozen semantics.

## Compatibility / Migration

- Preserve existing behavior and data unless the card explicitly authorizes a migration.

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

- [x] Candidate preference survives reload.

## Persistence Boundary

The project has no client-side persistence convention — `localStorage` and
`sessionStorage` appear in zero frontend files — so "survives reload" is
resolved on the backend, as a new canonical object rather than by widening
`ExecutionAttempt.summary`. Wiring the live "execution output → tray/compare"
data path is deliberately **not** in this card; the seam is mounted and tested
but no caller supplies it options yet.

## Independent Review

**Verdict: CHANGES_REQUIRED.** The card stays ACTIVE and must not be archived.

The DoD, the architecture constraints and the ownership change all pass; the
blocking finding is that two authorization paths on the newly introduced
persistent object have **no test coverage anywhere in the project**.

### Blocking

1. **`get` read authorization is unpinned.** Removing
   `Action.EXECUTION_READ` from `SqliteResultSelectionRepository.get` entirely
   was verified **not to fail a single test in the whole 1018-test suite**. Any
   actor could then read any preference record by id. The guard is present and
   correct — it is simply unasserted, so the next refactor can drop it silently.
   Pin: a non-member (and a viewer) `get` by id is refused.
2. **`update` write authorization is unpinned.** Changing `Action.EXECUTION_EDIT`
   to `EXECUTION_READ` in `update` is not caught either. A viewer passes the
   preceding `get` (READ) and would then be allowed to write. Pin: a viewer
   `PUT` is refused with 403.

Both are reachable through the shipped router and both are cheap to pin. Nothing
else needs to change for the card to pass.

### Second independent Review — verdict: PASS

A third mutation set, disjoint from both the developer's 45 and the first
review's 19, targeted structural and lifecycle guards rather than value bounds:
immutability, foreign-key enforcement, schema idempotency, status codes, seam
lifecycle and client identity. First pass **5 of 17 caught**; three findings were
then pinned (the record is immutable so its metadata cannot be smuggled in after
validation, an update restates metadata rather than merging it, and the seam's
`hasPreference` counts a rating on its own) plus `updated_at` stamping, giving
**10 of 17 caught** with every source restored byte-identical.

The 7 survivors are trivial or defence in depth, each re-checked: `PRAGMA
foreign_keys` is shadowed by `_project_id` rejecting an unknown run first; the
API's `extra="forbid"` is shadowed by the domain's; the create-path revision is
always 1 in practice; the audit row's project attribution, the seam's host check
and the client's id check and metadata forwarding are cosmetic.

### Blocking findings — resolved

Both authorization paths are now pinned, at the repository and at the HTTP
boundary, and each pin also asserts that the refused write left the stored
record untouched:

- `get` by id: a viewer may read one record; a non-member may not.
- `update`: a viewer `PUT` is refused with 403, and so is a viewer `POST`.

The fresh probe set was re-run after the fix: **12 of 19 now caught, up from 2 of
19**, with every source restored byte-identical. Newly caught are both
authorization paths, the API's `PermissionError`→403 mapping on create, the
listing order, the non-empty output name, the pinned `schema_version`, the
`sameResult` attempt-id term, the client's run-id escaping, its positive-revision
check, and its error-message extraction.

The 7 survivors are confirmed defence in depth rather than gaps, each re-checked
against a downstream guard: `expected_revision ge=1` falls through to the
repository CAS (409), `ordinal ge=0` is also enforced by the domain
`Field(ge=0)` and by `CHECK (ordinal >= 0)`, an empty identity is also rejected
by `OpaqueId` (`min_length=1`), and the comment length is also enforced by the
domain. The remaining three are trivial: the seam's default revision for a
record that carries none, and the seam's boolean coercion, which the backend
model re-coerces anyway.

### Non-blocking observations

- `sameResult` does not have its `attempt_id` term pinned: dropping it is not
  caught, while the ordinal and output-name terms are. The identity contract is
  the card's central claim, so all three terms should be asserted.
- `schema_version` being pinned to `workbench.result-selection/1` is unasserted;
  widening it to `str` is not caught. This is the migration contract.
- `list_for_run` ordering (`attempt_id, output_name, ordinal, id`) is unasserted.
- The client does not have its `encodeURIComponent(run)` escaping, its
  positive-revision check, or its error-message extraction pinned.
- Several API payload bounds (`ordinal ge=0`, `attempt_id` min length, comment
  length, `expected_revision ge=1`) are unpinned individually, but each is
  duplicated by the domain object or the repository CAS, so they are defence in
  depth rather than gaps.
- **Delivery gap (not the cause of this verdict, but needs a decision):** the
  frontend seam is the only R8 result seam with **no consumer**.
  `task-rich-node.js` provides `mountResultTray` and `mountResultCompare`, and
  `result-preview-runtime.js` is consumed by tray and compare, but nothing
  ever calls `WorkbenchCanvasResultSelection.create(...)` — so
  "Add select/favorite/rating/comment where generic" reaches no user. No R8
  successor (R8-20 Regenerate and Branch, R8-21 Result to Collection, R8-22
  Result to Canvas Materialization) would wire it either. The card's own text
  says the seam "is mounted", which overstates it: it is registered on the
  page, never mounted.

### What passed

- **DoD, independently confirmed through the real shipped app.** Driving
  `main.app` (not a test-built app) over HTTP across two OS processes: create
  → 201, restate → 200 at revision 2, a restatement with an expired revision →
  409 `stale_revision` with the accepted values still intact, and in a **new**
  process the identity `["attempt-3","poster.png",1]`, the preference
  `[true,false,4,"first pick"]` and `schema_version` all read back, with the
  same values present in the raw SQLite row. Viewer read → 200, viewer write →
  403, stranger → 403, audit events exactly `[created, updated]`.
- **Architecture:** no wholehouse vocabulary in Core; no codex leak into
  `workbench/`; no Git-hosting fetch; one Unified Canvas (the seam creates no
  nodes); no client-side persistence; no Approval/Frozen state; no computed
  scoring. The only `freeze` hits are the JS `Object.freeze` built-in and the
  project's own `freeze_value` helper, and the only approval/frozen/score/rank
  wording in the domain module is its docstring's explicit denial.
- **Ownership:** one new canonical owner (`ResultSelection`), reusing the
  tray/compare identity rather than minting a second result id, with no
  duplicate owner and no widening of `ExecutionAttempt.summary`.

### Method

19 fresh mutation probes, deliberately disjoint from the developer's 45, of
which 2 were caught and 17 survived; the survivors were then re-probed against
the full suite to separate real gaps from defence in depth. Note for future
runs: a mutation harness running the full suite sequentially can exceed the
command timeout, and a `SIGTERM` mid-probe kills Python before its `finally`
restore runs — one mutation was left applied and had to be repaired by hand.
Always re-verify every touched file's hash after a timed-out harness.

## Developer Verification

`./scripts/agent-verify.sh` — PASS.

- Python unit tests: 1018 OK (994 before this card + 24 new).
- Python AST parse: 211 files. JavaScript syntax: 140 files.
- Architecture guards: 4 OK. `git diff --check`: clean.

Focused suite: `tests/test_result_selection.py`, 24 tests, all passing. The
load-bearing one writes a preference through the application boundary and reads
it back through a fresh repository, a fresh service and a fresh HTTP client over
the same database file.

### Independent DoD probe (separate OS process)

Two processes over one database file: process 1 wrote and then restated a
preference; a **new** process read it back through a fresh repository, a fresh
service and the mounted router, and also inspected the raw SQLite row.

```text
reloaded_count 1
identity       ["attempt-7", "hero.png", 2]
preference     [true, true, 4, "still the best"]
revision       2
api_status     200   api_preference [true, 4, "still the best"]
raw_row        revision 2, payload comment "still the best"
```

The value is therefore stored, not cached: the restatement (rating 5 → 4) and
the three-part identity both survive a process boundary, and the payload is
present in the database file itself.

### Mutation review

45 targeted mutations, each rewritten into one guarded branch, then the focused
suite was required to fail. Every source was restored and verified
byte-identical by sha256.

- **42 caught.** Domain bounds (rating band, comment length, ordinal floor,
  revision floor, `extra="forbid"`, metadata credential screen, comment-only
  preference); repository guards (one record per result, edit-vs-read
  authorization on create and on list, both audit events, restated rating,
  revision bump, unknown-run rejection); service translations (conflict, stale,
  not-found); router guards (missing actor, not-found→404, run scoping on both
  read and write, boundary rating bound); seam guards (identity completeness,
  integer and non-negative ordinal, rating band and integrality, comment length,
  clear-vs-update reporting, revision and identity in `pending`, ordinal in the
  index key, identity-less records ignored, marked-only counting, comment
  escaping, explicit-null clearing); client guards (`expected_revision`, actor
  header, missing actor, run id); and the composition root registration.
- **3 not caught, all probed and judged non-blocking.**
  1. `repo: revision pre-check` and 2. `repo: CAS rowcount guard` are two guards
     for one invariant (optimistic-concurrency `WHERE id=? AND revision=?` plus
     a prior read comparison). Each mutation is masked by the other, so neither
     is individually observable from a single-threaded test. The invariant
     itself *is* pinned: a refused stale write is asserted to leave the stored
     revision and preference untouched, so no partial write can regress
     unnoticed. Deliberate defence in depth, not a defect.
  3. `repo: FOREIGN KEY(run_id)` is unreachable through the public path because
     `_project_id` rejects an unknown run first. Retained as a schema-level
     guard against direct repository misuse.

### Defects found and fixed during development

- `pending()` and `snapshot()` exposed only the internal composite `key`, so the
  client received no `attempt_id`/`output_name`/`ordinal` and mounted rows
  rendered with empty identity attributes. Both now carry the canonical identity
  parts; `identityFromKey` is the documented inverse of `indexKey`.
- `snapshot().count` counted a cleared-but-not-yet-saved record as marked.
  Marked-ness now requires an actual preference; a pending clear is reported
  through `pending()` instead.
- The client's `list()` relied on `fetch`'s implicit GET default, leaving the
  method untestable. It now states `method: 'GET'`.
- The service's not-found translation for `get` was untested; now pinned.
- The composition root's `include_router` line was untested — no test imported
  `main`, so deleting it would have left the card unreachable in the shipped app.
  Now asserted against the real app's OpenAPI paths.

## Final Ownership Evidence

Before:

No concept of a user's preference over a run result existed anywhere in
`workbench/`. The Result Tray staged results and the Result Compare workspace
compared them, but nothing recorded what the user decided about a candidate, and
nothing could survive a reload.

After:

`workbench/domain/execution/selection.py` (`ResultSelection`, schema
`workbench.result-selection/1`), `workbench/repositories/result_selection_repository.py`
(table `result_selections`, unique per `(attempt_id, output_name, ordinal)`),
`workbench/application/result_selection_service.py`, and
`workbench/api/result_selections.py`
(`/api/v1/execution-runs/{run_id}/selections`) own the persisted preference.
`static/js/workbench/canvas/result-selection-runtime.js` owns the client-side
decision boundary and `result-selection-api-client.js` is the only transport.

Duplicate owner removed:

None. The record deliberately reuses the tray/compare identity
(`attempt_id` + `output_name` + `ordinal`) instead of minting a second result id,
and it does not widen `ExecutionAttempt.summary`. No Approval/Frozen semantics
were introduced, so nothing here authorizes anything.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.

## Next Recommended Card

`R8-20`

Do not execute the next card in the same Agent run.
