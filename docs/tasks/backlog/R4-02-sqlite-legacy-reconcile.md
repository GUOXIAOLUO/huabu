# CARD R4-02 — SQLite / Legacy Canvas Reconciliation

- Round: R4
- Priority: P0
- Status: BACKLOG
- Depends on: R4-01

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

- [ ] Counts and differences are explicitly reported.
- [ ] Every unexpected row is classified or left safely untouched.
- [ ] Authority state is verified.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-03`

Do not execute the next card in the same Agent run.
