# CARD R4-40 — Retire R4 Feature Flags

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-09
- Completed: 2026-09-09
- Depends on: R4-39

## Goal

Remove R4 migration flags that no longer represent real runtime choices.

## Before Owner

Six R4 query flags selected rollback branches in the Canvas page and
performance harness.

## After Owner

One stable Unified Canvas runtime path.

## In Scope

- Inventory R4 flags against actual code.
- Delete dead branches and tests that only preserve completed migration paths.
- Keep only flags with explicit post-R4 purpose.

## Out of Scope

- Unrelated feature configuration remains unchanged.

## Definition of Done

- [x] No flag can re-enable Classic/Smart product runtime.

## Final Ownership Evidence

The six flags (`unified_canvas`, `node_shell`, `media_renderer`,
`legacy_renderer`, `semantic_zoom`, `screen_space_controls`) no longer appear
in Canvas runtime decisions or performance-harness forwarding. Native Canvas
scripts use the stable Unified path; compatibility modules remain bounded
adapters and are not URL-selectable product modes.

Focused flag-retirement tests passed (9). Full `./scripts/agent-verify.sh`
passed with 633 tests, 81 Python AST files, 111 JavaScript files, 4
architecture guards, and a clean diff check. R4-41 was not started.

## Next Recommended Card

`R4-41`

Do not execute the next card in the same Agent run.
