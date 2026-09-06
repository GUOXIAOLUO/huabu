# CARD ENG-06 — Architecture Guards Expansion

- Round: ENG
- Priority: P1
- Status: BACKLOG
- Depends on: R5+

## Goal

Continuously enforce architecture invariants as new systems land.

## Before Owner

document-only constraints

## After Owner

mechanical dependency guards

## In Scope

- Add guards for Core↔WholeHouse, Agent direct persistence, provider SDK in domain, permanent industry NodeKind, legacy ownership growth.
- Update as rounds add boundaries.

## Out of Scope

- Do not create brittle string-only guards where dependency tests are possible.

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

- [ ] Key invariants fail CI on intentional violations.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`ENG-ONGOING`

Do not execute the next card in the same Agent run.
