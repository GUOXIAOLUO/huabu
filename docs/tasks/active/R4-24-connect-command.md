# CARD R4-24 — Generic Connect Command

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-07T08:55+08:00 (Owner authorization via in-conversation)
- Closed: 2026-09-07T09:02+08:00 (implementer evidence; independent review:
  PASS 2026-09-07T09:52+08:00)
- Depends on: R4-23 (DONE) — pre-blocker R4-21.1 canvasId rectification (DONE
  2026-09-07T08:55+08:00) closed earlier today

> Process note (independent review P1 finding, corrected 2026-09-07T09:52+08:00):
> the frontend connect-drop migration — `createVersionedConnection` /
> `connectInputNodeVersioned` routing through `WorkbenchNodeClient.connectNodes`
> — actually landed in commit `1364d17` (the "R4-22/23/21.1 close + R4-24
> seam" commit), i.e. before this card was formally activated in `dae17c2`.
> The `1364d17` message's claim that the "frontend migration … is left for the
> next iteration" is inaccurate; the code was already present. The subsequent
> `6198fee` "close" commit therefore only added the end-to-end behavioral test
> and bookkeeping. The product behavior is correct and fully verified (373-test
> gate PASS); this note records the true commit ordering so the narrative is
> not misleading. No history rewrite was performed.

## Goal

Create an application-level connect mutation boundary.

## Before Owner

page side effects + raw save

## After Owner

GraphMutationService/application command

## In Scope

- Define generic connect command.
- Validate revision/project/canvas.
- Keep UI interaction separate from mutation.

## Out of Scope

- Do not put Classic/Smart side effects into Core graph model.

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

- [x] Generic connect mutation is atomic and revision-safe.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md` (R4-24 close entry).
- `docs/plans/R4_OWNERSHIP_MATRIX.md` deferred-migration section already
  records "Resolved for the drop path (2026-09-07, card R4-24)" — the
  foundation commit set it; no further ownership move on this card. The
  remaining deferred `connectInputNode` callers (auto-connect on drag,
  output flows, loop migration) stay deferred per the matrix.
- Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

- Connect drops on both pages coupled the durable edge with page side
  effects on one raw save (`commitClassicConnection` Classic /
  `connectInputNode` Smart). The atomicity guarantee lived at the page
  save, not at the application boundary.

After:

- `GraphMutationService.connect_nodes` (backend service in
  `workbench/application/graph_mutation.py`) owns the atomic,
  revision-safe edge mutation and — for Smart — the target
  `inputNodeIds` sync in the same lock. The HTTP route
  `POST /api/v1/canvases/{canvas_id}/graph/connect-nodes` maps the
  command to the service through `ConnectNodesPayload`, returns the
  projected edge plus the new revision, and translates `GraphMutationError`
  to HTTP 403/422 and `StaleCanvasRevisionError` to HTTP 409.
- `WorkbenchNodeClient.connectNodes(canvasId, command, actorId)` in
  `static/js/workbench/canvas/node-creation-client.js` is the single
  versioned client entry point; it gates on `requirePositiveRevision`
  before the request.
- `createVersionedConnection` (Classic) and `connectInputNodeVersioned`
  (Smart) are the page-side entry helpers; each routes the connect
  drop through `WorkbenchNodeClient.connectNodes(canvas.id, ...)`.

Duplicate owner removed: N/A — the page-side legacy connect helpers
(`commitClassicConnection`, `connectInputNode`) stay as bounded
fallback for the case where the versioned service rejects (e.g., stale
revision, `versioned_nodes=0`). They are no longer the default owner
for the connect drop; the application command is. The pre-card
binding "page side effects + raw save" no longer holds for the normal
connect drop path.

Tests prove: atomic edge mutation, revision CAS, 409 stale, 422
duplicate / invalid endpoint, 403 forbidden, Smart target
`inputNodeIds` + audit emission in the same lock, both pages'
helpers land at the connect command with the right canvas id /
project / expected revision / edge id / kind, and the helper
correctly returns `true` / `false` / `null` based on outcome.

## Next Recommended Card

`R4-25`

Do not execute the next card in the same Agent run.
