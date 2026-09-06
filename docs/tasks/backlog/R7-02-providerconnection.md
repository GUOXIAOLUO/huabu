# CARD R7-02 — ProviderConnection

- Round: R7
- Priority: P0
- Status: BACKLOG
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

- [ ] Multiple connections per provider are supported conceptually and tested.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R7-03`

Do not execute the next card in the same Agent run.
