# CARD R9-11 — Result to Asset

- Round: R9
- Priority: P1
- Status: DONE — independent Review PASS; archived 2026-09-14
- Depends on: R9-10

## Goal

Explicitly save selected run result as an Asset/AssetVersion.

## Before Owner

tray-only result

## After Owner

Asset materialization action

## In Scope

- Create asset identity/version from eligible output.
- Preserve run provenance.
- Return stable ref.

## Out of Scope

- No silent save of all results.

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

- [x] User-selected result becomes reusable Asset.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Developer Verification

- Added the explicit `POST /api/v1/execution-runs/{run_id}/assets` application
  path. It rechecks the selected ResultSelection and run/attempt ownership,
  creates an Asset and first AssetVersion through AssetService, preserves
  execution provenance, and returns the stable AssetVersionRef.
- Unselected results and results from another run are rejected before any Asset
  write; no silent save path was added.
- The Result Selection seam exposes an explicit `Save as asset` action only for
  selected records; the transport adapter posts declared `AssetVersionContent`
  to the R9-11 endpoint, and TaskRichNode exposes the shared selection mount.
- Focused suite: `tests/test_result_selection.py` plus result tray/task and
  result-asset suites — **57 tests PASS**.
- Full `./scripts/agent-verify.sh`: **PASS — 1302 tests**, 265 Python AST
  files, 152 JavaScript files, 4 architecture guards, and clean
  `git diff --check`.

### Independent Review Repair

- Asset creation and first AssetVersion persistence now use one canonical
  SQLite transaction through AssetService/AssetRepository; a failed version
  write cannot leave an empty Asset identity behind.
- The selected-result UI action is wired through a transport-only client and
  requires declared content; no bytes are fabricated and unselected rows have
  no save action.
- Focused regression is **57 tests PASS**; the full gate remains
  **PASS — 1302 tests** with 265 Python AST files, 152 JavaScript files, 4
  architecture guards, and clean `git diff --check`.

## Next Recommended Card

`R9-12`

Do not execute the next card in the same Agent run.
