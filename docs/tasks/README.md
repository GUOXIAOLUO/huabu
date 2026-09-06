# Xinhuabu Task Cards

## Directories

```text
docs/tasks/
├─ active/      # AGENT_NEXT_TASK points here
├─ backlog/     # ready/future task cards
├─ done/        # completed cards after review
└─ templates/
```

## Rule

Only `AGENT_NEXT_TASK.md` selects what an Agent may execute.

The existence of a backlog card does not authorize its implementation.

## Lifecycle

```text
BACKLOG
→ READY
→ ACTIVE
→ IMPLEMENTED
→ REVIEWED
→ DONE
```

A card should not move to DONE merely because code was written.
Its Definition of Done must be supported by tests/evidence.

## Round Gate

A later Round remains blocked until the current Round's formal Gate passes.

## Moving Cards

After review:

1. move completed card from `active/` to `done/`;
2. move exactly one next card from `backlog/` to `active/`;
3. update `AGENT_NEXT_TASK.md`;
4. do not start it in the same Agent run.
