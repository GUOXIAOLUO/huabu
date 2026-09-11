# CARD R4-33 — Extract Classic Execution Compatibility

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-07T12:34+08:00
- Closed: 2026-09-07T12:41+08:00
- Depends on: R4-32

## Goal

Detach required pre-R8 Classic execution behavior from canvas.js.

## Before Owner

canvas.js

## After Owner

bounded compatibility module

## In Scope

- Extract minimal retained execution behavior.
- Remove selection/render/persistence ownership dependencies.

## Out of Scope

- No R8 execution architecture.

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

- [x] Classic execution compatibility runs under unified Canvas ownership.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

`runLLMNode` wrote Canvas lifecycle/state directly — `node.running = true`,
`node.outputText = await callCanvasLLM(...)`, `node.runStatus = 'done'`,
`node.runError = ''`, `refreshNodes([node.id])`, `scheduleSave()`, `alert(...)`.

After:

`runLLMNode` routes those side-effects through the frozen
`WorkbenchCanvasClassicExecutionHost` handle (`markRunning` / `writeOutputText` /
`setRunStatus` / `render` / `save` / `notifyError`), injected by the Classic
page's lazy `ensureClassicExecutionHost()` accessor. The LLM transport
(`callCanvasLLM`) and the cascade orchestrators stay host-candidates.

Duplicate owner removed:

the direct `node.running` / `node.outputText` / `node.runStatus` /
`node.runError` writes and inline `refreshNodes` / `scheduleSave` / `alert`
calls inside `runLLMNode` (owner is now `classic-execution-host.js`).

## Next Recommended Card

`R4-34`

Do not execute the next card in the same Agent run.
