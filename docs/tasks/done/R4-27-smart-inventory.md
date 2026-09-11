# CARD R4-27 — Smart Capability Inventory

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-07T10:47+08:00 (Owner authorization via in-conversation
  "提交并开发下一任务")
- Closed: 2026-09-07T11:05+08:00 (implementer evidence; independent review pending)
- Depends on: R4-26 (DONE 2026-09-07T10:53+08:00)

## Goal

Classify every Smart-only retained capability before deleting Smart runtime.

## Before Owner

smart-canvas.js owns product capabilities

## After Owner

explicit migrate/compat/remove/defer decisions

## In Scope

- Inventory Composer, prompt presets, asset UX, media edit/crop/draw/panorama, group actions, cascade/execution.
- Mark each KEEP/MIGRATE/COMPAT/REMOVE/DEFER-R8.

## Out of Scope

- No blind deletion.

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

- `tests/test_smart_capability_inventory.py` (6 tests) — parses the machine-
  readable evidence manifest in `docs/plans/R4_SMART_CAPABILITY_INVENTORY.md`
  and verifies: valid disposition + non-empty target owner per capability,
  every evidence function name is grounded in `static/js/smart-canvas.js`, all
  In-Scope areas covered, non-trivial classification, unique ids.

## Regression

Run:

```bash
./scripts/agent-verify.sh
```

Result: PASS at 392 Python unit tests (baseline 386; +6), Python AST parse,
JavaScript syntax, Architecture guards (4), `git diff --check`.

## Definition of Done

- [x] Every Smart-only capability has a disposition and target owner.

  31 capabilities, 7 categories — each marked KEEP/MIGRATE/COMPAT/REMOVE/
  DEFER-R8 with a target owner and source-line evidence, in
  `docs/plans/R4_SMART_CAPABILITY_INVENTORY.md`.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Smart-only capabilities had no explicit per-capability disposition;
only a six-row high-level review (Composer / group / upload / video / media
layout / MiniMax) in the ownership matrix.

After: `docs/plans/R4_SMART_CAPABILITY_INVENTORY.md` owns the authoritative
per-capability disposition + target owner; the ownership matrix `Smart-only`
review table references it.

Duplicate owner removed: none (characterization only — no code owner changed).

## Next Recommended Card

`R4-28`

Do not execute the next card in the same Agent run.
