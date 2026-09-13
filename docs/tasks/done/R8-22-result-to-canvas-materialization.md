# CARD R8-22 — Result to Canvas Materialization

- Round: R8
- Priority: P0
- Status: DONE — independent Review PASS; archived 2026-09-13
- Depends on: `R8-21` (DONE, independent Review PASS)

## Goal

Materialize selected result explicitly as a Canvas node.

## Before Owner

implicit/legacy output nodes

## After Owner

explicit materialization service/action

## In Scope

- Define materialization command.
- Create generic compatible node/ref.
- Preserve source run/attempt lineage.

## Out of Scope

- Never auto-create one node per output.

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

- [x] Only explicit user/application action creates Canvas node.

## Scope decisions (asked before implementing)

- **The node uses a new canonical definition**, `DefinitionRef(type="workbench",
  id="execution-result", version="1")`, resolved by
  `workbench/application/result_node_definitions.py`. `NodeKind` gained `result`.
  The definition declares **no ports**: a materialized result has not been
  converted into an Asset or an Artifact — that is a later card — so the node
  must not claim to accept or produce typed values it has not been given.
- **The materialized result is not an Asset or an Artifact node** either. It is
  deliberately its own kind, so nothing downstream can mistake it for a
  converted resource.
- **No new table.** The node's lineage lives *on the node*: the four-part address
  in `config["result"]` and the producing run in `provenance_ref`. There is no
  materialization record to keep in step with the node, and no migration.
- **One named result per call, and it must already be selected.** Materializing
  reads `ResultSelection` rather than inventing a second opinion about which
  results matter; an unselected result is a conflict, not a silent success.
- **The frontend seam is mounted**, not merely registered — the R8-19 lesson.

## The persistence constraint that shaped the design

The only Canvas node store is the Legacy JSON one, and
`LegacyJsonNodeCreationRepository.create_node` refuses any definition that is not
an approved Legacy shape, so a canonical node could not be persisted at all. This
was not visible when the scope questions were answered, so it was raised and
decided separately.

The decision was: **write the canonical node into the same `canvas["nodes"]`
list, under the same `mutate_if_current` lock, with the same idempotency
convention** — via a new `CanonicalJsonNodeCreationRepository` rather than by
widening the Legacy one, so neither writer is allowed to accept what the other
must refuse. Three consequences are deliberate:

- The node carries a marker `type` (`workbench-result`) that Legacy consumers see
  but never produce, and repeats `x`/`y`/`w`/`h` alongside the canonical record
  so a consumer that only understands Legacy geometry can still place it.
- The canonical record is stored whole, so reading it back is validation rather
  than guesswork. `LegacyCanvasAdapter.node_to_record` routes the marker to
  `canonical_adapter.record_from_payload`, which is why the existing
  `GET /api/v1/canvases/{canvas_id}/nodes/{node_id}` answers honestly instead of
  flattening the node into a Legacy one.
- A pre-existing Legacy node in the same list is unaffected; a test pins this.

## Developer Verification

`./scripts/agent-verify.sh`: **PASS** — 1117 Python tests OK (1079 before this
card, +38 focused), 226 Python files parsed, 146 JavaScript files checked, 4
architecture guards OK, `git diff --check` clean.

Focused suite: `tests/test_result_materialization.py`, **38 tests**, all passing.
The load-bearing one materializes one result and asserts the node's kind, its
canonical definition, its four-part address, the producing run in
`provenance_ref`, and that exactly one node was added. Its neighbours assert the
other half of the DoD: an unselected sibling, a result nobody named, and a run
with no selections all refuse to produce a node.

### DoD proven through the shipped app (two OS processes)

The focused suite builds its own `FastAPI` app, so the DoD was additionally
proven against the real `main.app` — written by one process, read by a second
process against the same Canvas file:

