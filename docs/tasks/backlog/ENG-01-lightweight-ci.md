# CARD ENG-01 — Lightweight CI

- Round: ENG
- Priority: P1
- Status: BACKLOG
- Depends on: R4-20 or later

## Goal

Establish lightweight CI matching current repository capabilities.

## Before Owner

manual local verification

## After Owner

repeatable CI checks

## In Scope

- Run unit tests, Python AST parse, JS syntax, architecture guards, git diff --check and secret scan.
- Keep configuration lightweight.

## Out of Scope

- No large toolchain migration during R4.

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

- [ ] CI runs on PR/branch and matches local agent-verify essentials.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`ENG-02`

Do not execute the next card in the same Agent run.
