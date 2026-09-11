# CARD R4-30 — Extract Smart Execution Compatibility

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-07T11:50+08:00 (Owner authorization via in-conversation
  "提交并开发下一任务")
- Closed: 2026-09-07T12:30+08:00
- Depends on: R4-29 (DONE 2026-09-07T12:05+08:00)

## Goal

Keep required pre-R8 Smart execution behavior without letting it own Canvas.

## Before Owner

smart-canvas.js

## After Owner

bounded execution compatibility module

## In Scope

- Identify only required R4 compatibility.
- Detach Canvas lifecycle/state ownership.
- Keep future R8 design out.

## Out of Scope

- No ExecutionRuntime implementation.

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

- `test_execution_host_module_owns_the_canvas_lifecycle_contract` — vm-sandbox
  behavioral test over the real `execution-host.js`: delegates all five ops
  (`markRunning` coerces 0→false, `writePromptResult` passes through, `save` /
  `render` / `notifyError` forward), the handle is frozen, and a missing op or
  a non-object host throws `TypeError`.
- `test_smart_execution_compatibility_manifest_is_grounded_in_source` — parses
  the doc's embedded JSON manifest and verifies every entry `function` and
  every `evidence` name exists in `smart-canvas.js`, dispositions are from the
  allowed set, and the classification is non-trivial (host-cutover, seamed, and
  host-candidate all present).
- `test_execution_host_is_loaded_before_the_smart_page_and_run_prompt_llm_uses_it` —
  the module loads ahead of `smart-canvas.js`; the page constructs
  `executionHost` and `runPromptLLMNode` delegates `markRunning` /
  `writePromptResult` / `save` / `notifyError`; the old direct
  `node.promptResult = (result.text || '').trim()` and
  `node.llmProvider = provider;` writes are gone; the module has zero Smart
  leak.

## Regression

Run:

```bash
./scripts/agent-verify.sh
```

Result: PASS at 399 Python unit tests (baseline 396; +3), PASS Python AST
parse, PASS JavaScript syntax, PASS Architecture guards (4), PASS
`git diff --check`. `AGENT VERIFY: PASS`.

## Definition of Done

- [x] Compatibility works through unified Canvas ownership.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

`smart-canvas.js` owned the execution path's Canvas lifecycle/state directly —
`runPromptLLMNode` (and the generation/cascade entry points) wrote
`node.running` / `node.promptResult` / `node.promptResultOutdated` /
`node.llmProvider` / `node.llmModel` inline and called `render()` /
`scheduleSave()` / `toast()` themselves.

After:

`static/js/workbench/canvas/execution-host.js`
(`window.WorkbenchCanvasExecutionHost`) owns the bounded Canvas-lifecycle
contract (`markRunning` / `writePromptResult` / `save` / `render` /
`notifyError`); the Smart page injects the concrete operations, and
`runPromptLLMNode` routes its side-effects through the `executionHost` handle.
The characterization doc scopes the remaining entry points as host-candidates.

Duplicate owner removed:

`runPromptLLMNode` no longer writes Canvas state directly — its
`node.promptResult` / `node.llmProvider` / `node.running` writes and its
`render` / `scheduleSave` / `toast` calls now go through the single host
handle, with no redundant page-side copy.

## Next Recommended Card

`R4-31`

Do not execute the next card in the same Agent run.
