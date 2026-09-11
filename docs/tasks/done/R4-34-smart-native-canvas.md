# CARD R4-34 — Run Historical Smart Canvas Natively in canvas.html

- Round: R4
- Priority: P0
- Status: DONE
- Activated: 2026-09-07T14:30+08:00
- Closed: 2026-09-07T14:40+08:00
- Depends on: R4-33

## Goal

Open historical Smart canvases directly in the unified page/runtime.

## Before Owner

Smart page/handoff

## After Owner

canvas.html + Unified Runtime

## In Scope

- Characterize old Smart entry routing.
- Load Smart records in canvas.html.
- Verify retained capabilities and persistence.

## Out of Scope

- Do not delete Smart files until verified.

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

- [x] Historical Smart opens without smart-canvas page switch.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

`canvas.js` `openCanvas` checked
`WorkbenchCanvasEntryCompatibility.requiresLegacySmartHandoff(canvas)` and,
when true, called `openSmartCanvasPage(canvas.id)` which redirected
`window.location.href` to `/static/smart-canvas.html?id=…`. The
`createCanvas` Smart branch did the same after POSTing a new Smart-kind
record. `canvas.html` did not load the Smart-compatibility shared seams
(`composer.js`, `media-tools.js`).

After:

`canvas.js` `openCanvas` and `createCanvas` (Smart branch) no longer
branch on kind. Every record — Classic or Smart — opens on `canvas.html`
via the shared `WorkbenchCanvasEntryCompatibility.normalCanvasUrl(id, project)`
helper (the list entry URL is unchanged). `openSmartCanvasPage` is dead
code and removed. `canvas.html` loads `composer.js` and `media-tools.js`
ahead of `canvas.js`, so the unified page has the Composer shell lifecycle
and media-edit geometry available for Smart node types. The Smart product
runtime files stay on disk (`R4-36` retires them) and the
`WorkbenchCanvasEntryCompatibility` handoff helpers stay exported
(`R4-35` retires the module).

Duplicate owner removed:

the Smart handoff redirect in `canvas.js` (owner is now the unified
`canvas.html` + the shared `normalCanvasUrl` entry helper, and the
Smart-compatibility shared seams `composer.js` / `media-tools.js` for
the retained canvas-runtime capabilities).

## Next Recommended Card

`R4-35`

Do not execute the next card in the same Agent run.
