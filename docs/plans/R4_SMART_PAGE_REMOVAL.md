# R4 Smart Page Removal

Owner: card R4-36. Deletes the Smart product page (`static/smart-canvas.html`
+ `static/js/smart-canvas.js` + the Smart i18n bundle) and all its active
references now that R4-34 made `canvas.html` the single entry and R4-35
retired the handoff surface. The DoD "One visible Canvas page remains" is
satisfied when `canvas.html` is the only Canvas page in the product and the
regression gate is green.

## Audit results

A full-repo audit (after R4-35) finds the following active surfaces
referencing the Smart page; this card resolves each one.

### Files to delete (the Smart page + its companion assets)

- `static/smart-canvas.html` — the Smart product page.
- `static/js/smart-canvas.js` — the Smart page editor.
- `static/js/i18n/smart-canvas.js` — the Smart page i18n bundle
  (loaded by `static/js/i18n.js`).

### Active code to update

- `static/js/i18n.js` — drops `'/static/js/i18n/smart-canvas.js'` from its
  page-bundle list.
- `static/js/i18n/validate-i18n.js` — drops `static/js/i18n/smart-canvas.js`
  from the validation page list.
- `static/js/canvas-list.js` (L90) — the "Viewport math (mirrors
  smart-canvas.js)" header comment becomes a historical footnote
  (the math now lives only in canvas-list.js).
- `static/js/workbench/canvas/composer.js` (L7) and
  `static/js/workbench/canvas/media-tools.js` (L6, L15) — the comments
  that say "smart-canvas.js keeps rendering / the editor modal" become
  historical: these modules are now owned by `canvas.html` (R4-34) and
  the page comment is updated to reflect that the subject binding is
  resolved by the unified page, not a separate Smart page.

### Tests to update

- `tests/test_frontend_workbench_modules.py` — 18 dual-iteration sites
  (`for page, editor in (("canvas.html", "canvas.js"),
  ("smart-canvas.html", "smart-canvas.js")):` and the `adapter` variant)
  become single-iteration `(("canvas.html", "canvas.js"),)`. Standalone
  Smart-only test methods (those that read `smart-canvas.js` / `smart`
  directly and assert Smart-page-specific behavior) are removed because
  the Smart page is gone and the behavior under test no longer exists.
- `tests/test_canvas_entry.py` — the R4-35 routing test
  `test_no_smart_product_page_routing_remains_in_static_js` drops
  `smart-canvas.js` from the scanned list (the file is gone, so it
  cannot be a routable URL holder).
- `tests/test_canvas_runtime_state.py` — drops the Smart-page reads
  (the Smart page no longer exists to share runtime state with).
- `tests/test_repository_independence.py` — drops Smart-page
  references in the scanned source list.
- `tests/test_smart_capability_inventory.py` — DELETED. The R4-27
  inventory test pins evidence function names to `smart-canvas.js`,
  which is now gone; the inventory doc
  (`docs/plans/R4_SMART_CAPABILITY_INVENTORY.md`) is preserved as a
  historical snapshot with a header note that the source file is
  deleted and the manifest is a frozen R4-27 artifact.

### Active docs to update

- `docs/status/CURRENT_EXECUTION_STATUS.md` — R4-36 evidence section
  added; R4-27/28/29/30/32/33/34/35 sections left as historical
  records (they describe the work done at that time).
- `docs/plans/R4_OWNERSHIP_MATRIX.md` — `Smart handoff` row remains
  retired (R4-35); the `Smart product runtime` row is removed (no
  product page remains); a new "Canvas page surface" row records that
  `canvas.html` is the single visible page.
- `docs/plans/R4_SMART_HANDOFF_REMOVAL.md` — the "stays on disk" line
  for `smart-canvas.html` / `smart-canvas.js` is updated to "R4-36
  retired the page and the editor." (The R4-35 doc was accurate at
  R4-35 close; this keeps it accurate at R4-36 close.)
- `docs/plans/R4_SMART_NATIVE_ENTRY.md` — a brief "R4-36 retired the
  Smart page; canvas.html is now the sole Canvas page" annotation
  appended (the R4-34 doc is left as the R4-34 historical record).
