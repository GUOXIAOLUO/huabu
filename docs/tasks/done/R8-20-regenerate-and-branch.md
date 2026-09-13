# CARD R8-20 — Regenerate and Branch

- Round: R8
- Priority: P1
- Status: DONE — independent Review PASS; archived 2026-09-12
- Depends on: R8-19 (DONE, independent Review PASS)

## Goal

Create new runs/attempt branches from selected results/inputs.

## Before Owner

manual rerun

## After Owner

Execution branch action

## In Scope

- Define regenerate using same snapshot/policy override.
- Preserve lineage to source run/result.
- Show branch in history.

## Out of Scope

- No destructive overwrite of prior run.

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

- [x] Every regeneration has lineage.

## Scope decisions (asked before implementing)

- **Lineage lives in a new canonical object**, not in a new field on
  `ExecutionRun`, matching the R8-19 precedent and the card's "no migration
  unless authorized" clause.
- **Regenerate prepares a branch; it does not execute it.** Starting the new run
  needs an executor and is not what the DoD asks for.
- **The frontend seam is mounted**, not merely registered — `task-rich-node.js`
  provides `mountExecutionBranch` and `node-shell.js` mounts it when the host
  supplies `executionBranchOptions`. This is the R8-19 lesson applied: a seam
  with no consumer is a delivery gap.

## Developer Verification

`./scripts/agent-verify.sh`: **PASS** — 1047 Python tests OK (1042 at the gate
before the mutation review, +5 pins added by it), 216 Python files parsed, 142
JavaScript files checked, 4 architecture guards OK, `git diff --check` clean.

Focused suite: `tests/test_execution_branch.py`, **24 tests**, all passing. The
load-bearing one regenerates a run and then reads the lineage back through a
fresh repository, a fresh service and a fresh HTTP client over the same database
file, and asserts the new run is a *new* run.

### DoD proven through the shipped app (two OS processes)

The focused suite builds its own `FastAPI` app, so the DoD was additionally
proven against the real `main.app` — written by one process, read by a second
process against the same SQLite file:

```text
write: first_status 201, partial_result status 422, second_status 201, stranger 403
read : lineage_root "run-1", lineage_ids 2 (root-first), lineage_ends_at second run,
       raw_branches [["05c00e8f…","run-1"], ["88961100…","05c00e8f…"]],
       raw_has_result "attempt-4", run_count 3, source_revision 1
```

