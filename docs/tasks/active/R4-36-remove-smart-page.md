# CARD R4-36 — Delete smart-canvas.html

- Round: R4
- Priority: P0
- Status: DONE
- Activated: 2026-09-07T14:57+08:00
- Closed: 2026-09-07T15:09+08:00
- Depends on: R4-35

## Goal

Remove duplicate Smart product page after all retained behaviors are hosted elsewhere.

## Before Owner

smart-canvas.html

## After Owner

canvas.html only

## In Scope

- Verify no valid entry references Smart page.
- Delete page.
- Update tests/docs/routes.

## Out of Scope

- Do not hide broken routes with silent redirects unless explicitly intended.

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

- [x] One visible Canvas page remains.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

Two Canvas pages existed: `static/smart-canvas.html` (the Smart product
page) and `static/canvas.html` (the Classic page). 79 test methods in
`tests/test_frontend_workbench_modules.py` treated the two pages as
parallel adapters (dual-iterations + Smart-specific behavior contracts),
and a full-repo audit found 6 active files referencing `smart-canvas.html`
or `smart-canvas.js`.

After:

`static/smart-canvas.html`, `static/js/smart-canvas.js`,
`static/css/smart-canvas.css`, `static/js/i18n/smart-canvas.js` and
`tests/test_smart_capability_inventory.py` are deleted. `canvas.html`
is the sole Canvas page. 63 Smart-page-specific test methods are
removed; the 18 dual-iteration sites in the remaining test file iterate
over `canvas.html` only. i18n bundles, the canvas-list viewport comment,
and the composer / media-tools module comments are updated to record
the retirement. The R4-27 capability inventory doc is preserved as a
frozen historical snapshot.

Duplicate owner removed:

the Smart product page and its editor (owner is now `canvas.html`
alone; the Smart-only test methods and the Smart i18n bundle are
retired with the page).

## Next Recommended Card

`R4-37`

Do not execute the next card in the same Agent run.
