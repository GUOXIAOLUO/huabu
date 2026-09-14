# CARD R9-12 — Result to Artifact

- Round: R9
- Priority: P0
- Status: DONE — independent Review PASS (2026-09-14)
- Depends on: R9-11

## Goal

Explicitly promote selected run result into a formal ArtifactVersion.

## Before Owner

tray-only result

## After Owner

Artifact materialization action

## In Scope

- Create/new version with lineage.
- Support title/type metadata.
- Link Task/Run/result.

## Out of Scope

- No automatic Approved/Frozen.

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

- [x] Formal output is explicit and traceable.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: selected execution results had no Artifact promotion application path;
Asset materialization was the only result-to-resource path.

After: `ResultArtifactMaterializationService` verifies the selected result and
run/attempt relationship, then creates an Artifact and first ArtifactVersion
with execution lineage through the canonical ArtifactService.

Duplicate owner removed: none; the result promotion seam delegates persistence
to ArtifactService/ArtifactRepository and does not create a second Artifact store.

## Developer Verification

- Added `POST /api/v1/execution-runs/{run_id}/artifacts` for explicit promotion
  of one selected result.
- The application service preserves Task, run, attempt, input, Prompt, Model and Skill
  lineage, supports title/type metadata, and rejects unselected or cross-run
  results before writing.
- Artifact and first ArtifactVersion creation use one canonical SQLite
  transaction.
- Focused suite: `tests/test_result_artifact_materialization.py` plus Artifact
  domain/version/reference and result-asset suites — **42 tests PASS**.
- Full `./scripts/agent-verify.sh`: **PASS — 1306 tests**, 268 Python AST files,
  152 JavaScript files, 4 architecture guards, and clean `git diff --check`.

## 下一张推荐任务卡

`R9-13`

Do not execute the next card in the same Agent run.
