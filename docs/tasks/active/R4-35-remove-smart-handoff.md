# CARD R4-35 — Remove Smart Handoff

- Round: R4
- Priority: P0
- Status: DONE
- Activated: 2026-09-07T14:49+08:00
- Closed: 2026-09-07T14:54+08:00
- Depends on: R4-34

## Goal

Delete page-switch/handoff behavior now that Smart records run natively.

## Before Owner

Smart handoff compatibility

## After Owner

Unified entry

## In Scope

- Remove handoff routing.
- Add regression for historical Smart entry.

## Out of Scope

- Do not delete required compatibility modules.

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

- [x] No Smart product page routing remains.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

`WorkbenchCanvasEntryCompatibility` exported the four non-handoff helpers
plus `requiresLegacySmartHandoff` and `legacySmartCanvasUrl`; the
`/static/smart-canvas.html` URL string lived in `legacySmartCanvasUrl`.

After:

`WorkbenchCanvasEntryCompatibility` exports only the four non-handoff
helpers (`normalCanvasUrl`, `rememberCanvasListProject`,
`rememberedCanvasListProject`, `canvasListUrl`). A static-JS audit finds
zero hits for `/static/smart-canvas.html` anywhere under `static/js/`.
The `smart-canvas.html` / `smart-canvas.js` product page stays on disk
(`R4-36` retires it after capability verification).

Duplicate owner removed:

the Smart product-page handoff routing (the page-switch capability that
this card retires; the unified `canvas.html` + the shared
`normalCanvasUrl` entry helper is now the sole entry path).

## Next Recommended Card

`R4-36`

Do not execute the next card in the same Agent run.
