# CARD R6-24 — Common Image Analysis Configuration Proof

- Round: R6
- Priority: P0
- Status: DONE — independent Review PASS (2026-09-11)
- Depends on: R6-23

## Goal

Prove Asset → Task + common.image-analysis SkillBinding → save/restart without actual execution.

## Before Owner

individual components

## After Owner

cross-system persisted configuration proof

## In Scope

- Register a minimal generic common.image-analysis definition.
- Create Task binding to an image input and prompt.
- Save/restart/reload and verify exact refs/versions.

## Out of Scope

- No real AI/model execution.

## Compatibility / Migration

- Preserve existing behavior and data unless the card explicitly authorizes a migration.

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

- Add/run the smallest behavioral tests that prove this card's goal.
- Run `./scripts/agent-verify.sh`.

## Definition of Done

- [x] End-to-end configuration survives restart with no WholeHouse dependency.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

Asset input, Task state, Skill definition/binding, and Prompt version existed
as separate contracts without one restart-proof configuration composition.

After:

`WorkbenchCommonImageAnalysisConfiguration` registers the minimal generic
`common.image-analysis@1.0.0` definition, configures an AssetVersion input and
versioned Prompt override on Task Rich Node, and reconstructs the exact refs
and versions from persisted Task state after a new Task instance is created.

Duplicate owner removed:

The proof owns no execution, model/provider selection, WholeHouse behavior, or
Canvas persistence. It uses the injected Skill registry and existing Task Rich
Node persistence; embedded configuration remains the only demonstrated path.

## Next Recommended Card

`R7-01`

Do not execute the next card in the same Agent run.

## Implementation Evidence

Focused `tests/test_common_image_analysis_proof.py` coverage passes (2 tests),
including definition registration, AssetVersion/Prompt/SkillBinding exact refs,
restart reload equality, and absence of execution/WholeHouse ownership.
`./scripts/agent-verify.sh` passes with 768 tests, 136 Python AST files, 133
JavaScript files, 4 architecture guards, and clean diff check. Independent
Review PASS on 2026-09-11; R7-01 was not started.

## Independent Review

PASS — 2026-09-11. The configuration proof survives Task restart with exact
AssetVersion, SkillBinding, and Prompt references, without execution or
WholeHouse ownership.
