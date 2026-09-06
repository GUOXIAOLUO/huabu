# CARD R4-04 — Split-Brain Regression Suite

- Round: R4
- Priority: P0
- Status: BACKLOG
- Depends on: R4-03

## Goal

Turn the known split-brain incident into permanent regression coverage.

## Before Owner

Implicit safety assumptions

## After Owner

Executable regression protection

## In Scope

- Test sqlite authority normal routing.
- Test sqlite authority with old routing flag disabled.
- Test supported legacy migration/read state.
- Test restart/authority persistence and write isolation.

## Out of Scope

- No unrelated repository refactor.

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

- [ ] All split-brain tests prove behavior, not only constants.
- [ ] agent-verify passes or existing failures are documented.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-05`

Do not execute the next card in the same Agent run.
