# CARD R4-03 — SQLite Authority Split-Brain Guard

- Round: R4
- Priority: P0
- Status: DONE
- Depends on: R4-02
- Activated: 2026-09-06T17:43+08:00
- Completed: 2026-09-06T17:59+08:00

## Goal

Prevent normal runtime from silently routing writable Canvas traffic to Legacy JSON when canonical authority is SQLite.

## Before Owner

Feature-flag/runtime repository selection

## After Owner

Explicit canonical authority policy

## In Scope

- Characterize canvas_repository() and authority_state behavior.
- Add a small authority resolver/policy seam.
- When authority=sqlite, normal runtime must use SQLite.
- Retain explicit Legacy migration/recovery/import paths.

## Out of Scope

- Do not delete Legacy compatibility.
- Do not implement frontend revision cutover.

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

- [x] SQLite authority cannot silently select writable Legacy. (`canvas_repository()` routes through the explicit policy on every call; startup fails fast — module-level node-API wiring, `startup_event`, and `__main__` — with `CanvasAuthoritySplitBrainError`, clean message, exit 1, when `WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED=false` while `authority_state=sqlite`. Live check: refusal with database byte-identical, sha256 `3cca0054…`.)
- [x] Explicit recovery/import remains available. (Legacy routing still works when authority is `legacy_json` or unavailable — wiring test `test_r4_legacy_recovery_and_migration_paths_stay_available_when_authority_inactive`; `project_canvas_migration_service()`, `tools/migrate_project_canvas.py`, and the tested lossless rollback export are untouched.)
- [x] Focused behavior tests pass. (11 new tests: resolver matrix, tolerant reader, wiring refusal, mid-flight authority-activation detection, recovery availability, startup wiring; full regression 308 tests PASS.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Feature-flag/runtime repository selection — `canvas_repository()` branched
only on `WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED`, so a disabled flag silently
returned writable Legacy JSON even with `authority_state=sqlite` (the documented
morning split-brain hazard).

After: Explicit canonical authority policy — one seam
(`workbench/application/canvas_authority_policy.py`) owns the routing decision and
is consulted per call plus enforced at all three startup layers; the ownership
matrix Canvas-persistence row now names the policy seam as the only repository
selection path.

Duplicate owner removed: the routing flag's silent legacy-fallback branch
(`flag false → writable Legacy regardless of authority`) no longer exists; the
flag keeps meaning only inside the policy when authority is inactive.

## Next Recommended Card

`R4-04`

Do not execute the next card in the same Agent run.