`run_count 3` with `source_revision 1` is the out-of-scope boundary ("no
destructive overwrite of prior run") measured, not merely asserted.

### Mutation-based Git Review

34 probes, one per guarded branch, each applied alone with the focused suite run
against it and the source restored byte-for-byte afterwards (sha256 verified for
all 7 touched files after the run).

- First pass: **25/34 caught**, 9 survivors.
- The 9 survivors were all "guard present, no test aimed at it" rather than
  "guard missing". Five pins were added (`tests/test_execution_branch.py`,
  19 → 24 tests): the branch repository refusing a viewer on `create`,
  `get_for_run` and `list_lineage` directly; a branch refusing to cross
  projects; the new run's `summary` naming its source; the record's immutability
  and metadata safety check; and a hostile row id proving the seam escapes
  `data-branch-id`.
- Second pass: **33/34 caught**, all files verified byte-identical.

The single remaining survivor is an **equivalent mutant**: dropping
`ORDER BY created_at, id` from `list_children` changes nothing, because
`EXPLAIN QUERY PLAN` shows both the ordered and unordered query use the same
`SEARCH execution_branches USING INDEX idx_execution_branches_source
(source_run_id=?)` — the index is already ordered by `(source_run_id,
created_at, id)`. The clause is kept as an explicit statement of the guarantee
so a future index change cannot silently reorder children; it is not
independently observable.

### Defects found and fixed during development

- An unknown source run answered 400 instead of 404: the service collapsed the
  run service's `not_found` into a generic error. It now translates it.
- A partial result name answered **500**, not 422, in the real app: the payload
  validator raised a bare `ValueError`, which pydantic keeps as a live exception
  object in the error context, making the 422 body unserializable. It now raises
  `PydanticCustomError("partial_result", …)`. Found only because the DoD was
  probed through `main.app` rather than through a test-built app.
- Nine guards were present but unpinned (see the mutation review above).

## Final Ownership Evidence

Before:

There was no lineage concept anywhere in `workbench/`. `ExecutionRun` had no
parent field, and the only way to run something again was to create a run by
hand — "manual rerun" — leaving no record of where the second run came from.

After:

`workbench/domain/execution/branch.py` (`ExecutionBranch`, schema
`workbench.execution-branch/1`) owns lineage, backed by
`workbench/repositories/execution_branch_repository.py` (table
`execution_branches`, `UNIQUE(run_id)` so a run has at most one origin, foreign
keys and audit on both ends), `workbench/application/execution_branch_service.py`
(one `regenerate` operation that creates the new run and its lineage together),
and `workbench/api/execution_branches.py`
(`/api/v1/execution-runs/{run_id}/branches`, `.../branches/{branch_id}` and
`.../lineage`). `static/js/workbench/canvas/execution-branch-runtime.js` owns the
client-side description and `execution-branch-api-client.js` is the only
transport.

Duplicate owner removed:

None. The branch record reuses the Result Tray / Result Selection identity
(`attempt_id` + `output_name` + `ordinal`) to name a source result rather than
minting a second result id, and `ExecutionRun` was left untouched — a
regeneration adds a run, it never edits the one it came from.

## Independent Review

**Verdict: PASS.**

The reviewer's probe set was deliberately disjoint from the developer's 34: it
targeted structure, lifecycle and schema rather than value bounds. First pass
**5/26 caught**, which produced four blocking findings.

### Blocking findings (all fixed)

1. **The canonical record's contract was unpinned.** Six guards — unknown field
   refused, `revision >= 1`, `kind` a closed set, `source_ordinal >= 0`,
   `source_output_name` non-empty, `schema_version` a pinned literal — had no
   test at all. The immediately preceding card pins all six for its own record
   (`tests/test_result_selection.py::test_record_rejects_out_of_contract_values`),
   so this was a regression against the established convention, not a judgement
   call. Fixed by mirroring that test and by pinning the schema version as a
   hard-coded literal rather than against the imported constant, which is
   tautological.
2. **A lineage cycle did not provably terminate.** `UNIQUE(run_id)` bounds
   origins, not ancestry, so two runs descending from each other are
   constructible; without the visited set the walk would run to the depth bound
   and report the same records 64 times. Fixed with a test that builds the cycle.
3. **The conflict contract was unpinned at both layers** — neither the service's
   `conflict` code nor the API's 409 mapping was tested, so a client could not
   rely on a duplicate origin being reported as a conflict. Fixed with a 409
   test. Note the premise of the first attempt was wrong: through the API the
   run id is always fresh, so the reachable conflict is the branch record's
   primary key, not `UNIQUE(run_id)`.
4. **The lineage endpoint's authorization had no coverage at the HTTP layer.**
   `/branches` was pinned for a stranger; `/lineage` was not. Fixed.

Also pinned while in the file: the audit payload's `has_result_lineage`, the run
table arriving on a fresh database, unmounting leaving no marker, a non-object
policy override being dropped, and the client's `lineage` blank-run guard,
metadata forwarding and `list` actor header.

Second pass **22/26**, every source restored byte-identical. The four survivors
are non-blocking:

- `PRAGMA foreign_keys` is shadowed by `_project_id`, which rejects an unknown
  run first — the same shadowing the preceding card recorded.
- `self._runs.migrate()` is a **redundant call**: `SqliteExecutionRunRepository.
  __init__` already migrates, so removing the explicit line changes nothing.
- The seam's `REASONS` array and mounted surface being frozen is a convention
  with no consumer that could mutate them, not an observable behaviour.

Focused suite grew 24 → 30 tests. Final gate: 1053 tests, 216 Python AST files,
142 JavaScript files, 4 architecture guards, clean diff.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.

## Next Recommended Card

`R8-21`

Do not execute the next card in the same Agent run.
