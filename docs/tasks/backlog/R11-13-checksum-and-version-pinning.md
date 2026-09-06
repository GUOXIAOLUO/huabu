# CARD R11-13 — Checksum and Version Pinning

- Round: R11
- Priority: P0
- Status: BACKLOG
- Depends on: R11-12

## Goal

Pin every handoff reference and checksum content to prevent ambiguity.

## Before Owner

latest/current mutable refs

## After Owner

exact version refs + checksums

## In Scope

- Compute/store checksums.
- Reject missing/mutable unresolved refs.
- Verify on reopen/export.

## Out of Scope

- No 'latest' refs inside approved handoff.

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

- [ ] Package validation detects changed/missing content.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R11-14`

Do not execute the next card in the same Agent run.
