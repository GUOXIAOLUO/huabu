# CARD R4-41 — R4 Full Acceptance Gate

- Round: R4
- Priority: P0
- Status: BLOCKED
- Activated: 2026-09-09
- Depends on: R4-40

## Goal

Prove Unified Canvas Cutover is complete before activating R5.

## Before Owner

R4 in_progress

## After Owner

R4 PASS or explicit blocker report

## In Scope

- Run data/restart/stale-write tests.
- Run selection/drag/resize/zoom/pan/keyboard/connect/group/clipboard.
- Run media/workflow compatibility.
- Run 100/300 node performance and listener/timer/DOM duplication checks.
- Verify one page/runtime/persistence/render/interaction/creation owner.

## Out of Scope

- Do not mark PASS with known duplicate runtime ownership.

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

- [ ] Every formal R4 gate item passes or R4 remains in_progress with concrete blockers.
- [ ] Only after full PASS may active_round become R5.

## Blockers

- The R4-39/R4-40 cutover is integrated on local `main` at `c201b0f`.
  The Integration Owner must still evaluate every A–N checklist item against
  that commit; all checklist boxes remain open, so integration state is not
  yet an acceptance decision.
- The committed evidence contains 100/300-node interaction samples, a source
  audit and one five-render 300-node heap observation. It is not a complete
  merged Gate-K record: it has no explicit per-item acceptance matrix, no
  100-node memory observation and no repeated growth threshold. It therefore
  cannot close DOM/listener/timer/observer/memory acceptance by itself.
- `docs/plans/R4_FINAL_GATE_CHECKLIST_MULTI_AGENT.md` remains `R4: NOT PASS`
  with all required acceptance items unchecked.
- Review finding repaired in this run: title/icon edits in
  `canvas-app-records.js` now use the dedicated `/meta` POST boundary and no
  longer PUT the full graph payload. Regression coverage was added and passes.
- Review finding repaired in this run: compatibility-only graph-array
  projections in `canvas-app-interaction.js` now route through the bounded
  `legacy-canvas-mutation.js` seam; the interaction module has no direct
  `nodes.push`/`connections.push` writes. This is still compatibility code,
  not a claim that the formal merged integration gate has passed.
- Review finding repaired in this run: interaction blur cleanup and canvas
  metadata/crop resize cleanup now share one global listener per event. Output
  preview pan and compare-slider now share one guarded global pointer pair;
  touch handlers remain separate for the touch lifecycle.
- Remote polling lifecycle is covered by an idempotent start/stop regression
  test; repeated starts create one interval and repeated stops clear it once.
- Output preview/compare initialization is now idempotent, preventing repeated
  element-listener binding on re-entry; focused source-contract coverage
  passes.
- Runtime listener/timer audit is committed in
  `docs/benchmarks/r4-41-runtime-audit-2026-09-09.md`; it remains diagnostic
  evidence and does not satisfy the Integration Owner Gate by itself.
- The same local audit now includes a 300-node Chromium heap observation over
  five confirmed real re-renders: 24,905,516 bytes before and after (zero observed
  delta). It is diagnostic evidence only, not a complete merged acceptance
  result.
- Isolated local browser rechecks repaired an actual viewport-controller
  initialization defect and the harness's cross-frame event sequence. The
  disposable 100-node run passed zoom/pan/minimap visual updates in 15.400 /
  27.500 / 116.400 ms; the disposable 300-node run passed them in 10.900 /
  62.100 / 30.500 ms. These local measurements remain diagnostic only and do
  not supply the required complete memory or duplicate-resource acceptance
  evidence.

The committed regression verifier is green (637 Python tests, 81 Python AST
files, 112 JavaScript syntax files, 4 architecture guards, and clean diff
check), but that result does not override the formal acceptance requirements
above.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: R4-40's stable Canvas runtime and retired-flag state, with the R4-39 /
R4-40 changes not yet accepted by the formal R4 gate.

After: no ownership change authorized by this acceptance-only card; R4 remains
`in_progress` and R5 remains unauthorized.

Duplicate owner removed: not asserted by this acceptance-only card until the
Integration Owner completes the final duplicate-runtime evidence review.

## Next Recommended Card

`R5-01`

Do not execute the next card in the same Agent run.
