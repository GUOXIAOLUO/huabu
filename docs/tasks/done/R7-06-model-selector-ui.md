# CARD R7-06 — Model Selector UI

- Round: R7
- Priority: P1
- Status: DONE — independent Review PASS; closed 2026-09-11
- Depends on: R7-05

## Goal

Expose Auto/compatible model selection in Task without provider plumbing overload.

## Before Owner

provider-shaped selectors

## After Owner

ModelAvailability selector

## In Scope

- Show compatible entries.
- Support Auto while preserving resolved route visibility.
- Show unavailable reason when relevant.

## Out of Scope

- Do not expose credentials in node UI.

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

- [x] Task binds availability/selection separately from Skill.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

Task model selection was exposed through provider-shaped selectors, without a
route-aware Auto state or explicit unavailable-route explanation.

After:

`WorkbenchModelSelector` renders compatible ModelAvailability entries, supports
Auto with visible resolved-route projection, shows unavailable reasons, and
binds only `modelSelection` into TaskRichNode state independently of Skill
binding.

Duplicate owner removed:

No provider credential, ProviderConnection, ModelDefinition, executor, route
execution, or Skill ownership was added to the Task UI. Availability metadata
is reduced to a credential-free public projection before rendering.

## Next Recommended Card

`R7-07`

Do not execute the next card in the same Agent run.

## Implementation Evidence

Focused `tests/test_model_selector.py` coverage passes (3 tests), proving Auto
resolution visibility, explicit route selection, unavailable reasons, Task
state persistence boundary, credential-free UI serialization, and production
`NodeCardHost → NodeShell → TaskRichNode` wiring. Related
model/availability/compatibility tests remain green. `./scripts/agent-verify.sh`
passes with 784 tests, 152 Python AST files, 134 JavaScript files, 4
architecture guards, and clean diff check. R7-06 remains ACTIVE pending
independent Review; R7-07 was not started.
