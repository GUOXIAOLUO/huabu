# CARD R5-11 — Asset Rich Node

- Round: R5
- Priority: P1
- Status: DONE
- Previous implementation: COMPLETE — re-executed and repaired 2026-09-10
- Independent Review: PASS — 2026-09-10
- Depends on: R5-10

## Goal

Prove Rich Node presentation using a generic existing asset/media record.

## Before Owner

basic media card

## After Owner

Rich Asset presentation

## In Scope

- Implement card/expanded/workspace/inspector behavior using existing asset-compatible data.
- Keep R9 AssetVersion architecture out.
- Test load/reload and legacy payload compatibility.

## Out of Scope

- No Resource Library yet.

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

- [x] Asset node exercises all four presentation levels without future-system leakage.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: media cards rendered existing payloads, but there was no generic rich-asset presentation contract spanning all four presentation levels.

After: `WorkbenchAssetRichNode` adapts existing asset-compatible and legacy media payloads, deduplicates media items, and drives card/expanded/workspace/inspector transitions through the shared presentation state model. NodeShell reuses its single presentation controller when creating the adapter, so the Unified Canvas has no duplicate presentation owner.

Duplicate owner removed: presentation transitions remain centralized in `WorkbenchPresentationState`; the rich-asset adapter owns only asset-compatible projection and does not introduce AssetVersion, Resource Library, or new persistence ownership.

Verification: focused AssetRichNode and NodeShell tests pass (4 tests), covering legacy
payload compatibility, deduplication, all four presentation levels, reload,
immutable media snapshots, shared presentation ownership, and the production
render-path contract. `./scripts/agent-verify.sh` passes (693 tests, 104 Python AST files, 121
JavaScript files, 4 architecture guards, clean diff check). Developer Git
Review PASS; independent Review PENDING.

## Next Recommended Card

`R5-12`

Do not execute the next card in the same Agent run.
