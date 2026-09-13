# CARD R7-01 — ProviderDefinition

- Round: R7
- Priority: P0
- Status: DONE — independent Review PASS; closed 2026-09-11
- Depends on: R6-24

## Goal

Define provider metadata independently from credentials and models.

## Before Owner

provider-shaped settings/code

## After Owner

ProviderDefinition

## In Scope

- Define generic provider id/title/capabilities/config schema metadata.
- Migrate/read existing provider definitions through adapters.

## Out of Scope

- No credentials stored in definition.

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

- [x] Provider definition can exist without a connection.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

Provider metadata lived in provider-shaped settings and compatibility code; no
independent, credential-free ProviderDefinition contract existed.

After:

`ProviderDefinition` owns versioned provider id/title/protocol, capabilities,
configuration-schema metadata, and neutral metadata. The domain contract
rejects credential-like metadata recursively, while
`ProviderDefinitionAdapter` projects only public metadata from legacy payloads
and strips credential-like values.

Duplicate owner removed:

No ProviderConnection, CredentialRef, ModelDefinition, endpoint/account state,
or provider execution ownership was added. Existing provider settings remain
compatibility input rather than becoming the canonical definition.

## Next Recommended Card

`R7-02`

Do not execute the next card in the same Agent run.

## Implementation Evidence

Focused `tests/test_provider_definition.py` coverage passes (3 tests), proving
connection-free construction, immutability/duplicate protection, and legacy
metadata projection without credential values. `./scripts/agent-verify.sh`
passes with 771 tests, 140 Python AST files, 133 JavaScript files, 4
architecture guards, and clean diff check. Independent Review initially found
a domain-level metadata gap; recursive credential rejection was added and the
focused/full verification returned green. Independent Review is pending;
R7-02 was not started.
