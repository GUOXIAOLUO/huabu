# CARD R11-11 — HandoffManifest

- Round: R11
- Priority: P0
- Status: BACKLOG
- Depends on: R11-10

## Goal

Define a deterministic manifest for formal external handoff.

## Before Owner

ad hoc export bundles

## After Owner

HandoffManifest

## In Scope

- Include version refs/checksums/destination/export format/validation/creator/approver/status.
- Version schema.

## Out of Scope

- No Kujiale-specific Core fields.

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

- [ ] Manifest fully identifies handed-off content.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R11-12`

Do not execute the next card in the same Agent run.
