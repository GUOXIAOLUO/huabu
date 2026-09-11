# CARD R6-07 — Collection Gallery View

- Round: R6
- Priority: P1
- Status: ACTIVE — implementation complete; independent Review pending
- Depends on: R6-06

## Goal

Add gallery presentation for visual collections.

## Before Owner

no collection UX

## After Owner

Collection Rich Node gallery view

## In Scope

- Render referenced media/items efficiently.
- Support selection/open item.
- Integrate with Rich Node card/expanded/workspace.

## Out of Scope

- No image editing.

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

- `tests/test_collection_rich_node.py` — 2 focused tests PASS.
- Full `./scripts/agent-verify.sh` PASS: 717 tests, 117 Python AST files,
  122 JavaScript files, 4 architecture guards, clean diff check.

## Definition of Done

- [x] Gallery works for mixed valid visual references and reloads.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.

## Final Ownership Evidence

Before: Collections had a domain/persistence model but no Collection Rich Node
gallery or renderer registration.

After: `WorkbenchCollectionRichNode` owns the gallery projection, item
selection/open intents, and shared presentation-state integration. The
unified NodeShell/RendererRegistry mounts it for Collection records; the
Canvas adapter only projects the retained Collection payload.

Duplicate owner removed: none identified; media resolution is injected and no
image-editing or Collection persistence logic was added to the gallery.

## Next Recommended Card

`R6-08`

Do not execute the next card in the same Agent run.
