# CARD R4-05 — Canonical Canvas API

- Round: R4
- Priority: P0
- Status: BACKLOG
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

- [ ] Canonical API reads revision.
- [ ] CAS success increments revision.
- [ ] Stale expected_revision returns conflict.
- [ ] Old API remains characterized.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-06`

Do not execute the next card in the same Agent run.
