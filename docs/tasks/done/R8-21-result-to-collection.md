# CARD R8-21 — Result to Collection

- Round: R8
- Priority: P1
- Status: DONE — independent Review PASS; archived 2026-09-12
- Depends on: `R8-20` (DONE, independent Review PASS)

## Goal

Allow selected results to be added to a Collection explicitly.

## Before Owner

manual copy/Canvas nodes

## After Owner

explicit collection materialization

## In Scope

- Create references/items from selected outputs.
- Preserve run/result lineage metadata.

## Out of Scope

- No formal Asset/Artifact conversion yet.

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

- [x] Selected results can populate a Collection without Canvas node creation.

## Scope decisions (asked before implementing)

- **`execution_result` becomes a first-class member of the Collection type
  system**, rather than lineage being hidden in `item.metadata`. The card's
  out-of-scope clause rules out converting a result into an Asset or an
  Artifact, so the existing reference kinds cannot be borrowed without lying
  about what the item holds.
- It is realised as its own cell type, not as a `CollectionReferenceCell`:
  every other reference points at a resource by a *single* id, whereas a result
  is named by four parts, so a single `reference_id` would over- or
  under-address it. `execution_result` is therefore added to
  `CollectionValueType` (what a column may hold) but deliberately **not** to
  `CollectionReferenceType`.
- **"Selected" is read from Result Selection** (`selected=True`) rather than
  passed in, so the card does not mint a second notion of selection.
- **The operation appends to an existing Collection**, revision-checked. No new
  table, and `Collection` is not otherwise reshaped.
- **The frontend seam is mounted**, not merely registered — the R8-19 lesson.

## Developer Verification

`./scripts/agent-verify.sh`: **PASS** — 1078 Python tests OK (1053 before this
card, +25 focused), 219 Python files parsed, 144 JavaScript files checked, 4
architecture guards OK, `git diff --check` clean.

Focused suite: `tests/test_result_collection.py`, **25 tests**, all passing. The
load-bearing one collects a run's selected results and then asserts both halves
of the DoD: the items carry the four-part result identity, and no Canvas was
touched at all.

### DoD proven through the shipped app (two OS processes)

The focused suite builds its own `FastAPI` app, so the DoD was additionally
proven against the real `main.app` — written by one process, read by a second
process against the same SQLite file:

```text
write: added_status 200, added_revision 2, added_items 2, stranger 403, zero_revision 422
read : stored_revision 2, stored_item_count 2,
       stored_identities [["run-1","attempt-1","poster.png",0], ["run-1","attempt-2","thumb.png",0]],
       stored_cell_types ["execution_result","execution_result"],
       column_types ["execution_result"], canvas_count 0
```

`canvas_count 0` is the out-of-scope half of the DoD measured on disk rather
than asserted, and `stored_cell_types` shows the results were collected as
results rather than converted into Assets or Artifacts.

### Mutation-based Git Review

33 probes, one per guarded branch, each applied alone with the focused suite run
against it and the source restored byte-for-byte afterwards (sha256 verified for
all 6 touched files after the run).

- First pass: **25/33 caught**, 8 survivors.
- Seven of the eight were "guard present, no test aimed at it" and were pinned
  (`tests/test_result_collection.py`, 22 → 25 tests): the result cell's
  out-of-contract values, a taken column id, an aggregate that cannot be
  validated, the API's `expected_revision >= 1`, and the seam refusing a result
  whose name is an empty string.
- Second pass: **32/33**, all files verified byte-identical.

The one survivor is an **unreachable guard**: the service translates the
selection service's `not_found`, but `ExecutionRunService.get` has already
rejected an unknown run against the same database a few lines earlier, so
`list_for_run` cannot raise it. It is kept as defence in depth.

### Defects found and fixed during development

- `_validate` let a raw pydantic `ValidationError` escape the service, which the
  API would have answered with a 500. It now raises
  `ResultCollectionServiceError("invalid_collection", …)`.
- Seven guards were present but unpinned (see the mutation review above).

## Independent Review

**Verdict: PASS.**

The reviewer's probe set was deliberately disjoint from the developer's 33: it
targeted schema shape, lifecycle, and whether the seam actually honours what the
service allows. First pass **8/22 caught**, which produced one functional defect
and four coverage findings.

### Blocking finding: the seam could not use a custom column key

The service and the API both let a caller choose the column results land in, but
the seam hard-coded it — `recordFrom` read only `values.result`, and the
mounted `requestFrom` always sent `result`. A Collection that collected under
`chosen` would have been rendered empty, and no request could have asked for it:
a delivered capability that was unreachable from the only client. A mutation
probe cannot discover a missing feature; this was found by reading the seam
against the service contract.

Fixed by threading a column key through `create({columnKey})`, `recordFrom` and
the mounted `requestFrom`, and pinned by a test that hydrates two items under
two different columns and asserts only the chosen one is rendered.

### Other findings (all pinned)

- The result cell's `attempt_id` bound was untested — every part of the identity
  is required, since a blank attempt would point at the wrong result.
- The API payload's `run_id` and `column_key` bounds were untested.
- The seam's hydrated `revision` was never asserted, though it is what a further
  append has to name.
- The client's `Content-Type` header was never asserted.

Second pass **13/22**, and a further **3/9** once two corrections were applied
(below), giving **16/22**.

### Two corrections the reviewer had to make

- **A probe set that runs only the focused suite under-reports.** Seven probes
  targeted the pre-existing `Collection` aggregate, which is covered by
  `tests/test_collection_domain.py`; run against the focused suite alone they
  all survived, and two of them (`an item is closed`, `schema column keys are
  unique`) are in fact already pinned there. The measure has to include the
  suite that actually owns the code under test.

### Non-blocking survivors

- Five guards on the pre-existing `Collection` aggregate — the schema version as
  a pinned literal, immutability, `revision >= 1`, `order >= 0`, and unique
  column *ids* — have no test anywhere. They predate this card, the card is not
  authorized to reshape `Collection`, and `test_collection_domain.py` has only
  four tests. Recorded here as an observation for whoever owns that aggregate
  rather than silently expanded into.
- The seam's mounted surface being frozen is a convention with no consumer that
  could mutate it, not an observable behaviour.

Focused suite grew 25 → 26 tests.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

A produced result could only reach a Collection by hand — copying it into Canvas
nodes and collecting those — because `Collection` had no way to point at a
result at all: its reference kinds are Asset, Artifact, entity and Collection,
and converting a result into an Asset or an Artifact is explicitly out of scope
for this card. `ResultSelection` (R8-19) already recorded which results the user
selected, but nothing consumed it.

After:

`workbench/domain/collection/models.py` gained `CollectionExecutionResultCell`,
so `execution_result` is a declared value type and an item can name the result
it came from. `workbench/application/result_collection_service.py` owns the one
operation — it reads the run's selected results, makes sure the Collection's
schema can hold results under the requested key without retyping a column that
already exists, and appends the items through the existing revision-checked
`CollectionService.update`. `workbench/api/result_collections.py` exposes
`POST /api/v1/collections/{collection_id}/results`. On the client,
`result-collection-runtime.js` describes a collected result and
`result-collection-api-client.js` is the only transport; both are mounted
through `task-rich-node.js` and `node-shell.js`.

Duplicate owner removed:

None. The result identity is the same four parts Result Selection rates and
Execution Branch descends from — no second result id was minted — and the
Collection aggregate itself was not reshaped: only one new value type was added
to a closed set, which widens it without invalidating any stored Collection.

## Next Recommended Card

`R8-22`

Do not execute the next card in the same Agent run.
