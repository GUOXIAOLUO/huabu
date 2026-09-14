# Xinhuabu Task Cards

## Directories

```text
docs/tasks/
├─ backlog/     # future cards, and the single ACTIVE card while it is in flight
├─ done/        # completed cards, after independent Review PASS
├─ reference/   # requirements / acceptance references — not task-selection authority
└─ templates/
```

`docs/tasks/active/` no longer exists. Cards were activated into it during the R4
era; since R8-22 / R9-01 the active card has stayed in `backlog/` and been marked
by its own `Status:` header, with `AGENT_NEXT_TASK.md` pointing at the card's real
path. Every card archived since then carries that `Status:`-header convention.

The empty `active/` directory and the matching `scripts/agent-activate-task.sh`
were both retired on 2026-09-13 — the script had implemented the old
`backlog/ → active/` move and rewrote a `- Task ID:` line that
`AGENT_NEXT_TASK.md` no longer has (it uses `- Active Task:`). Activation is now a
manual bookkeeping edit; see *Moving Cards* below.

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

The card stays in `backlog/` for the whole of `ACTIVE` … `REVIEWED`; only its
`Status:` header changes. It moves to `done/` at `DONE`.

## Round Gate

A later Round remains blocked until the current Round's formal Gate passes.

## Moving Cards

After independent Review PASS:

1. move the completed card from `backlog/` to `done/`, and set its `Status:` to
   `DONE — independent Review PASS; archived <date>`;
2. activate exactly one dependency-satisfied card by setting its `Status:` to
   `ACTIVE — dependency satisfied; implementation not started`; it stays in
   `backlog/`;
3. update `AGENT_NEXT_TASK.md` (Active Task, Task Card, Status, Depends on) and
   `docs/tasks/TASK_INDEX.md`, and extend the archived-through range;
4. do not start the newly activated card in the same Agent run.

`tests/test_current_fact_documentation.py` pins the pointer's `Status:` line
against the active card's own, and pins the index rows, so this bookkeeping fails
the suite instead of drifting silently.

## UX Video Replica Wave

The UI replica work is represented by normal task cards `UX-01` through `UX-15`.
They are not a parallel planning system.

Rules:

1. `AGENT_NEXT_TASK.md` remains the only task-selection authority.
2. `UX-01` may be activated only after `R10-08` is DONE and the R10 Round gate / independent review is PASS.
3. Exactly one UX card may be ACTIVE at a time.
4. UI reference documents under `docs/design/video-replica/` are requirements and acceptance evidence, not task-selection authority.
5. `R11-01` remains blocked until `UX-15` is DONE and independently reviewed PASS.
6. Do not activate a UX card merely because it exists in `backlog/`.
7. Each UX card follows the same lifecycle as every other task card: BACKLOG → READY → ACTIVE → IMPLEMENTED → REVIEWED → DONE.
8. After a UX card passes review, move it according to the normal task-card process and activate only the next authorized card in a separate Agent run.

The UX cards must preserve the existing architecture:

- One Unified Canvas.
- No greenfield / second Canvas runtime.
- Preserve Node / Skill / Model / ProviderConnection / Executor separation.
- Reuse canonical creation, graph mutation, execution, result, collection, asset and persistence services.
- Do not move WholeHouse business logic into Core.
- Do not expand `classic-*` compatibility modules as the long-term implementation path.
