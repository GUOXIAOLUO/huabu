# CARD R6-04 — Edge / InputBinding Separation

- Round: R6
- Priority: P0
- Status: DONE — independently reviewed PASS
- Depends on: R6-03
- Completed: 2026-09-11

## Goal

Make graph relation and execution data binding explicitly separate concepts.

## Before Owner

edge-implied input assumptions

## After Owner

separate GraphRelation + InputBinding semantics

## In Scope

- Audit places where an Edge is treated as runtime input.
- Route true data binding through InputBinding.
- Keep visual/semantic edges independent.

## Out of Scope

- Do not remove useful graph visualization.

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

- [x] No normal execution-data path depends solely on an Edge.
- [x] Tests demonstrate Edge can exist without input binding and vice versa.

## Completion Evidence (2026-09-11)

- `ConnectNodesCommand.edge_kind` is a Legacy persistence/display discriminator
  only; graph mutation does not create, resolve, or imply a typed
  `InputBinding`.
- Default generator and Loop input projection APIs read typed `InputBinding`
  references only. Legacy Edge traversal is isolated behind explicitly named
  compatibility adapters and is opt-in at the existing Legacy page boundary.
- Behavioral coverage proves an `EdgeRecord` can exist with no binding, an
  `InputBinding` resolves without an edge, and both records can coexist without
  identity coupling. Frontend coverage proves typed bindings win over unrelated
  Edges and that the explicit Legacy adapters retain old behavior.
- Focused tests: 19 passed across separation, graph mutation, binding
  resolution, and frontend projections. Full `./scripts/agent-verify.sh`: PASS
  (708 tests, 109 Python AST files, 121 JavaScript files, 4 architecture guards,
  clean diff check).
- Developer Git Review: PASS. Independent Review: PASS.

## Final Ownership Evidence

Before: Legacy edge/input projections could be mistaken for one shared runtime
input concept; the application command did not state the distinction.

After: `EdgeRecord`/`GraphMutationService` own graph relations, while
`InputBinding`/`BindingResolver` own typed execution-data references. Legacy
Edge projection is an explicitly named compatibility adapter.

Duplicate owner removed: graph mutation no longer claims binding semantics, and
binding resolution has no Canvas Edge dependency or model invocation.

## Next Recommended Card

`R6-05`

Do not execute the next card in the same Agent run.
