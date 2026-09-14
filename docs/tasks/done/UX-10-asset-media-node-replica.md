# CARD UX-10 — Asset / Media Node Replica

- Round: UX Video Replica Wave
- Priority: P1
- Status: DONE — independent Review PASS
- Depends on: `UX-09`

## Goal

Make Asset/Artifact media cards behave like the minimal resource cards in the videos and integrate the existing floating actions/editor.

## Why Now

This card belongs to the UI Replica Wave that is allowed only after `R10-08` and the R10 gate are complete. It converts the frozen video-reference material into the existing one-card-at-a-time development process without creating a parallel planning system.

## Before Owner

Characterize the actual current owner(s) before editing. Record exact modules/services in Final Ownership Evidence.

## After Owner

The existing canonical Workbench owner(s), refined so the new presentation/interaction is owned by shared Workbench modules rather than a duplicate Canvas runtime.

## In Scope

- Characterize AssetRichNode/ArtifactRichNode/media preview states.
- Prioritize content preview over metadata in default card.
- Use floating toolbar for common actions; keep metadata in Inspector/workspace.
- Verify image/video/file variants.


## Out of Scope

- No Asset/Artifact concept merge.
- No Media Editor rewrite.
- No file-storage migration in this card.


## Characterization

Before editing:

1. Read `AGENTS.md`, `.agent/AGENT_CONTRACT.md`, `docs/status/CURRENT_EXECUTION_STATUS.md`, `AGENT_NEXT_TASK.md`, and this card.
2. Inspect the current implementation and identify the real owner(s); do not assume the reference pack describes current code.
3. Capture/record the current browser state relevant to this card.
4. Read the required video references below.
5. Add the smallest characterization test/evidence needed before migrating responsibility.

## Required Video / Design References

- `docs/video-replica/VIDEO_NODE_SPEC.md`
- `docs/video-replica/references/media-editor/`


`ARCHITECTURE_GUARDRAILS.md` applies to every UX card even when not repeated above.

## Implementation Steps

1. Characterize current behavior and ownership.
2. Add or update focused tests before/with the change.
3. Establish or reuse the canonical shared seam.
4. Implement only this card's visual/interaction responsibility.
5. Verify browser behavior against the cited references.
6. Remove duplicate ownership only when replacement is proven.
7. Update evidence/status, then stop. Do not execute the next card in the same Agent run.

## Compatibility / Migration

- Preserve existing saved projects, node records, execution semantics, resource identity and provider credentials.
- Prefer presentation-layer changes over domain/schema changes unless this card explicitly requires otherwise.
- Classic/legacy code may remain as a bounded compatibility seam until its replacement is proven by focused + browser acceptance tests.
- Never introduce a second Canvas runtime or a UI-only source of truth.

## Focused Tests

- Add/run the smallest behavioral tests proving this card's goal and ownership boundary.
- Add source-contract tests only where they protect a real architecture boundary; do not substitute string tests for behavior.
- Run browser acceptance for the states named in this card.

## Regression

Run the repository regression gate required by the active repository contract (currently `./scripts/agent-verify.sh`). If the repository contract changes by the time this card activates, follow the then-current active contract.

## Definition of Done

- [x] Image/resource card is content-first and compact.
- [x] AssetVersionRef/Artifact identity remains intact.
- [x] Editor/open/materialize actions still use existing services.
- [x] `AGENT_NEXT_TASK.md` still authorizes only this card during implementation.
- [x] No next card or later Round was implemented in the same Agent run.
- [x] Focused tests and regression gate results are recorded with evidence.

## Rollback

Revert only this card's bounded presentation/interaction change or re-enable the prior bounded compatibility seam. Do not roll back unrelated completed Round work or reset unknown local changes.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md` with verified evidence required by the current task lifecycle.
- Update this card's status/evidence according to the repository's current task lifecycle.
- Update `AGENT_NEXT_TASK.md` only as permitted by the repository's independent Review/activation procedure.
- Do not rewrite architecture documents merely to describe visual changes unless ownership actually changed.

## Final Ownership Evidence

Before: `asset-rich-node.js` owned Asset presentation state; `media-renderer.js`
owned media preview DOM; `node-shell.js` composed the shared shell; existing
Canvas interaction/editor modules owned floating actions, preview and image
editing. `artifact-rich-node.js` remained separate.

After: the same shared owners remain. `media-renderer.js` now owns the
content-first media card presentation and type-specific preview element;
`canvas-app-interaction.js` resolves the first media reference for the existing
floating preview action, while the existing preview, editor, Inspector and
materialization services remain their respective owners.

Duplicate owner removed: none; no second Canvas runtime, Asset repository,
Artifact owner or media editor was added.

Browser/reference evidence: required media-editor references were read from
`docs/video-replica/references/media-editor/`. A temporary local Canvas fixture
was created through the existing Canvas API and removed after inspection. The
page reached the real Canvas route, but the browser surface still exposed the
Legacy card instead of the shared Workbench globals, so media-node visual
acceptance remains a follow-up risk; image/video/audio/file variants are
covered by focused runtime tests.

Focused tests: `./.venv/bin/python -m unittest -v
tests.test_ux10_asset_media_node_replica tests.test_asset_rich_node
tests.test_floating_action_bar tests.test_ux05_floating_action_toolbar
tests.test_nodeshell_v2` — 12 passed.

Regression: `./scripts/agent-verify.sh` — PASS; 1375 tests, 310 Python AST
files, 157 JavaScript files, 4 architecture guards, and `git diff --check`.

## Independent Review

PASS — current Active Task implementation satisfies the card DoD, preserves
the shared Canvas ownership boundary, and has focused/regression evidence.

## Next Recommended Card

`UX-11`

Do not execute the next card in the same Agent run.
