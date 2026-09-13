# CARD R7-03 — ModelDefinition

- Round: R7
- Priority: P0
- Status: DONE — independent Review PASS; closed 2026-09-11
- Depends on: R7-02

## Goal

Represent model identity/capabilities independently from access route.

## Before Owner

provider-specific model strings

## After Owner

ModelDefinition

## In Scope

- Define model id/provider-family-neutral metadata/capabilities/context/IO metadata.
- Import/project existing model lists.

## Out of Scope

- Do not encode connection credentials.

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

- [x] ModelDefinition is not an availability instance.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

Model identity was represented by provider-specific model strings and lists;
there was no independent model identity contract.

After:

`ModelDefinition` owns provider-neutral model id/family, display name,
normalized capabilities, input/output modalities, context window, parameter
schema, and native metadata. `ModelDefinitionAdapter` projects legacy model
strings/objects and lists without adding provider or connection ownership.

Duplicate owner removed:

No ProviderConnection, CredentialRef, ModelAvailability, route, executor,
credential, Canvas, or Node ownership was added. Existing provider model lists
remain compatibility input rather than becoming a second canonical store.

## Next Recommended Card

`R7-04`

Do not execute the next card in the same Agent run.

## Implementation Evidence

Focused `tests/test_model_definition.py` coverage passes (3 tests), proving
route-free model identity, context and IO metadata, legacy object/list
projection, deterministic first-seen deduplication, credential/route rejection,
and duplicate metadata rejection. Related provider tests remain green.
`./scripts/agent-verify.sh` passes with 776 tests, 143 Python AST files, 133
JavaScript files, 4 architecture guards, and clean diff check. R7-03 remains
ACTIVE pending independent Review; R7-04 was not started.