- `docs/tasks/TASK_INDEX.md` — updates the Smart page task chain
  status to closed.

### Historical references NOT changed

The following references are historical records of completed work and
are left untouched (rewriting them would falsify the R4 narrative):

- `docs/tasks/active/R4-21.1`, `R4-25`, `R4-27`, `R4-28`, `R4-29`,
  `R4-30`, `R4-34`, `R4-35` — DONE cards whose evidence sections
  describe the work done against `smart-canvas.js` at that time.
- `docs/tasks/done/*` — completed R3/R4 cards.
- `docs/proposals/R4_UNIFIED_CANVAS_CUTOVER.md`,
  `docs/proposals/unified-canvas-runtime.md` — forward-looking
  proposals that the R4 round is now executing.
- `docs/benchmarks/canvas-payload-baseline-2026-09-02.md` — a frozen
  baseline snapshot.
- `MIGRATION_PLAN.md`, `IMPLEMENTATION_PLAN.md`, `CURRENT_ARCHITECTURE.md`
  — historical / current-state plans.
- `AGENTS.md` — the R4 hard-constraint source of truth; its mention of
  `smart-canvas.js` is in the constraint narrative (e.g. "Smart/Carrier
  are migration sources, not permanent modes") and is left intact.
- `docs/tasks/backlog/R4-37-remove-smart-runtime.md` — the next card,
  which legitimately describes what is in `smart-canvas.js` today
  (and will describe what R4-36 leaves behind once R4-36 closes).

## Inventory

| Surface | Disposition | Before evidence |
|---|---|---|
| `static/smart-canvas.html` | **deleted** (this card) | the Smart product page; the sole holder of the Smart page UI |
| `static/js/smart-canvas.js` | **deleted** (this card) | the Smart page editor; the sole holder of the Smart product runtime |
| `static/js/i18n/smart-canvas.js` | **deleted** (this card) | the Smart page i18n bundle |
| `static/js/i18n.js` smart-canvas entry | **removed** (this card) | line 9 |
| `static/js/i18n/validate-i18n.js` smart-canvas entry | **removed** (this card) | line 12 |
| `static/js/canvas-list.js` smart-canvas comment | **updated** (this card) | line 90 |
| `static/js/workbench/canvas/composer.js` smart-canvas comment | **updated** (this card) | line 7 |
| `static/js/workbench/canvas/media-tools.js` smart-canvas comments | **updated** (this card) | lines 6, 15 |
| `tests/test_frontend_workbench_modules.py` 18 dual-iterations | **refactored** (this card) | 18 single-line replacements to single-iteration; Smart-only test methods removed |
| `tests/test_canvas_entry.py` routing test smart-canvas scan | **updated** (this card) | drop `smart-canvas.js` from the scanned list |
| `tests/test_canvas_runtime_state.py` smart reads | **updated** (this card) | drop Smart reads |
| `tests/test_repository_independence.py` smart refs | **updated** (this card) | drop Smart refs |
| `tests/test_smart_capability_inventory.py` | **deleted** (this card) | R4-27 evidence test; the manifest is now a frozen historical snapshot |
| `docs/plans/R4_SMART_CAPABILITY_INVENTORY.md` | **annotated** (this card) | header note: source file deleted; manifest is a frozen R4-27 artifact |
| `docs/plans/R4_SMART_HANDOFF_REMOVAL.md` | **updated** (this card) | "stays on disk" → "R4-36 retired" |
| `docs/plans/R4_SMART_NATIVE_ENTRY.md` | **annotated** (this card) | brief R4-36 retirement note appended |
| `docs/plans/R4_OWNERSHIP_MATRIX.md` | **updated** (this card) | Smart product runtime row removed; Canvas page surface row records single page |
| `docs/status/CURRENT_EXECUTION_STATUS.md` | **appended** (this card) | R4-36 evidence section |
| `docs/tasks/TASK_INDEX.md` | **updated** (this card) | Smart page task chain marked closed |
| `static/js/workbench/canvas/canvas-entry-compatibility.js` | unchanged | only a comment mentions `smart-canvas.html` (no leading slash, documentation only) |
