# CARD R4-39 — Remove Legacy canvas.js Product Runtime

- Round: R4
- Priority: P0
- Status: DONE
- Activated: 2026-09-08
- Completed: 2026-09-09
- Depends on: R4-38

## Goal

Replace the old Classic monolith with a small neutral bootstrap.

The card begins with a dependency-grounded residual-runtime inventory. Deletion
is not authorized merely because R4-38 moved named bodies into Classic seams:
the seams still require page-owned state and host operations from `canvas.js`.
Each removal wave must first establish a real replacement owner and browser
parity, then delete the corresponding Classic ownership.

## Before Owner

canvas.js monolith

## After Owner

small canvas-app bootstrap

## In Scope

- Move remaining legitimate bootstrap wiring.
- Delete monolithic business/runtime code.
- Verify legacy records.

## Out of Scope

- No new bootstrap monolith.

## Execution Pattern

```text
characterize
→ focused test
→ establish seam
→ implement/migrate
→ verify
→ remove duplicate ownership
```

## Definition of Done

- [x] No Classic product runtime remains.

## Final Ownership Evidence

Before: `static/js/canvas.js` was an 11,334-line page-global product runtime
and the single loaded owner of Canvas state, adapters, interaction,
media/workflow UI, execution composition, and startup wiring.

After: `canvas.html` natively loads nine ordered responsibility scripts,
ending in the 49-line `canvas-app-bootstrap.js`. It does not fetch,
concatenate, or evaluate source at runtime. Shared Canvas/session/render/
interaction/mutation/media modules remain the behavior owners established by
Waves 2–5.

Duplicate owner removed: `static/js/canvas.js` and its script reference are
deleted. The executable gate requires native ordered loading, explicit
inline-action exports, the absence of `canvas.js`, and all eight residual
ownership clusters to be `MIGRATED`.

Final verification (2026-09-09): PASS — default and all-six-zero URLs rendered
the same persisted two-node Canvas; workflow modal open/close passed. Full
`./scripts/agent-verify.sh`: PASS (630 tests, 80 Python AST files, 111
JavaScript files, 4 architecture guards, clean diff check). Independent Review:
PASS.

## Next Recommended Card

`R4-40`

Do not execute the next card in the same Agent run.
