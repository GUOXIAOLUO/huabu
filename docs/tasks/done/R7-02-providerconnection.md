# CARD R7-02 — ProviderConnection

- Round: R7
- Priority: P0
- Status: DONE — independent Review PASS; closed 2026-09-11
- Depends on: R7-01

## Goal

Represent configured provider connections separately from provider definitions.

## Before Owner

provider settings/global secrets

## After Owner

ProviderConnection + CredentialRef

## In Scope

- Define connection id/provider/ref/config/credential ref/status metadata.
- Keep secrets outside normal domain serialization.

## Out of Scope

- No raw secret persistence in Canvas/Node.

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

- [x] Multiple connections per provider are supported conceptually and tested.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

Provider settings/global secrets were the only provider connection-shaped
owner; no independent connection or credential-reference contract existed.

After:

`ProviderConnection` owns connection identity, provider identity, external
reference, non-secret configuration, credential reference, status, and neutral
metadata. `CredentialRef` contains only an opaque credential-store id.

Duplicate owner removed:

No secret value, ProviderDefinition, ModelDefinition, execution route, or Canvas
node persistence ownership was added. Existing provider settings remain
compatibility input and are not rewritten.

## Next Recommended Card

`R7-03`

Do not execute the next card in the same Agent run.

## Implementation Evidence

Focused `tests/test_provider_connection.py` coverage passes (2 tests), proving
two independently identified connections can share one provider and that
credential values are excluded from normal serialization. It also verifies
opaque CredentialRef validation, secret-field rejection including camelCase and
nested variants, and immutability.
Related ProviderDefinition tests remain green. `./scripts/agent-verify.sh`
passes with 773 tests, 141 Python AST files, 133 JavaScript files, 4
architecture guards, and clean diff check. R7-02 remains ACTIVE pending
independent Review; R7-03 was not started.
