# CARD R4-32 — Extract Classic Provider Compatibility

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-07T12:13+08:00 (Owner authorization via in-conversation
  "提交并开发下一任务")
- Closed: 2026-09-07T12:55+08:00
- Depends on: R4-31 (DONE 2026-09-07T12:40+08:00)

## Goal

Detach retained provider-shaped UI behavior from canvas.js.

## Before Owner

canvas.js

## After Owner

compatibility modules under unified runtime

## In Scope

- Extract presentation/controls.
- Use unified render/interaction boundaries.
- Remove Canvas lifecycle ownership.

## Out of Scope

- No R7 registry.

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

- `test_provider_controls_module_owns_the_canvas_commit_contract` — vm-sandbox
  behavioral test over the real `provider-controls.js`: `setField`/`save`/
  `render` delegate to the injected host, the handle is frozen, and a missing
  op or a non-object host throws `TypeError`.
- `test_provider_controls_is_loaded_before_the_classic_page_and_llm_body_uses_it` —
  the module loads ahead of `canvas.js`; the page constructs the handle via
  `ensureProviderControls()`; `renderLLMBody` delegates its provider/model/
  system/mode controls through `providerControls.setField(...)`; the old direct
  `node.llmProvider = e.target.value` / `node.showSystem = !node.showSystem` /
  `node.systemPrompt = e.target.value` writes are gone; the module has zero
  Classic leak.

## Regression

Run:

```bash
./scripts/agent-verify.sh
```

Result: PASS at 407 Python unit tests (baseline 405; +2), PASS Python AST
parse, PASS JavaScript syntax, PASS Architecture guards (4), PASS
`git diff --check`. `AGENT VERIFY: PASS`.

## Definition of Done

- [x] Provider compatibility no longer makes canvas.js a product runtime.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

`canvas.js`'s `renderLLMBody` owned the provider-card control → Canvas
lifecycle/state path directly — its handlers wrote `node.llmProvider` /
`node.model` / `node.showSystem` / `node.systemPrompt` / `node.mode` inline and
called `render()` / `scheduleSave()` themselves.

After:

`static/js/workbench/canvas/provider-controls.js`
(`window.WorkbenchCanvasProviderControls`) owns the bounded control-commit
contract (`setField` / `save` / `render`); the Classic page injects the
concrete Canvas operations, and `renderLLMBody` routes its five controls
through the `providerControls` handle.

Duplicate owner removed:

`renderLLMBody`'s handlers no longer write Canvas state or call
`render`/`scheduleSave` directly — there is exactly one owner for the
provider-control commit path (`provider-controls.js`), with no redundant
page-side copy. The other provider bodies remain page-owned compatibility
(out of this card's narrow cutover).

## Next Recommended Card

`R4-33`

Do not execute the next card in the same Agent run.
