# CARD R6-01 — PortTypeRegistry

- Round: R6
- Priority: P0
- Status: DONE
- Previous implementation: COMPLETE — production wiring repaired 2026-09-10
- Independent Review: PASS — 2026-09-10
- Depends on: R5-13

## Goal

Establish an extensible registry for typed ports without industry-specific permanent Core types.

## Before Owner

stringly-typed/ad hoc port artifact types

## After Owner

PortTypeRegistry

## In Scope

- Characterize existing port strings.
- Define generic core types and extension mechanism.
- Include generic CAD-compatible type such as asset.cad without WholeHouse semantics.

## Out of Scope

- No executor-specific port logic.

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

- [x] Ports resolve through one registry, including the NodeCreationService production seam.
- [x] Package extension does not require new Core NodeKind.

## Re-execution Evidence (2026-09-10)

- `NodeCreationService` accepts an injected `PortTypeRegistry` and resolves every
  definition port set before persistence; unknown types fail with
  `invalid_port_types` and cannot mutate the repository or audit log.
- The localhost legacy creation wiring supplies the generic Core registry,
  preserving existing definitions while keeping the registry as the single
  resolution boundary.
- Focused tests: 36 passed (`test_port_type_registry`, `test_node_creation_service`,
  `test_legacy_node_adapters`). Full `./scripts/agent-verify.sh`: PASS (696 tests,
  104 Python AST files, 121 JavaScript files, 4 architecture guards, clean diff
  check).
- Developer Git Review: PASS. Independent Review PASS; card is ready for archive.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: `InputPort` and `OutputPort` carried stringly-typed values without one resolver or generic inheritance semantics.

After: `PortTypeRegistry` owns namespaced type registration, lookup, port-set resolution, parent compatibility, generic Core types, and the `asset.cad` type.

Duplicate owner removed: callers no longer need local type tables or compatibility rules; package extensions register through the same registry seam and do not add Core NodeKinds or executor-specific logic.

Verification: the retained registry tests plus the production NodeCreationService
seam tests pass; the re-execution evidence above is the current verification.
The earlier 32-test/689-test result is historical and does not replace the current
696-test verification.

## Next Recommended Card

`R6-02`

Do not execute or activate the next card before independent Review PASS.