```text
write: created_status 201, created_kind result,
       created_definition {workbench, execution-result, 1},
       created_result [run-1, attempt-1, poster.png, 0], created_provenance run-1,
       second_status 201, unselected 409, unnamed 404, no_actor 401, zero_revision 422
read : stored_node_types [workbench-result, workbench-result],
       stored_kinds [result, result], stored_provenance [run-1, run-1],
       stored_identities [[run-1, attempt-1, poster.png, 0], [run-1, attempt-2, thumb.png, 0]],
       stored_geometry [[40, 50, 320, 240], [40, 50, 320, 240]],
       audit_sources [result_materialization, result_materialization]
```

`stored_identities` shows each node names exactly the one result it was asked
for, and `audit_sources` shows both were created by an explicit materialization
rather than by running something.

### Mutation-based Git Review

44 probes, one per guarded branch, each applied alone with the suites that own the
code under test run against it and the source restored byte-for-byte afterwards
(sha256 verified for all 11 touched files).

- First pass: **41/44 caught**, 3 survivors.
- All three were pinned (`tests/test_result_materialization.py`, 37 → 38 tests);
  second pass **44/44**, every file verified byte-identical.

Two of the three survivors were the same lesson in two places: **a guard that a
lower layer also enforces looks equivalent, and a mutation probe cannot tell the
difference.** The service refuses `expected_revision=0`, and so does
`NodeCreationService._validate_command`; the API bounds `ordinal >= 0`, and so
does the service `_validate`. Removing either outer guard changed no observable
behaviour. They were pinned by making the layering observable instead: a test
injects a recording node-creation service and asserts the service refuses before
it ever asks for a node, and the API test now asserts that a payload rejection
produces FastAPI's validation *list* rather than the service's coded object.

The third was ordinary under-testing: the seam escaped the node id, but no test
gave it an id that needed escaping.

### A tooling trap worth recording

The first mutation run reported **44/44 caught in 22 seconds**, which was wrong.
The harness had been launched with a Rosetta (x86_64) interpreter, so the child
process ran the project's arm64 venv under the wrong architecture,
`pydantic_core` and `PIL` failed to load, and every suite died at import — a
non-zero exit that looked exactly like a caught probe. Two corrections:

- **Run the harness with the venv's own interpreter**, never a differently-built
  one, whenever it spawns the project's Python.
- **Count the tests.** The harness now parses `Ran N tests` and refuses to accept
  a run shorter than the expected 77 as evidence. A collection error and a test
  failure both exit non-zero; only one of them is a result.

## Independent Review

**Verdict: PASS.**

The reviewer's set of 13 probes was deliberately on different axes from the
developer's 44: schema shape and closed sets, lifecycle and teardown,
persistence serialisability, published-contract drift, and the error-code
contract per cause. Baseline 95 tests green across the five suites that own the
code under test. First pass **6/13 caught**, second pass **12/13** after the gaps
below were pinned. Focused suite grew 38 → 48 tests.

### Blocking finding: the published node schema no longer matched the domain

`schemas/node-record/node-record.v1.schema.json` enumerates `kind`, and it was
missing **`result`** — the kind this card adds — and **`collection`**, which had
already drifted out before this card. A consumer validating against the
published schema would have rejected every result node this card produces.

No probe could have found this: it is a *missing declaration*, not a guard that
can be removed. The existing test checked only the `schema_version` constant, so
the drift was invisible to the whole suite.

Fixed by adding both kinds to the enum, and — more importantly — by making the
contract self-enforcing: `tests/test_node_record.py` now compares the published
enum against `get_args(NodeKind)` for exact equality, so a future kind cannot
drift out again.

### Six contract gaps in new canonical code, all pinned

- `ExecutionResultIdentity` declared `frozen=True`, `extra="forbid"` and an
  `output_name` bound of 255, and **none of the three was tested**. The identity
  is stored inside a node's `config`, which is a plain dict, so the record's own
  guarantees are the only thing protecting it.
- `record_from_payload` copies its input before stripping the store-only keys.
  Without that copy it **strips them from the canvas still held in memory** — a
  real corruption path, not a stylistic one.
