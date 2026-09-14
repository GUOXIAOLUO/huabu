# UI Replica Wave Activation Guide

This guide adapts the video-reference work to the repository's existing task-card lifecycle.

## Do not activate now unless the gate is satisfied

Current repository work continues through the active R9/R10 cards. The presence of UX cards in `docs/tasks/backlog/` does not authorize UI work.

UX entry gate:

- `R10-08` is DONE.
- R10 independent Review / round gate is PASS.
- Working tree and current-fact documents are reconciled.
- `AGENT_NEXT_TASK.md` is ready to point to exactly one new card.

Then activate only `UX-01` using the same normal task-card procedure used for R cards.

## During the UX wave

For each card:

1. `AGENT_NEXT_TASK.md` points to exactly one UX card.
2. Agent reads current facts and that card.
3. Agent characterizes, implements, tests, records evidence, then stops.
4. Independent reviewer reviews while the card remains the current card according to the repository's then-current lifecycle.
5. Only after PASS is the card archived and the next UX card activated.

## Exit gate

`R11-01` remains blocked until `UX-15` passes independent Review.

## Important

Do not replace `AGENT_NEXT_TASK.md` from this pack. It must always represent the live repository state.
