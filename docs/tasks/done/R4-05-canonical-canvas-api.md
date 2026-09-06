# CARD R4-05 — Canonical Canvas API

- Round: R4
- Priority: P0
- Status: DONE
- Activated: 2026-09-06T18:12+08:00
- Completed: 2026-09-06T18:22+08:00
- Depends on: R4-04

## Goal

Introduce a canonical Canvas transport API with explicit logical revision while keeping old endpoints as compatibility.

## Before Owner

main.py/legacy-shaped Canvas transport

## After Owner

workbench/api/canvases.py canonical seam

## In Scope

- Characterize current GET/PUT Canvas endpoints.
- Add canonical GET returning canvas + revision + updated_at.
- Add PUT with expected_revision CAS.
- Return explicit stale revision conflict information.

## Out of Scope

- Do not remove old compatibility API.
- Do not migrate all frontend callers yet.

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

- [x] Canonical API reads revision. (`GET /api/v1/canvases/{canvas_id}` returns the lossless payload plus canonical `revision`, `updated_at`, `project_id`, `title`, `deleted` from `CanvasRecord`.)
- [x] CAS success increments revision. (`PUT` with matching `expected_revision` performs full-payload replace via `replace_canvas_payload` and returns revision N+1; behavioral test verifies 1→2 with the persisted read-back.)
- [x] Stale expected_revision returns conflict. (409 with explicit `error: stale_revision`, `expected_revision`, `current_revision`, `current_updated_at`.)
- [x] Old API remains characterized. (Legacy `GET /api/canvases/{id}` keeps its `{"canvas": ...}` shape with no `revision` key — pinned by test; legacy PUT `base_updated_at` semantics untouched, existing characterization tests still pass.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: main.py/legacy-shaped Canvas transport — reads carried no logical
revision and optimistic concurrency was `updated_at`-based inside the legacy
route handlers.

After: workbench/api/canvases.py canonical seam — `/api/v1/canvases/{canvas_id}`
GET/PUT with explicit logical revision and CAS, authority-gated (503 without
active SQLite authority), registered in the loopback-gated versioned API block;
ownership matrix revision/CAS row updated to name the canonical transport.

Duplicate owner removed: none yet — the legacy transport remains the bounded
compatibility path by card scope; browser callers migrate in R4-06/R4-07, after
which the duplicate can be retired.

## Next Recommended Card

`R4-06`

Do not execute the next card in the same Agent run.
