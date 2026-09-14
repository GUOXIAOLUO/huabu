# Full Backlog Usage

This directory contains detailed executable cards through R17.

## Important

Future cards are intentionally detailed but are **not frozen specifications**.

At each Round boundary:

1. read the newly verified `CURRENT_EXECUTION_STATUS.md`;
2. review the next Round's cards against the code that actually exists;
3. amend cards if discoveries from earlier rounds changed the safest implementation;
4. activate exactly one card.

Do not treat an old backlog card as more authoritative than verified repository reality.

## Why keep future cards anyway?

They preserve architecture intent and decomposition:

- one ownership move per card;
- explicit dependencies;
- explicit out-of-scope;
- testable DoD;
- no accidental WholeHouse/Core coupling;
- no automatic cross-Round implementation.

## Activation

Activation is a **manual bookkeeping edit**. There is no activation script;
`scripts/agent-activate-task.sh` was retired on 2026-09-13.

After the previous card has passed independent Review and been moved to `done/`,
activate exactly one dependency-satisfied card by editing, in the same change:

1. the card's own `Status:` header →
   `ACTIVE — dependency satisfied; implementation not started`
   (the card **stays in `backlog/`**);
2. `AGENT_NEXT_TASK.md` — `Active Task`, `Task Card`, `Status`, `Depends on`, and
   the archived-through range;
3. `docs/tasks/TASK_INDEX.md` — the card's row.

`docs/tasks/README.md` → *Moving Cards* is the authoritative statement of this
flow, and `tests/test_current_fact_documentation.py` pins the pointer and the
index rows so the three files cannot drift apart silently.

Activating a card only records *which* card is next.
It does **not** authorize implementation, and does **not** run Codex or ZCode.
