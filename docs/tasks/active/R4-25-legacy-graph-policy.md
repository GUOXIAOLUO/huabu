# CARD R4-25 — Legacy Graph Compatibility Policy

- Round: R4
- Priority: P1
- Status: ACTIVE
- Activated: 2026-09-07T09:20+08:00 (Owner authorization via in-conversation
  "提交并开发下一任务")
- Depends on: R4-24 (DONE 2026-09-07T09:02+08:00)

## Goal

Contain Smart/Classic historical connect side effects in compatibility policy.

## Before Owner

page runtime side effects

## After Owner

LegacyGraphCompatibilityPolicy/repository adapter

## In Scope

- Characterize Smart inputNodeIds.
- Characterize Classic group/generator-output sync.
- Apply necessary side effects atomically in compatibility boundary.

## Out of Scope

- Core graph service must remain generic.

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

- [ ] Historical behavior preserved without Core if classic/smart branches.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-26`

Do not execute the next card in the same Agent run.
