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

After the previous card is reviewed and moved out of `active/`:

```bash
./scripts/agent-activate-task.sh R5-01
```

This only activates the card.
It does **not** run Codex or ZCode.
