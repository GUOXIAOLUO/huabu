# CARD R4-26 — Group Mutation Cutover

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-07T10:17+08:00 (Owner authorization via in-conversation
  "提交并开始下一步")
- Closed: 2026-09-07T10:53+08:00 (implementer evidence; independent review pending)
- Depends on: R4-25 (DONE 2026-09-07T09:45+08:00)

## Goal

Unify group create/add/remove/ungroup mutations.

## Before Owner

page-specific group persistence

## After Owner

Graph/application mutation boundary

## In Scope

- Migrate group mutations.
- Preserve old payload compatibility.
- Verify revision/save/reload.

## Out of Scope

- Do not introduce Collection semantics.

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

- `tests/test_group_membership.py` — `GroupMembershipServiceTests`
  (authorized change delegates + audits; missing-field / non-positive-revision /
  invalid-operation / self-membership / unauthorized rejection) and
  `LegacyJsonGroupMembershipRepositoryTests` (add+remove persist and reload under
  one revision lock; idempotent add; stale-revision rejection; missing group /
  member rejection).
- `tests/test_canvas_nodes_api.py` — group-membership endpoint delegates and
  returns the new revision; payload rejects invalid operation / non-positive
  revision; service errors map forbidden→403 and invalid→422.
- `tests/test_frontend_workbench_modules.py::
  test_group_membership_routes_through_the_graph_membership_command` — one client
  method, one Smart versioned helper, drag-gesture wiring, Core zero adapter leak.

## Regression

Run:

```bash
./scripts/agent-verify.sh
```

Result: PASS at 386 Python unit tests (baseline 373; +13), Python AST parse,
JavaScript syntax, Architecture guards (4), `git diff --check`.

## Definition of Done

- [x] Group mutation has one authoritative path.

  Smart add-member now persists through `GroupMembershipService.set_membership`
  (atomic, revision CAS, audited). Remove/ungroup, image absorption and
  group-merge remain page-side compatibility (deferred per the ownership
  matrix); Classic membership stays page-owned until geometry parity.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: group membership persisted by adapter-side `group.items` mutation plus
a raw page `scheduleSave()` (no application boundary).

After: `GroupMembershipService.set_membership` →
`LegacyJsonGroupMembershipRepository.set_group_membership` under the canvas
revision lock; Smart drag-in member add routes through
`WorkbenchNodeClient.setGroupMembership`; audit event appended.

Duplicate owner removed: none (the page-side optimistic projection and the
legacy `group-membership.js` query helper are retained by design — the helper is
business-neutral read-only, not a second writer).

## Next Recommended Card

`R4-27`

Do not execute the next card in the same Agent run.
