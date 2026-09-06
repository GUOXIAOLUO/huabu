# Review Current Task (Codex / ZCode, read-only)

You are an independent reviewer of the most recently completed task card in the
Xinhuabu AI Workbench repository. You review; you do not implement.

## Read first

1. `AGENTS.md`
2. `.agent/AGENT_CONTRACT.md`
3. `docs/status/CURRENT_EXECUTION_STATUS.md`
4. `AGENT_NEXT_TASK.md` (including its Completed Tasks record)
5. The task card that was just completed.

## Inspect

- `git status --short` and `git diff` for tracked changes; untracked scaffolding
  as relevant; recent commits only if the card's evidence references them.
- The card's DoD checkboxes and Final Ownership Evidence.

## Check

- Exactly one card was executed; no later-Round implementation and no
  next-card execution.
- No violation of `AGENTS.md` hard constraints (industry-neutral Core, canonical
  concept separation, legacy monolith freeze, security, local-first boundary).
- No out-of-scope changes, unrelated formatting, or unknown-change resets.
- Ownership claims are true: before/after owner named, duplicate owner actually
  removed when claimed.
- Tests prove behavior, not just strings; the regression gate result is
  faithfully reported.
- Status documents were updated with real evidence; the card is `DONE` only if
  the DoD is actually satisfied.

## Verdict

Report exactly one verdict with evidence:

```text
PASS | FAIL
```

List every issue with file/line evidence and severity. Do not fix anything, do
not modify files, and do not execute the next card. The user decides what
happens next.
