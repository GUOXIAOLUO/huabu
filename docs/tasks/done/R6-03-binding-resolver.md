# CARD R6-03 — Binding Resolver

- Round: R6
- Priority: P0
- Status: DONE
- Independent Review: PASS — 2026-09-10
- Depends on: R6-02

## Goal

Resolve generic binding references into normalized inputs.

## Before Owner

call-site-specific resolution

## After Owner

BindingResolver

## In Scope

- Support asset-like, artifact-like, collection, entity-like and literal references at the abstraction level available.
- Keep unresolved/future references explicit.
- Return typed errors.

## Out of Scope

- No model invocation.

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

- [x] Bindings resolve deterministically and do not rely on Canvas edges.

## Re-execution Evidence (2026-09-10)

- Added the industry-neutral `BindingResolver` application module with an
  injected resource resolver seam for asset-like, artifact-like, collection,
  and entity-like references.
- Literal JSON references normalize locally without model invocation. Missing
  adapters and missing sources remain explicit `unresolved` results; disabled
  bindings remain explicit `disabled` results. Duplicate IDs and malformed
  literals return typed `BindingResolutionError` values.
- Results are deterministic by `(order, binding_id)` and the resolver has no
  Canvas, Edge, provider, executor, or model dependency.
- Focused tests: 21 passed across binding resolution, typed bindings, node
  records, creation, and Legacy adapters. Full `./scripts/agent-verify.sh`:
  PASS (703 tests, 108 Python AST files, 121 JavaScript files, 4 architecture
  guards, clean diff check).
- Developer Git Review: PASS. Independent Review pending; do not archive or
  activate R6-04 in this turn.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: binding reference resolution was absent from a shared module, leaving
future callers to interpret source references locally.

After: `BindingResolver` owns deterministic ordering, literal normalization,
injected resource lookup, explicit unresolved/disabled states, and typed errors.

Duplicate owner removed: no caller needs Canvas-edge traversal or source-type
specific fallback logic to normalize bindings; execution remains out of scope.

## Next Recommended Card

`R6-04`

Do not execute the next card in the same Agent run.
