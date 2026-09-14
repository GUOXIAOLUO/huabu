# CARD R9-04 — Resource Library Shell

- Round: R9
- Priority: P0
- Status: DONE — independent Review PASS
- Depends on: R9-03 (DONE, independent Review PASS)

## Goal

Create unified Resources UI shell without adding top-level navigation.

## Before Owner

scattered asset/prompt/skill UX

## After Owner

Resource Library

## In Scope

- Create category/search/filter layout.
- Integrate Asset/Collection/Prompt/Skill entry points.
- Keep extensible resource registry.

## Out of Scope

- No new top-level nav categories.

## Compatibility / Migration

- Preserve existing behavior and data unless the card explicitly authorizes a migration.
- The retained per-category item search inputs and every existing tab body stay
  page-owned; this card adds the Resources chrome, it does not rewrite the
  per-category managers.

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

- Add/run the smallest behavioral tests that prove this card's goal.
- Run `./scripts/agent-verify.sh`.

## Definition of Done

- [x] Resources are reachable under one top-level section.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: the section's category list was static markup inside
`static/asset-manager.html` (five hand-written `data-tab` buttons bound at
script load), with no registry, no unified search and no filter row; Collection
and Skill had no entry point from the Resources section at all.

After: `WorkbenchResourceLibraryShell` (`static/js/workbench/canvas/resource-library-shell.js`)
owns the Resources category rail, the unified search control and the
resource-kind filter row, driven by `createRegistry()` /
`createShell()`. The page seeds the registry with seven categories covering the
four canonical resource kinds this card names (`asset`, `prompt`, `collection`,
`skill`) plus the retained `workflow` / canvas-asset / local categories.
Library-surface categories keep the page's single `data-tab` switch path;
canvas-surface categories (Collection, Skill) route to the Unified Canvas
through the studio shell's `studio-switch-page` message instead of growing a
second resource library inside the page.

Duplicate owner removed: the static `[data-tab]` markup and the load-time
`document.querySelectorAll('[data-tab]')` binding are gone — the shell is the
single owner of the category rail and of the rail's active state (the page's
`render()` no longer toggles a static tab set). The per-category item search
inputs remain page-owned compatibility and are deliberately not retired here.

## Developer Verification

- Focused `tests/test_resource_library_shell.py`: **6 tests PASS** — the
  registry is extensible/ordered and rejects duplicate ids, unknown surfaces,
  unknown kinds and missing labels; the shell renders the rail + unified search
  + kind filter from the page's real `RESOURCE_CATEGORY_DEFINITIONS`; the kind
  filter projects the rail and keeps the active category pinned; the page mounts
  the shell as the single Resources chrome; resources stay under one top-level
  section and canvas entries route out; both scripts pass `node --check`.
- `./scripts/agent-verify.sh`: **PASS — 1197 tests**, 243 Python AST files,
  147 JavaScript files, 4 architecture guards, clean `git diff --check`.
- Browser acceptance (headless Chrome + CDP, real local server): the studio
  shell shows exactly one `素材库` top-level entry; inside it the rail renders
  all 7 categories with `assets` active, `collections`/`skills` as canvas
  entries, the unified search and the 5 resource-kind chips; typing in the
  unified search keeps focus and mirrors into the active category's own
  `assetSearch` input; the `提示词` chip narrows the rail to
  `assets` (active, pinned) + `prompts` without leaving the section; clicking
  `集合` routes the studio to the Unified Canvas frame (`studio_active_page` →
  `canvas`).
- Independent Review returned PASS; this card is archived.

## Truth Reconciliation (this run)

`tests/test_current_fact_documentation.py` still pinned `R9-03` as the Active
Task in `AGENT_NEXT_TASK.md` / `TASK_INDEX.md`, so the pre-change baseline gate
was red (1191 tests, 1 failure). The repository's real current fact is that
R9-03 is DONE + independent Review PASS + archived and R9-04 is the sole ACTIVE
card; the test was stale from the R9-03 close. The contract now pins R9-04, and
the stale `verified_commit` / `verification_source` header narrative in
`docs/status/CURRENT_EXECUTION_STATUS.md` was corrected in the same pass.

## Next Recommended Card

`R9-05`

Do not execute the next card in the same Agent run.
