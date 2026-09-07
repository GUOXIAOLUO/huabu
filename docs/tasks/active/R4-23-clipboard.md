# CARD R4-23 — Clipboard Unified Creation

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-07 (after R4-22 close)
- Closed: 2026-09-07T07:35+08:00 (implementer evidence; independent review: PASS
  2026-09-07T09:52+08:00 — the card file's earlier `Status: BACKLOG` / `backlog/`
  location were bookkeeping drift, corrected on the review's P1 finding)
- Depends on: R4-22

## Goal

Unify copy/paste/duplicate and external paste creation paths.

## Before Owner

page-specific clipboard mutation

## After Owner

CreationController / command runtime

## In Scope

- Migrate node copy/paste.
- Migrate multi-copy.
- Characterize external image/text paste.
- Remove raw create/save duplication.

## Out of Scope

- No new clipboard product scope.

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

- [x] Clipboard regression passes across legacy record types.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

Classic `pasteNodes` and Smart `pasteNodes` materialized the clipboard fragment
through the shared graph-fragment module, then appended nodes/connections
directly and issued a raw Canvas save; both pages owned near-duplicate paste
implementations. Smart additionally owned an inline duplicate of the fragment
commit inside the same function.

After:

Single-node, connection-free clipboard paste of the losslessly persistable
Legacy shapes — Classic `image` (url/name/mediaKind) and `prompt` (text),
Smart `smart-prompt` (full durable config) — creates through
`CreationController.createNode` and `NodeCreationService` with the explicit
`clipboard` provenance source (`NodeCreationSource.CLIPBOARD`), revision CAS
adoption, undo-snapshot projection and selection projection; no raw node
append or Canvas save on that path. Placement still comes from the shared
center-anchored materialization, so position behavior is unchanged.

Duplicate owner removed:

The Smart page's inline paste-fragment commit was extracted behind
`pasteClipboardFragmentLegacy`, and both adapters' single supported-shape
paste no longer contains a page-owned create/save path — the versioned path
removes the raw `nodes.push` + `scheduleSave` for those shapes. Multi-node
fragments, connections, groups, smart-image (scale parity), non-default
loops, content outputs and all other types remain adapter-owned compatibility
on the fragment path; synchronous Alt-drag duplicate gestures stay page-owned
(the drag session needs the copy synchronously); external image paste to a
target node and Smart asset-inbox paste remain adapter-owned; top-level
external file materialization was already routed by R4-22; neither adapter
has an external text-paste creation path (characterized).

Tests: HTTP route test proves clipboard-sourced creation persists/reloads
across Classic image/prompt and Smart smart-prompt record types; frontend
wiring contract pins the candidate gates, one `clipboard` source per adapter,
canvasId envelope propagation, and the retained fragment fallback; envelope
sandbox covers a clipboard command; full `agent-verify.sh` PASS at 360 tests.

Pre-existing finding (reported, not fixed — outside this card): the R4-21
blank-create entry points in both pages omit `canvasId` in their
`createNode(...)` calls while the controller requires it, so all ten
blank-create entries throw at runtime on the default loopback path. Recorded
in `docs/status/CURRENT_EXECUTION_STATUS.md` for Owner rectification.

## Next Recommended Card

`R4-24`

Do not execute the next card in the same Agent run.
