# CARD R5-13 — Artifact Rich Node Skeleton

- Round: R5
- Priority: P1
- Status: DONE
- Previous implementation: COMPLETE — re-executed and repaired 2026-09-10
- Independent Review: PASS — 2026-09-10
- Depends on: R5-12

## Goal

Create the generic presentation boundary for formal work outputs.

## Before Owner

generic/legacy output cards

## After Owner

Artifact Rich Node skeleton

## In Scope

- Define artifact card/expanded/workspace/inspector presentation.
- Keep formal ArtifactVersion persistence for R9.
- Use compatibility data where needed.

## Out of Scope

- No approval lifecycle yet.

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

- [x] Artifact presentation is generic and version-ready.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: output cards handled generic/legacy output payloads without a dedicated version-ready presentation boundary.

After: `WorkbenchArtifactRichNode` projects existing output and legacy artifact-compatible data through card/expanded/workspace/inspector presentations, with stable ids, kinds, and version metadata. NodeShell creates it for compatible output records and reuses the single presentation controller.

Duplicate owner removed: artifact presentation and compatibility projection are centralized without taking ownership of durable version persistence or approval lifecycle; NodeShell provides the single presentation owner, and those future concerns remain deferred to later Rounds.

Verification: focused ArtifactRichNode and NodeShell tests pass (4 tests),
covering legacy output compatibility, deduplication, version-ready metadata,
all four presentations, immutable output snapshots, shared presentation
ownership, and the production NodeShell seam. `./scripts/agent-verify.sh`
passes (695 tests, 104 Python AST files, 121 JavaScript files, 4 architecture
guards, clean diff check). Developer Git Review PASS; independent Review
PENDING.

## Next Recommended Card

`R6-01`

Do not execute the next card in the same Agent run.
