# CARD R7-12 — Codex Event Normalizer

- Round: R7
- Priority: P0
- Status: DONE — independent Review PASS 2026-09-11
- Depends on: R7-11

## Goal

Normalize Codex protocol events into Workbench-neutral runtime events.

## Before Owner

raw Codex events leaked upward

## After Owner

EventNormalizer

## In Scope

- Map lifecycle/progress/output/error events.
- Preserve raw diagnostic ref when needed.
- Test stable normalized schema.

## Out of Scope

- No Agent UI.

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

- [x] Upper layers can observe events without Codex protocol knowledge.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: `CodexBridge` exposed protocol method names and Codex-specific event
kinds directly through its public event queue.

After: `CodexEventNormalizer` owns the mapping to stable Workbench-neutral
`RuntimeEvent` lifecycle/progress/output/error/approval semantics. The bridge
queue exposes only `RuntimeEvent`; raw protocol methods and payload shapes are
not exposed, with only an explicit diagnostic reference retained when useful
for support.

Duplicate owner removed: protocol-event classification was removed from the
bridge's upper-facing event contract; no Agent UI or Workbench business event
owner was introduced.

Focused evidence: tests cover lifecycle, progress, output, approval, unknown
notification, transport error, terminal EOF, timeout, and queue integration
through the normalized fields, including rejection of raw payload leakage.
Focused tests pass (11); full verification passes with 794 tests, 156 Python
AST files, 134 JavaScript files, 4 architecture guards, and clean diff check.

## Next Recommended Card

`R7-13`

Do not execute the next card in the same Agent run.
