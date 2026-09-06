# Run Current Task (Codex)

You are executing exactly one task card in the Xinhuabu AI Workbench repository.
This prompt is self-contained; do not rely on chat memory.

## Read first, in this order

1. `AGENTS.md`
2. `.agent/AGENT_CONTRACT.md`
3. `docs/status/CURRENT_EXECUTION_STATUS.md`
4. `AGENT_NEXT_TASK.md`
5. The task card that `AGENT_NEXT_TASK.md` points to.

## Execute

- Complete exactly that one card, including its In Scope, Execution Pattern,
  Focused Tests, and Regression sections.
- Never start another card or a later Round. Planning edits do not authorize
  future Round implementation.
- Do not `git reset`/`checkout`/`clean` unknown changes; do not commit, push,
  or switch tasks. Local-first boundary per the contract.
- Do not touch files outside the card's scope.

## Verify

- Run the card's focused tests.
- Run the regression gate `./scripts/agent-verify.sh`; it must pass before the
  card may be marked `DONE`.
- Classify every result as existing vs new.

## Bookkeeping, then stop

1. Update `docs/status/CURRENT_EXECUTION_STATUS.md` with verified evidence.
2. Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only if ownership changed.
3. Set the card status to `DONE` only when its DoD is actually satisfied.
4. Write the recommended next card into `AGENT_NEXT_TASK.md` without executing it.
5. Stop after this one card.

## Final report must state

Before Owner, After Owner, duplicate owner removed, files changed, test results,
remaining issues, recommended next card.
