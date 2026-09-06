# CARD R4-12 — Generic Legacy Card Rendering Cutover

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-11

## Goal

Replace legacy-page-render-then-wrap behavior for generic nodes with NodeRecord → Registry → Renderer → NodeShell.

## Before Owner

legacy pre-rendered DOM adoption

## After Owner

registry-owned generic rendering

## In Scope

- Identify generic node families still using adopted legacy DOM.
- Move one family at a time to renderer-owned DOM.
- Keep lossless legacy payload compatibility where required.

## Out of Scope

- Provider/execution systems remain compatibility only.

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

- [ ] Generic migrated cards no longer depend on pre-rendered page DOM.
- [ ] Regression passes.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-13`

Do not execute the next card in the same Agent run.
