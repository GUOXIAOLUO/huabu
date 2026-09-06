# CARD R4-12 — Generic Legacy Card Rendering Cutover

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-06T21:12+08:00
- Completed: 2026-09-06T21:28+08:00
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

- [x] Generic migrated cards no longer depend on pre-rendered page DOM. (Classic prompt cards on the default path: `mountCanvasNodeShellForLegacy` mounts with `preserveLegacyContent:false` and the `prompt-card` renderer — priority 10, self-registered with `NodeCardHost.registry` — builds the editor DOM inside NodeShell; a behavioral test drives the real NodeCardHost + NodeShell + registry pipeline. The pre-rendered markup survives verbatim as the `legacy_renderer=0` fallback and the prompt branch now skips it on the default path.)
- [x] Regression passes. (AGENT VERIFY: PASS — 339 unit tests, 73 Python AST files, 65 JavaScript files, 4 architecture guards, `git diff --check`.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Legacy pre-rendered DOM adoption — prompt cards were rendered as page
HTML strings first and adopted into NodeShell afterwards, with page-bound
listeners.

After: Registry-owned generic rendering — the `prompt-card` renderer owns the
prompt card DOM (textarea, template button, live counter with over-limit
class) inside NodeShell; the page keeps state and services behind
rendererOptions callbacks (`onPromptInput`, `onOpenTemplate`, `templateActive`,
counter limits, scroll binding). Smart's composer-owned smart-prompt card is
intentionally not migrated; provider/execution systems remain compatibility
only per card scope.

Duplicate owner removed: the page's pre-rendered prompt DOM for the default
path — the markup now exists only inside the `legacy_renderer=0` fallback
branch; the ownership-matrix Prompt (Classic) row and map section record the
cutover.

## Next Recommended Card

`R4-13`

Do not execute the next card in the same Agent run.
