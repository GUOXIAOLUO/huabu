# CARD R4-03 — SQLite Authority Split-Brain Guard

- Round: R4
- Priority: P0
- Status: ACTIVE
- Depends on: R4-02
- Activated: 2026-09-06T17:43+08:00

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

- [ ] SQLite authority cannot silently select writable Legacy.
- [ ] Explicit recovery/import remains available.
- [ ] Focused behavior tests pass.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-04`

Do not execute the next card in the same Agent run.
