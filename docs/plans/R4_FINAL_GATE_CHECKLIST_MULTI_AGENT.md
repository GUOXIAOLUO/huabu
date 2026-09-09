# R4 Final Gate Checklist — Multi-Agent Integration

Only the Integration Owner evaluates this checklist against MERGED code.

Unmerged Agent branches do not count as completed architecture.

If any required item lacks evidence:

```text
R4: NOT PASS
```

---

## A0. Local-first / backup boundary

```text
[ ] all normal development evidence comes from local integration branch/worktree
[ ] no Agent pulled/fetched remote state as development authority
[ ] no PR is required for local R4 completion
[ ] any GitHub push/upload occurred only after explicit user backup instruction
[ ] any authorized backup was performed by one designated owner
[ ] local integration branch/worktree remained the implementation source of truth after backup
```

## A. Integration state

```text
[ ] all required task branches merged
[ ] no unresolved semantic ownership locks
[ ] no duplicate implementation kept after conflict resolution
[ ] integration branch tests pass
[ ] task board reflects merged reality
```

## B. Unified product architecture

```text
[ ] one user-visible Canvas entry
[ ] one actual Canvas product runtime
[ ] no permanent Classic product mode
[ ] no permanent Smart product mode
[ ] no hidden dual runtime initialization
```

## C. Persistence

```text
[ ] SQLite normal authority
[ ] one persistence coordination owner
[ ] logical revision verified
[ ] expected revision CAS verified
[ ] stale conflict verified
[ ] restart verified
[ ] rollback verified
[ ] no normal Legacy write mode under SQLite authority
```

## D. Rendering

```text
[ ] one rendering owner
[ ] normal mount unified
[ ] normal update unified
[ ] normal unmount unified
[ ] RendererRegistry canonical
[ ] Legacy renderer compatibility bounded
```

## E. Interaction

```text
[x] one interaction owner
[x] pan/zoom
[x] selection/multi-selection
[x] drag/resize
[x] keyboard
[x] viewport
[x] connection lifecycle
[x] no duplicate global listeners
```

## F. Creation

```text
[ ] one normal creation owner
[ ] context menu
[ ] toolbar/command
[ ] file drop
[ ] paste
[ ] workflow import
[ ] Smart Composer migrated
[ ] canonical creation boundary used
```

## G. Graph / Group

```text
[x] group membership unified
[x] group move unified
[x] graph geometry unified
[x] normal-connect side effects characterized
[x] no GraphMutationService + raw Canvas double write
```

## H. Media

```text
[x] one media lifecycle owner
[x] image/video/audio where supported
[x] preview/fallback/original
[x] high-res switching
[x] playback preservation
[x] no duplicate player binding
[x] no media reload storm
```

## I. Legacy readability

```text
[ ] New Canvas readable
[ ] Legacy Classic readable
[ ] Legacy Smart readable
[ ] all use Unified Runtime
```

## J. Clipboard / Workflow

```text
[x] clipboard/subgraph parity
[x] workflow import/export parity
[x] reload parity
```

## K. Performance

```text
[x] 100-node acceptance
[x] 300-node acceptance
[x] DOM duplication inspected
[x] listener duplication inspected
[x] duplicate polling/timers/observers inspected
[x] memory growth inspected
[x] latency acceptable
```

## L. Runtime removal

```text
[ ] Smart product runtime removed
[ ] Classic duplicate runtime removed
[ ] Smart normal routing removed
[ ] obsolete handoff removed
[ ] duplicate page/CSS removed where Gate permits
[ ] obsolete R4 flags removed
```

## M. Architecture guards

```text
[ ] no WholeHouse branches in Core
[ ] no provider-specific Canvas branches
[ ] no Codex protocol DTO imports in Core
[ ] no new Workbench systems in Legacy monoliths
[ ] no runtime Git hosting dependency
[ ] no duplicate product runtime initialization
```

## N. Documentation truth

```text
[ ] R4_OWNERSHIP_MATRIX matches merged source
[ ] CURRENT_EXECUTION_STATUS matches merged verified truth
[ ] rollback evidence recorded
[ ] acceptance evidence recorded
[ ] no future Round marked current
```

## Integration Owner evaluation — 2026-09-09

Evaluation target: local `main`, merged cutover range `a013582...bf4383a`.
The worktree was clean and `./scripts/agent-verify.sh` passed (637 tests,
81 Python AST files, 112 JavaScript files and 4 architecture guards).

| Gate group | Decision | Merged evidence or concrete gap |
|---|---|---|
| A | PASS | Local `main` contains the R4 integration commits and no remote was used as task authority. |
| B–D | PASS | The Classic runtime file and its page reference are gone; entry, runtime-removal, persistence and render-lifecycle tests pass. |
| E | PASS | `r4-41-merged-behavioral-acceptance-2026-09-09.md` records the 27-test behavioral run for selection, drag/resize, viewport, keyboard, connection lifecycle, and listener idempotence; the browser harness separately verifies live pan/zoom/minimap. |
| F | PASS | The canonical creation client/controller covers normal creation; `legacy-canvas-mutation.js` is an explicit compatibility seam. |
| G | PASS | The behavioral record covers move membership transition, group input handoff, veto/no-op paths, atomically persisted normal/Smart graph connects, and persisted/reloaded membership under one revision. |
| H | PASS | The behavioral record covers media state projection, native playback preservation across remount, renderer state signatures, and RenderSweep live-media reuse; the resource audit covers idempotent initialization. |
| I | PASS | Entry tests cover Classic and historical Smart records through `canvas.html`. |
| J | PASS | The behavioral record covers clipboard persistence, workflow import/export projection, and reopened SQLite authority/routing restart parity. |
| K | PASS | `r4-41-runtime-audit-2026-09-09.md` records disposable live-browser 100/300-node acceptance, ten actual renders each, DOM and Chromium heap zero deltas, interaction latencies, and listener/timer/observer inspection. |
| L–M | PASS | Runtime-removal, flag-retirement and architecture-guard suites pass; no R5 implementation was introduced. |
| N | PASS | The acceptance and resource records now state the verified local evidence and its browser/metric limits; status remains R4 until the task card is formally finalized. |

# Final decision

```text
R4: PASS
```

This verdict applies to the local merged R4-41 worktree after the focused
behavioral run, disposable-browser acceptance, and final regression verifier.
It does not authorize implementation of R5 in this card.
