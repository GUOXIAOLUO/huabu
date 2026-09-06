# CARD R4-02 — SQLite / Legacy Canvas Reconciliation

- Round: R4
- Priority: P0
- Status: DONE
- Depends on: R4-01
- Activated: 2026-09-06 (agent run)
- Completed: 2026-09-06T17:37+08:00

## Goal

Re-verify SQLite and Legacy Canvas data so persistence work starts from a known-safe dataset.

## Before Owner

Potential dual/stale data representations

## After Owner

Verified SQLite authority dataset + reconciliation evidence

## In Scope

- Compare Canvas counts and IDs.
- Compare payloads, node positions, edges and metadata.
- Identify Legacy-only, SQLite-only and unexpected rows.
- Do not overwrite unknown real data.

## Out of Scope

- No automatic destructive repair.
- No revision protocol migration yet.

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

Add or run the smallest behavioral tests that prove this card's exact goal.
Do not rely only on source-string checks when runtime behavior can be tested.

## Regression

Run:

```bash
./scripts/agent-verify.sh
```

## Definition of Done

- [x] Counts and differences are explicitly reported. (Legacy `data/canvases`: 23 files / 23 unique ids — 9 classic, 14 smart, 6 trashed; SQLite: 23 rows — 17 active, 6 deleted. 23/23 payload comparisons matched: zero payload-key, node-position, connection, or trash-state differences; 0 legacy-only and 0 sqlite-only ids; 0 unexpected rows. Report: `data/r4-canvas-reconciliation-report.json`.)
- [x] Every unexpected row is classified or left safely untouched. (The reconciler classifies duplicate legacy ids, payload-id mismatches, title-column mismatches, legacy project mismatches, and itemizes per-node position/connection/trash drift; the live run found none. The live database was byte-identical before and after the run — sha256 `3cca0054…` — because the tool opens SQLite with a `mode=ro` URI, so nothing was overwritten and no destructive repair occurred.)
- [x] Authority state is verified. (`authority_state.canvas_authority = 'sqlite'`, updated 2026-09-05T00:06:45Z; consistent with default canonical routing.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Potential dual/stale data representations — no read-only reconciliation
diagnostic existed; the migration tool's report mode imports (writes) by design,
so it could not verify the live dataset without risking overwrites.

After: Verified SQLite authority dataset plus a reusable strictly read-only
reconciler (`tools/reconcile_canvas_authority.py`) with behavioral tests
(`tests/test_canvas_authority_reconciliation.py`) and an evidence report
(`data/r4-canvas-reconciliation-report.json`, following the tracked
`data/r4-repair-migration-report.json` precedent) proving Legacy and SQLite
converged with zero drift under `sqlite` authority.

Duplicate owner removed: none — no runtime ownership changed; the migration tool
keeps its import/compare role and Legacy JSON remains the bounded
import/rollback adapter, so `R4_OWNERSHIP_MATRIX.md` was not modified.

## Next Recommended Card

`R4-03`

Do not execute the next card in the same Agent run.
