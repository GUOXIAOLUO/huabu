# CARD R4-06 — Browser Persistence Uses Logical Revision

- Round: R4
- Priority: P0
- Status: DONE
- Activated: 2026-09-06T18:27+08:00
- Completed: 2026-09-06T18:40+08:00
- Depends on: R4-05

## Goal

Move normal browser save concurrency from updated_at/base_updated_at to logical revision.

## Before Owner

timestamp compatibility cursor

## After Owner

logical Canvas revision

## In Scope

- Update canonical persistence client.
- Adopt server revision after save/load.
- Keep updated_at as display/compat metadata only.
- Update focused tests.

## Out of Scope

- Do not refactor rendering/interaction.

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

- [x] Normal save sends expected_revision. (The persistence client composes the canonical `PUT /api/v1/canvases/{id}` with `expected_revision` from its owned revision cursor; sandbox test proves the wire body `{payload: {...minus transport fields}, expected_revision: N}`.)
- [x] Client adopts returned revision. (The cursor follows load → save → 409 `current_revision` → recovery responses, and `adoptRevision` feeds it after versioned writes; sandbox test proves the chain 5 → 6 → 9 → 10 across a conflict.)
- [x] No normal CAS depends on timestamp. (Canonical CAS is revision-only; `payload.updated_at` is stamped server-side as display/compat metadata and `base_updated_at` survives only inside the explicit legacy 503/revision-less fallback.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Timestamp compatibility cursor — normal browser saves raced on
`base_updated_at`/`updated_at` through the legacy PUT, with the logical
revision only mirrored into the same slot by `adoptRevision`.

After: Logical Canvas revision — the shared persistence client owns the
revision cursor and the canonical-first CAS transport; `updated_at` is display/
compat metadata only (stamped server-side); the legacy transport remains the
explicit 503/revision-less fallback and `metadata()` awaits R4-07.

Duplicate owner removed: the timestamp cursor no longer owns normal save
concurrency — it was demoted to display/compat metadata inside the client seam;
ownership-matrix revision/CAS row updated accordingly.

## Next Recommended Card

`R4-07`

Do not execute the next card in the same Agent run.