- `CANONICAL_NODE_REQUEST_METADATA_KEY` is a **persisted format constant** shared
  with the Legacy writer, and was only ever referenced through the constant that
  defines it — the same tautology that had already been fixed for the `type`
  marker, missed here on the second constant.
- The seam's `destroy` cleared the host but did not detach it, so a later
  `hydrate` would render into a torn-down host.

### Three capability tests the developer set did not cover

- **The generic node-creation route cannot create a canonical result node.** It
  resolves definitions through `LegacyDefinitionRegistry` and answers
  `definition_not_found`. This is the DoD's other half: not only does only an
  explicit action create the node, no other route can.
- A **replayed request id returns the node it first created** even when the
  retry names a different result, so a retry cannot silently materialize the
  wrong thing.
- A canonical node **survives a Legacy writer mutating the same canvas** — the
  two share one node list, so this had to be shown rather than assumed.

### Non-blocking survivor

One: the API maps `invalid_request` to 422, but the payload's own bounds reject
every value that would reach it, so the branch is unreachable through the API.
It is kept as defence in depth.

### An observation for whoever wires the renderer registry

The result node declares `RendererRef(id="result", version="1")`, and no
renderer is registered under that id — but no production code resolves renderers
through `RendererRegistry` at all today (only tests do), and the page builds its
records with a hard-coded `legacy@1`. The node is therefore rendered by the seam
this card mounts. This was a deliberate choice, recorded here so the gap is
closed by whoever makes the registry live rather than discovered then.

### Defects found and fixed during development

- `ExecutionResultIdentity.matches` was written and never called. Dead code that
  no probe could flag was removed rather than shipped.
- Two guards repeated a lower layer and were unpinned (see the mutation review).
- Stored format constants were initially asserted through the constant they
  define, which makes the assertion a tautology: changing the marker or the
  creation-source value would have passed. Both are now asserted as literals.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

A produced result could only reach a Canvas implicitly — by being rendered into a
Legacy output node as a side effect of running something. There was no action that
materialized a result: the only node-creation path is
`NodeCreationService`, and it is wired to Legacy adapters whose repository
whitelist rejects every canonical definition, so no canonical result node could
have been created or persisted. `ResultSelection` (R8-19) recorded which results
the user chose and R8-21 learned to consume that, but nothing could put a chosen
result onto a Canvas.

After:

`workbench/domain/execution/result_identity.py` owns the four-part address of one
result. `workbench/application/result_materialization_service.py` owns the one
operation — it reads the run, refuses another project's result, requires that the
named result is already selected, and builds the node through the existing
`NodeCreationService` with `NodeCreationSource.RESULT_MATERIALIZATION`, putting
the address in `config["result"]` and the run in `provenance_ref`. The definition
lives in `workbench/application/result_node_definitions.py`;
`workbench/repositories/canonical_json_node_repository.py` persists it alongside
Legacy nodes under the same lock, and
`workbench/domain/canvas/canonical_adapter.py` reads it back losslessly.
`workbench/api/result_materializations.py` exposes
`POST /api/v1/canvases/{canvas_id}/result-nodes`. On the client,
`result-materialization-runtime.js` describes a materialized node and
`result-materialization-api-client.js` is the only transport; both are mounted
through `task-rich-node.js` and `node-shell.js`.

Duplicate owner removed:

The result identity is the same four parts Result Selection rates and Branch
descends from — no second result id was minted. Two smaller duplications were
removed rather than added to: the persisted `type` marker and the
idempotency-key constant are defined once in
`workbench/domain/canvas/models.py` and shared by the writer and the reader, and
the Legacy writer was left alone instead of being widened to admit canonical
shapes. `NodeCreationService` gained only an optional `provenance_ref` on its
command, so every existing creation path is unchanged.

## Next Recommended Card

`R9-01`

Do not execute the next card in the same Agent run.
