# CARD R4-10 — Group Rendering Cutover

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-06T19:38+08:00
- Completed: 2026-09-06T20:25+08:00
- Depends on: R4-09

## Goal

Use Group as the first complete rendering ownership proof.

## Before Owner

Classic/Smart group rendering

## After Owner

Unified RenderRuntime

## In Scope

- Move group mount/update/unmount to unified rendering.
- Preserve position/size/reload/delete behavior.
- Remove duplicate group rendering callbacks from page runtimes.

## Out of Scope

- Do not redesign Group semantics.

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

- [x] Create/render/update/move/resize/reload/delete pass. (Versioned group create/delete and shell-mount tests pass; resize and member-sync paths untouched; the runtime destroys mounted handles on delete and canvas loads; full regression 334 tests PASS including the behavioral `mountGroupCard` test and both-adapters cutover contract test.)
- [x] Only one product rendering owner remains. (Group mount policy — record assembly from own/member media, media-vs-legacy decision with `mediaEnabled:false` rollback, mount execution and lifecycle, resolved shell view on the result — lives only in `WorkbenchRenderRuntime.mountGroupCard`; Classic's group branch (`mountCanvasGroupShell`) and Smart's group batch delegate with only gates, member-media extraction, intents, and control selectors. Smart's inline record-selection ternary was removed.)

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: Classic/Smart group rendering — both pages implemented the group mount
policy separately (media-record assembly, renderer choice, legacy-content
preserve, control stripping) and discarded mounted handles.

After: Unified RenderRuntime — `mountGroupCard` on the render runtime owns the
complete group mount contract and its lifecycle entry; pages supply only flag
gates, member-media extraction, intents, and control selectors; the
ownership-matrix Group rows and map section record the cutover.

Duplicate owner removed: the per-page group mount policy — Smart's inline
record-selection (`smartGroupMediaRecord : legacyNodeView` ternary) and the
duplicated decision logic in Classic's media mount are gone; the old record
builder survives only inside the eligibility gate.

## Next Recommended Card

`R4-11`

Do not execute the next card in the same Agent run.
