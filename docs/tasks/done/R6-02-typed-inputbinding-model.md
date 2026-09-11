# CARD R6-02 — Typed InputBinding Model

- Round: R6
- Priority: P0
- Status: DONE
- Independent Review: PASS — 2026-09-10
- Depends on: R6-01

## Goal

Replace transitional list[dict] input bindings with a typed domain model.

## Before Owner

untyped NodeRecord input_bindings

## After Owner

InputBinding model

## In Scope

- Define binding id/target/source_type/source_ref/role/order/enabled/metadata.
- Add validation/serialization.
- Add compatibility adapter for existing payloads.

## Out of Scope

- No execution yet.

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

- [x] Typed model round-trips and legacy payloads remain readable.

## Re-execution Evidence (2026-09-10)

- Added the industry-neutral `InputBinding` model with binding identity,
  target port, typed source category/reference, role, ordering, enabled state,
  and metadata validation.
- `NodeRecord` now stores typed `InputBinding` values while
  `LegacyInputBinding` preserves unknown old objects without guessing their
  semantics. `InputBindingAdapter` converts both directions losslessly;
  Legacy API serialization retains the original object shape.
- `NodeCreationService` converts initial binding payloads at the application
  seam, and `LegacyCanvasAdapter` converts existing node payloads on read.
  No execution logic or provider/industry-specific behavior was added.
- Focused tests: 42 passed. Full `./scripts/agent-verify.sh`: PASS (699 tests,
  106 Python AST files, 121 JavaScript files, 4 architecture guards, clean
  diff check).
- Developer Git Review: PASS. Independent Review pending; do not archive or
  activate R6-03 in this turn.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: `NodeRecord.input_bindings`, `NodeCreateCommand.initial_bindings`, and
Legacy node payloads used untyped dictionaries with no typed/opaque seam.

After: `InputBinding` owns typed binding validation and serialization;
`LegacyInputBinding` plus `InputBindingAdapter` owns compatibility conversion
and lossless legacy output.

Duplicate owner removed: callers no longer need to interpret source categories
or copy binding dictionaries; execution remains out of scope and no executor
owns binding semantics.

## Next Recommended Card

`R6-03`

Do not execute the next card in the same Agent run.
