# CARD R7-05 — Capability Matching

- Round: R7
- Priority: P0
- Status: DONE — independent Review PASS; closed 2026-09-11
- Depends on: R7-04

## Goal

Match Skill capability requirements to available model routes.

## Before Owner

manual model selection

## After Owner

ModelCompatibilityResolver

## In Scope

- Normalize capability requirements.
- Filter/score valid ModelAvailability entries.
- Return explicit incompatibility reasons.

## Out of Scope

- No silent fallback.

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

- [x] Skill requirements resolve deterministically or fail explicitly.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

Capability requirements relied on manual model selection and had no shared
route compatibility or explicit incompatibility result.

After:

`ModelCompatibilityResolver` normalizes Skill capability requirements, filters
disabled/unavailable or incomplete ModelAvailability routes, scores compatible
routes deterministically, and returns explicit reasons when none match.

Duplicate owner removed:

No ModelDefinition, ModelAvailability, ProviderConnection, Executor, Canvas, or
Node ownership was added; the resolver only consumes those contracts and does
not execute or silently substitute a route.

## Next Recommended Card

`R7-06`

Do not execute the next card in the same Agent run.

## Implementation Evidence

Focused `tests/test_model_compatibility.py` coverage passes (3 tests), proving
normalization, deterministic best-route selection, explicit missing/disabled
reasons, and explicit empty-requirement failure. `./scripts/agent-verify.sh`
passes with 781 tests, 151 Python AST files, 133 JavaScript files, 4
architecture guards, and clean diff check. R7-05 remains ACTIVE pending
independent Review; R7-06 was not started.
