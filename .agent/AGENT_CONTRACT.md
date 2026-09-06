# Agent Contract

Process contract for every coding agent (Codex, ZCode/GLM, or other) executing
work in this repository. It governs **how** agents run. **What** the product and
architecture allow is governed by `AGENTS.md`, which always remains the highest
rule. If this contract ever appears to conflict with `AGENTS.md`, `AGENTS.md`
wins.

## 1. Authority reading order

Before any implementation or behavior change, read in this order:

1. `AGENTS.md` — hard architecture constraints;
2. `.agent/AGENT_CONTRACT.md` — this contract;
3. `docs/status/CURRENT_EXECUTION_STATUS.md` — the only authority for the
   currently authorized Round and verified state;
4. `AGENT_NEXT_TASK.md` — the selector for the one active task card;
5. The task card it points to (normally under `docs/tasks/active/` or
   `docs/tasks/backlog/`).

Architecture documents (`CURRENT_ARCHITECTURE.md`, `TARGET_ARCHITECTURE.md`,
`MIGRATION_PLAN.md`, `IMPLEMENTATION_PLAN.md`) are read as required by the card.
No other chat history, memory, or external context selects work.

## 2. Local-first execution boundary

- Remote operations (push, backup, repository sync) are disabled by default.
  GitHub backup happens only on an explicit user request.
- Never `git reset`, `git checkout`, `git clean`, or otherwise discard unknown
  worktree changes.
- Never `git commit`, `git push`, or rebase unless the user explicitly asks.
- Never switch to or activate the next task by yourself.
- Do not modify, rewrite, or "clean up" files that are outside the active
  card's scope, including unrelated formatting.

## 3. One card per run

- Execute **exactly one** task card: the card `AGENT_NEXT_TASK.md` points to
  while it is `READY`.
- Only `docs/status/CURRENT_EXECUTION_STATUS.md` authorizes the active Round.
  A card from a later Round must never be executed, even if it exists under
  `docs/tasks/backlog/`.
- Partial completion is not permission to skip a Gate. If the card's DoD is not
  satisfied, the card is not `DONE`.

## 4. Execution loop

Follow the card's Execution Pattern, which is always some form of:

```text
characterize
-> focused test
-> establish seam
-> implement/migrate
-> verify
-> remove duplicate ownership
```

Behavioral tests are preferred over source-string checks: do not rely only on
string assertions when runtime behavior can be tested.

## 5. Ownership evidence

Every card must be able to answer:

- Before Owner (who owned the responsibility before);
- After Owner (who owns it after);
- duplicate/old owner removed, and new owner established;
- what the tests prove.

R4 progress is measured as ownership movement, not helper count:

```text
Classic Runtime Ownership down
Smart Runtime Ownership down
Unified Runtime Ownership up
```

## 6. Verification

- Run the card's focused tests.
- Run the repository regression gate:

```bash
./scripts/agent-verify.sh
```

- The gate must pass before a card may be marked `DONE`.
- Classify results as existing vs new: a failure caused by the environment or
  by pre-existing committed state is reported as such, never silently fixed by
  discarding changes.

## 7. Completion bookkeeping

After implementation/verification, and only after the DoD is actually satisfied:

1. update `docs/status/CURRENT_EXECUTION_STATUS.md` with verified evidence
   (branch, HEAD, dirty state, test counts, dated narrative entry);
2. update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when ownership changed;
3. set the card's status to `DONE` in the card file;
4. write the recommended next card into `AGENT_NEXT_TASK.md` (point at the
   backlog card path; do not execute it);
5. report and **stop**.

If the card is blocked instead, set its status to `BLOCKED`, record the reason
in the card and in `AGENT_NEXT_TASK.md`, and stop without improvising scope.

## 8. Final report format

The final message to the user states:

- Before Owner / After Owner / duplicate owner removed;
- files changed;
- test results (focused + regression, with classification);
- remaining issues;
- recommended next card (not executed).

## 9. Review discipline

A second agent session may review the completed card read-only via
`.agent/prompts/review-current-task.md`. Reviewers verify the one-card boundary,
`AGENTS.md` constraints, ownership claims, and that tests prove behavior; they
do not modify code and do not execute the next card. Implementation and review
alternate between agents (for example ZCode implements, Codex reviews); two
agents must not write the same worktree at the same time.
