# CARD R9-10 — Artifact Inspector and History

- Round: R9
- Priority: P1
- Status: DONE — independent Review PASS
- Depends on: R9-09

## Goal

Expose artifact versions, provenance and comparison in Inspector/Workspace.

## Before Owner

generic artifact skeleton

## After Owner

versioned Artifact UX

## In Scope

- Show version list/current status/lineage.
- Allow compare/open/materialize actions.

## Out of Scope

- No Approval UI yet.

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

- [x] Version history is inspectable and prior versions remain immutable.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Developer Verification

- Added the canonical Artifact resource surface to the existing Resources page;
  no second Canvas runtime or artifact-specific persistence path was created.
- Artifact list/history reads use the authorized `/api/v1/artifacts` service
  boundary. The Inspector renders current version, immutable history, lineage,
  content references, comparison selection, open, and materialize entry points.
- Focused suites: `tests/test_artifact_inspector.py`,
  `tests/test_artifact_version.py`, `tests/test_artifact_domain.py`, and
  `tests/test_current_fact_documentation.py` — **35 tests PASS**.
- Browser acceptance: real local Resources page switched to `产物` and showed
  the Artifact empty state; no second Canvas runtime was loaded.
- `./scripts/agent-verify.sh`: **PASS — 1291 tests**, Python AST, JavaScript
  syntax, architecture guards, and `git diff --check` all PASS.

### Independent Review Repair

- Comparison now uses the server-named current version as the implicit first
  side, so selecting one comparison version is sufficient to render a pair.
- Materialization now emits an explicit `artifact-materialize-request` handoff
  containing both Artifact and ArtifactVersion ids; it does not mutate Canvas
  state or bypass the formal NodeCreation/GraphMutation boundary.
- The Studio shell forwards that handoff to the existing Canvas iframe, whose
  state boundary queues the explicit request for confirmation through the
  formal Canvas creation entry; no second runtime or direct graph mutation was
  introduced.
- The Canvas creation entry now consumes the queued request through the
  existing `CreationController`, creates the generic execution-result node with
  the ArtifactVersion reference, applies the revision/undo/selection result,
  and clears the pending request only after a successful formal write.
- ArtifactVersion references are now validated by the application boundary for
  project ownership and version identity before NodeCreation; the canonical
  node command also persists a typed `artifact_version` output reference for
  reload-safe inspection.
- Missing Artifact or ArtifactVersion identities are normalized to the
  controlled `artifact_reference_not_found` creation error instead of leaking a
  repository exception as HTTP 500.
- The Canvas API now accepts and maps `initial_output_refs`, so the typed
  ArtifactVersion reference reaches NodeCreation and is not rejected by the
  request contract.

## Final Ownership Evidence

Before: Artifact versions were persisted and readable by API, but no Resources
page surface exposed their history or lineage.

After: the existing Resources page owns Artifact selection and mounts the
Artifact Inspector; `artifact-inspector.js` owns pure presentation and request
shape, while ArtifactService/repository remain the canonical data owners.

Duplicate owner removed: none; Asset Inspector remains Asset-owned and Artifact
Inspector is a separate Artifact presentation boundary.

## Independent Review

- PASS — independent Review completed; archived 2026-09-14.

## Next Recommended Card

`R9-11`

Do not execute the next card in the same Agent run.
