# CARD R6-07 — Collection Gallery View

- Round: R6
- Priority: P1
- Status: DONE — independent Review PASS 2026-09-11
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

- `tests/test_collection_rich_node.py` — 5 focused tests PASS.
- Full `./scripts/agent-verify.sh` PASS: 721 tests, 117 Python AST files,
  123 JavaScript files, 4 architecture guards, clean diff check.

## Definition of Done

- [x] Gallery works for mixed valid visual references and reloads.

## Documentation

- Updated `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Updated `AGENT_NEXT_TASK.md` after independent Review PASS.

## Final Ownership Evidence

Before: Collections had a domain/persistence model but no Collection Rich Node
gallery or renderer registration.

After: `WorkbenchCollectionRichNode` owns the gallery projection, item
selection/open intents, and shared presentation-state integration. The
unified NodeShell/RendererRegistry mounts it for Collection records; the
Canvas adapter only projects resolver/snapshot/Canvas-owned media into the
gallery and never creates AssetVersion/ArtifactVersion ownership.

Duplicate owner removed: NodeCardHost is the sole gallery descriptor owner;
media resolution is injected or projected from retained snapshots/Canvas
outputs, and no image-editing or Collection persistence logic was added.

Independent Review: PASS. The production path, mixed image/video rendering,
presentation reuse, selection/open callbacks, resolver boundaries, and
ownership constraints were verified. R6 does not create AssetVersion or
ArtifactVersion persistence or a second resource resolver.

## Next Recommended Card

`R6-08`

Do not execute the next card in the same Agent run.
