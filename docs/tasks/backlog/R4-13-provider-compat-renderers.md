# CARD R4-13 — Provider-Shaped Compatibility Renderers

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-12

## Goal

Extract provider-shaped legacy card rendering from Canvas product runtime ownership.

## Before Owner

Classic/Smart page runtime

## After Owner

compatibility renderers under unified lifecycle

## In Scope

- Inventory LLM/Comfy/RunningHub/Video/MiniMax/LTX retained UI.
- Move rendering lifecycle behind compatibility renderer boundaries.
- Do not make provider types permanent Core NodeKinds.

## Out of Scope

- Do not build R7 Provider Registry or R8 Execution Runtime.

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

- [ ] Unified RenderRuntime owns lifecycle.
- [ ] Compatibility module owns only legacy/provider presentation behavior.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-14`

Do not execute the next card in the same Agent run.
