# CARD R9-09 — ArtifactVersion and Lineage

- Round: R9
- Priority: P0
- Status: DONE — independent Review PASS (2026-09-14); archived 2026-09-14
- Depends on: R9-08

## Goal

Create immutable ArtifactVersion with execution/input lineage.

## Before Owner

mutable outputs

## After Owner

ArtifactVersion

## In Scope

- Define immutable version payload/content refs.
- Attach source run/attempt/input/prompt/model/skill lineage.
- Add repository/service/API.

## Out of Scope

- Do not overwrite prior versions.

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

- [x] Every formal result version has lineage.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: Artifact existed only as an identity; no version content or lineage record existed.

After: `ArtifactVersion` is immutable, carries content refs and required run/attempt/input/prompt/model/skill lineage, and is persisted/read through authorized service/API boundaries.

Duplicate owner removed: mutable output version ownership was not present; ArtifactVersion is now the sole version record while Artifact remains identity-only.

## Next Recommended Card

`R9-10`

Do not execute the next card in the same Agent run.

## Developer Verification

- Focused suites: `tests/test_artifact_version.py`,
  `tests/test_artifact_domain.py`, and
  `tests/test_current_fact_documentation.py` — **33 tests PASS**.
- `./scripts/agent-verify.sh`: **PASS — 1289 tests**, Python AST, JavaScript
  syntax, architecture guards, and `git diff --check` all PASS.
- ArtifactVersion persistence is append-only and authorized through the
  repository, service, and API boundaries.

## Independent Review

- PASS — current Active Task implementation and tests satisfy the card DoD,
  architecture constraints, and Ownership requirements.
