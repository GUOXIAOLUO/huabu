# CARD R4-04 — Split-Brain Regression Suite

- Round: R4
- Priority: P0
- Status: DONE
- Activated: 2026-09-06T18:05+08:00
- Completed: 2026-09-06T18:10+08:00
- Depends on: R4-03

## Goal

Turn the known split-brain incident into permanent regression coverage.

## Before Owner

Implicit safety assumptions

## After Owner

Executable regression protection

## In Scope

- Test sqlite authority normal routing.
- Test sqlite authority with old routing flag disabled.
- Test supported legacy migration/read state.
- Test restart/authority persistence and write isolation.

## Out of Scope

- No unrelated repository refactor.

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

- [x] All split-brain tests prove behavior, not only constants. (`tests/test_split_brain_regression.py`: 5 scenario tests exercise `main.canvas_repository()`/`new_canvas`/migration service end to end on isolated fixtures — routing identity, refused routing raising `CanvasAuthoritySplitBrainError`, real legacy read/write plus a completed backfill import, a reopened repository deciding routing after restart, and writes landing in exactly one store.)
- [x] agent-verify passes or existing failures are documented. (AGENT VERIFY: PASS — 313 unit tests, 71 Python AST files, 63 JS files, 4 architecture guards, `git diff --check`.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Implicit safety assumptions — the split-brain behaviors lived only in
scattered wiring assertions and in the documented incident narrative.

After: Executable regression protection — one named suite
(`tests/test_split_brain_regression.py`) permanently pins the four incident
scenarios: normal SQLite routing, refused disabled-flag routing, supported
legacy state while authority is inactive, restart-durable authority, and
one-store write isolation.

Duplicate owner removed: none — verification-only card; no ownership changed, so
`R4_OWNERSHIP_MATRIX.md` was not modified.

## Next Recommended Card

`R4-05`

Do not execute the next card in the same Agent run.
