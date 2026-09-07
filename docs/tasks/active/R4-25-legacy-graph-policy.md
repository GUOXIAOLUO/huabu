# CARD R4-25 — Legacy Graph Compatibility Policy

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-07T09:20+08:00 (Owner authorization via in-conversation
  "提交并开发下一任务")
- Closed: 2026-09-07T09:45+08:00 (implementer evidence; independent review
  pending per AGENT_CONTRACT §9)
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

- [x] Historical behavior preserved without Core if classic/smart branches.

Characterization (what was contained, where it lived before):

- Classic `applyClassicConnectionSideEffects` (`static/js/canvas.js`) owned
  three rules inline: the group add-member type check
  (`['image','prompt'].includes(groupedNode?.type)` gated by
  `graphCommand('canvas.group.add-member','classic')`), plus an unconditional
  `syncLatestGeneratedOutputToConnection(fromId, toId)` and
  `syncGeneratorInputs()`.
- Smart `connectInputNodeVersioned` (`static/js/smart-canvas.js`) owned the
  loop-input rule inline: `to.type === 'smart-loop'` → derive
  `looksImage` / `looksPrompt` from the source shape and the smart-group
  image/prompt counts, flip `to.imageInput` / `to.showPrompt`, re-fit via
  `fitSmartLoopNode`, and reject the connect when neither `canImage` nor
  `canPrompt` holds.

Seam (what owns it now):

- New module `static/js/workbench/canvas/legacy-graph-compatibility.js`
  exposing `window.WorkbenchLegacyGraphCompatibility.create(...)` with
  `applyClassicConnect({fromId, toId, fromNode, toNode})` →
  `{groupAddMember, addedNodeIds, shouldSyncOutput, shouldSyncGeneratorInputs}`
  and `prepareSmartConnect({fromNode, toNode})` →
  `{shouldConnect, loopTouched, flipImageInput, flipShowPrompt, fit,
  toImageInput, toShowPrompt, appendInputNodeId}`.
- Both pages keep only the mechanically-unavoidable execution of page-owned
  effects and reach the policy through a lazy accessor
  (`ensureLegacyGraphCompatibilityPolicy` /
  `ensureSmartLegacyGraphCompatibilityPolicy`).
- `workbench/application/graph_mutation.py` remains untouched and
  industry-neutral — still zero `smart-loop` / `imageInput` / `showPrompt` /
  `syncLatestGeneratedOutput` / `group.items` / `inputNodeIds` references.

Historical quirks deliberately preserved (a refactor, not a behavior change):

- Classic output / generator syncs stay **unconditional** on every connect
  commit — they were never gated on node type.
- Smart `loopTouched` follows `looksImage || looksPrompt`, **not** the flips,
  so revisiting an already-flagged loop still re-fits it.
- Smart `canImage` / `canPrompt` are evaluated against the flags **after**
  the flips are applied.

Tests proving it (all in `tests/test_frontend_workbench_modules.py`):

- `test_legacy_graph_compatibility_policy_owns_connect_side_effects` —
  policy module exists and is the single owner; both page helpers delegate
  through the accessor; no adapter rule literal survives in either helper;
  Core graph service has zero adapter leak.
- `test_legacy_graph_compatibility_policy_matches_classic_smart_history` —
  behavioral: drives the real policy in a vm sandbox over representative
  node pairs (group add-member + idempotence, smart-prompt → smart-loop,
  smart-loop → smart-loop flag copy, no-op revisit, smart-image target
  append) and pins the historical semantics above.
- `test_classic_connect_side_effects_apply_the_policy_projection` —
  behavioral: drives the REAL `applyClassicConnectionSideEffects` out of
  `canvas.js` with the real policy and page-shaped mocks; asserts group
  membership is added once, idempotent on repeat, suppressed when the
  command gate denies it, and that both syncs run on every commit.
- R4-24's `test_versioned_connect_drops_land_at_the_application_command`
  now also loads the real policy into the Smart sandbox, so the helper and
  the policy are exercised together.

Verification: `./scripts/agent-verify.sh` PASS at 373 Python unit tests
(baseline 370; +3 from this card), PASS Python AST parse, PASS JavaScript
syntax, PASS Architecture guards (4), PASS `git diff --check`.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before: the Classic / Smart connect side-effect RULES were duplicated as
inline branches inside the two page runtimes —
`applyClassicConnectionSideEffects` in `static/js/canvas.js` (group
membership type check + command gate + unconditional output/generator syncs)
and the `to.type === 'smart-loop'` block in `connectInputNodeVersioned` in
`static/js/smart-canvas.js` (looksImage/looksPrompt derivation, flag flips,
re-fit, connect rejection). Neither rule was testable in isolation and both
sat next to the durable mutation they decorate.

After: one named owner — `static/js/workbench/canvas/legacy-graph-compatibility.js`
(`window.WorkbenchLegacyGraphCompatibility`). It is the only place that
names the Classic group-membership types, issues
`canvas.group.add-member`, derives the Smart loop-input shape, and decides
`loopTouched` / `shouldConnect`. Both pages keep executing the page-owned
effects but only as a mechanical application of the projection the policy
returns. Core `GraphMutationService` stays industry-neutral.

Duplicate owner removed: the type literals and command ids that decided
these side effects no longer exist in the page sources —
`['image','prompt'].includes(...)` and
`graphCommand('canvas.group.add-member','classic')` are gone from
`canvas.js`, and `smart-loop` / `looksImage` / `looksPrompt` are gone from
`connectInputNodeVersioned` in `smart-canvas.js`. Each rule now has exactly
one home. Three existing contracts that pinned the old inline forms
(R4-24 connect-drop wiring, shared command-catalog usage, Classic node-shell
reuse) were updated to pin the new owner instead.

## Next Recommended Card

`R4-26`

Do not execute the next card in the same Agent run.
