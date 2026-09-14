# CARD R10-04 — Entity Rich Node

- Round: R10
- Priority: P1
- Status: DONE — independent Review PASS; archived 2026-09-14
- Depends on: R10-03

## Goal

Render/edit generic entity data through Rich Node/Inspector.

## Before Owner

no entity UX

## After Owner

Entity Rich Node

## In Scope

- Definition-driven fields.
- Version-aware edit flow.
- Show relations.

## Out of Scope

- No industry-specific fields in Core.

## Compatibility / Migration

- Preserve existing behavior and data unless the card explicitly authorizes a migration.

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

- [x] Package entity definitions can drive UI later.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: no Entity renderer or Inspector presentation in the shared Canvas runtime.

After: `WorkbenchEntityRichNode` plus the `entity-rich@1` RendererRegistry entry
render generic definition-driven fields, current version identity, relations,
and emit version-aware edit intents.

Duplicate owner removed: none introduced; entity persistence remains owned by
`SqliteEntityRepository`/`EntityService`, and UI emits intents only.

## Implementation Evidence

- Added `static/js/workbench/canvas/entity-rich-node.js` with generic field
  projection, relation display, inspector editing, and `baseVersionId` intent
  provenance. It contains no package or industry-specific fields and no API
  persistence call.
- Registered the renderer through `NodeCardHost` and shared `NodeShell`; loaded
  it from `static/canvas.html` and styled it in `static/css/canvas.css`.
- Focused suite: `tests.test_entity_rich_node`, `tests.test_nodeshell_v2`, and
  `tests.test_renderer_registry` — 6 tests passed.
- Full gate: `./scripts/agent-verify.sh` — PASS, 1329 tests, 288 Python AST
  files, 154 JavaScript files, 4 architecture guards, and clean diff check.
- Browser acceptance attempt: the documented live route is
  `/static/canvas.html`; the in-app browser rejected the localhost navigation
  with `ERR_BLOCKED_BY_CLIENT`. Direct HTTP verification returned 200 and
  confirmed the new script is present. No browser screenshot assertion was
  possible in this environment.
- Independent Review repair: `NodeCardHost` now forwards entity edits through
  the shared `onIntent` boundary as `entity_edit`, while preserving an optional
  `onEdit` observer. The focused suite and full gate were rerun after this fix.

## Next Recommended Card

`R10-05`

Do not execute the next card in the same Agent run.
