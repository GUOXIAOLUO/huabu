# CARD R4-09 — Establish Unified RenderRuntime

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-08

## Goal

Create a real RenderRuntime that owns lifecycle rather than another helper facade.

## Before Owner

page runtimes + hosts

## After Owner

Unified RenderRuntime

## In Scope

- Define mount/update/unmount contract.
- Own renderer selection and NodeShell lifecycle.
- Wire one bounded node family through it.
- Prove duplicate page ownership is removed for that responsibility.

## Out of Scope

- Do not migrate every node family at once.

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

Add or run the smallest behavioral tests that prove this card's exact goal.
Do not rely only on source-string checks when runtime behavior can be tested.

## Regression

Run:

```bash
./scripts/agent-verify.sh
```

## Definition of Done

- [ ] RenderRuntime owns a complete lifecycle slice.
- [ ] At least one former page owner is removed.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-10`

Do not execute the next card in the same Agent run.
