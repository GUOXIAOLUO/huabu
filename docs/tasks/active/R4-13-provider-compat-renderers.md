# CARD R4-13 — Provider-Shaped Compatibility Renderers

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-06T21:35+08:00
- Completed: 2026-09-06T21:54+08:00
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

- [x] Unified RenderRuntime owns lifecycle. (Provider-shaped Classic cards resolve to the `provider-compat` renderer through the registry and mount/unmount via the runtime's keyed handle lifecycle; the mounted-handle `destroy()` now carries per-card cleanup — the LTX editor teardown fires at the runtime unmount boundary, and `deleteSelectedNodes` (previously with no runtime unmounts at all) unmounts every removed id through the runtime.)
- [x] Compatibility module owns only legacy/provider presentation behavior. (`provider-compat-renderer.js` adopts the page-built body verbatim and adds no execution, provider, or persistence logic; provider identities stay legacy `definition_ref` values, never Core NodeKinds.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Classic/Smart page runtime — provider card cleanup (LTX editor destroy)
was called directly inside page delete handlers, `deleteSelectedNodes` had no
runtime unmounts at all, and provider cards resolved through the anonymous
source-payload fallback.

After: Compatibility renderers under unified lifecycle — `provider-compat`
(priority 5) owns adoption + per-card cleanup for the nine provider-shaped
Classic types; page deletes route through runtime unmounts; the
ownership-matrix provider row and map section record the boundary.

Duplicate owner removed: direct page cleanup ownership — `deleteNode` no
longer calls `destroyLTXEditor` itself and the bulk delete flow's direct
cleanup loop was replaced by runtime unmounts; the LTX teardown now has
exactly one owner (the renderer's destroy hook behind the runtime).

## Next Recommended Card

`R4-14`

Do not execute the next card in the same Agent run.
