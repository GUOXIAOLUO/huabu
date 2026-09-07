# CARD R4-31 — Classic Capability Inventory

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-07T12:05+08:00 (Owner authorization via in-conversation
  "提交并开发下一任务")
- Closed: 2026-09-07T12:40+08:00
- Depends on: R4-30 (DONE 2026-09-07T12:30+08:00)

## Goal

Classify Classic-only retained capabilities before deleting Classic runtime.

## Before Owner

canvas.js owns product capabilities

## After Owner

explicit disposition map

## In Scope

- Inventory provider cards, Comfy, RunningHub, MiniMax, LTX, video, output/log/asset/cascade/execution.
- Assign target owner/disposition.

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

- `tests/test_classic_capability_inventory.py` (6 tests) parses the document's
  embedded JSON evidence manifest and verifies: the manifest points at
  `static/js/canvas.js`; every capability has a valid disposition + non-empty
  target owner; every evidence function name is actually present in
  `canvas.js`; all In-Scope areas (provider cards, Comfy, RunningHub, MiniMax,
  LTX, video, output/log, asset, cascade/execution) are covered; the
  classification is non-trivial (MIGRATE + COMPAT + DEFER-R8 all used); and
  capability ids are unique.

## Regression

Run:

```bash
./scripts/agent-verify.sh
```

Result: PASS at 405 Python unit tests (baseline 399; +6), PASS Python AST
parse, PASS JavaScript syntax, PASS Architecture guards (4), PASS
`git diff --check`. `AGENT VERIFY: PASS`.

## Definition of Done

- [x] Every Classic-only capability has target disposition.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

`canvas.js` owned Classic-only product capabilities with no explicit
disposition map.

After:

`docs/plans/R4_CLASSIC_CAPABILITY_INVENTORY.md` maps every Classic-only,
product-relevant capability (13 capabilities across 9 categories) to a
disposition and target owner, anchored by
`tests/test_classic_capability_inventory.py`.

Duplicate owner removed:

n/a — characterization-only card; no code migrated or deleted (no blind
deletion).

## Next Recommended Card

`R4-32`

Do not execute the next card in the same Agent run.
