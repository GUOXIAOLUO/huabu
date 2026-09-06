# CARD R4-07 — Remote Sync Uses Revision

- Round: R4
- Priority: P0
- Status: DONE
- Activated: 2026-09-06T18:45+08:00
- Completed: 2026-09-06T19:00+08:00
- Depends on: R4-06

## Goal

Make remote/window synchronization compare canonical revisions instead of timestamps.

## Before Owner

updatedAt comparison

## After Owner

logical revision comparison

## In Scope

- Characterize current remote sync.
- Replace normal timestamp ordering with revision ordering.
- Test stale second-window save and refresh/adopt flow.

## Out of Scope

- No UI redesign.

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

- [x] Two-window stale conflict is deterministic. (Sandbox tests: same/older revision never re-applies even with a newer timestamp; revision-less probes keep timestamp ordering; own-client notifications filtered. HTTP round-trip + meta probe pins the stale second-window save → 409 with current_revision/canvas → adopt → save flow.)
- [x] Remote apply cannot regress to an older revision. (`WorkbenchCanvasRemoteSync.check()` and `WorkbenchCanvasUpdateMessage.newerForCanvas()` order by revision first; an older revision with a huge timestamp is ignored — pinned by test. Classic's polling flow peeks meta → compares → loads → applies, and both adapters feed `currentRevision` baselines.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: updatedAt comparison — remote sync polled the legacy `/meta` timestamp
and WebSocket notifications ordered by `updated_at`, so cross-window freshness
was a timestamp heuristic over the legacy transport.

After: Logical revision comparison — the canonical transport carries the
version truth (`/api/v1/canvases/{id}/meta` probe; revision in the
`canvas_updated` broadcast), the shared remote-sync coordinator and
update-message filter order by revision with a bounded timestamp fallback, and
both adapters supply `revisionOf()` baselines; the ownership-matrix
remote/version-polling row now names revision ordering on the default path.

Duplicate owner removed: the timestamp comparison no longer owns normal remote
version ordering — it survives only as the bounded fallback for revision-less
legacy probes; the matrix row was updated accordingly.

## Next Recommended Card

`R4-08`

Do not execute the next card in the same Agent run.
