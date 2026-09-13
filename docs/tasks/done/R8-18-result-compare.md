# CARD R8-18 — Result Compare

- Round: R8
- Priority: P1
- Status: DONE — independent Review PASS; archived 2026-09-12
- Depends on: R8-17 (DONE, independent Review PASS)

## Goal

Compare multiple candidate outputs without materializing them.

## Before Owner

manual Canvas comparison

## After Owner

Result compare workspace

## In Scope

- Support multi-select compare.
- Provide side-by-side metadata/preview.
- Preserve selection.

## Out of Scope

- No domain-specific scoring.

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

- [x] Users can compare candidates while they remain run results.

Evidence: `static/js/workbench/canvas/result-compare-runtime.js` exposes
`WorkbenchCanvasResultCompare` with `candidateFrom`, `candidatesFrom` and
`create`. `candidatesFrom(cards, items)` joins the tray's staged cards to their
staged items on `item_id`, so every candidate carries the run-result linkage
(`run_id`, `attempt_id`, `output_name`, `ordinal`) rather than anything derived
from a Canvas node. A bounded ordered selection (min 2, max 4) renders one column
per selected candidate, side by side, each with its metadata and its preview. The
preview body is delegated to `WorkbenchCanvasResultPreview` rather than
re-implemented, and the workspace exposes no promotion, materialization or node
creation entry point. An end-to-end probe fed with the real executor output
vocabulary (DirectModel raw text, RunningHub `{kind,url,filename}`, ComfyUI
`{kind,filename,subfolder,item_type}` with no url, MCP
`{kind,uri,mime_type}`) compared three candidates whose staged tray state stayed
byte-identical, whose `materialized` flags all stayed `false`, and whose Canvas
graph object was byte-identical.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

Manual, per-output, pairwise Canvas comparison: the only comparison in the
codebase lived in the Classic output surface, inside `openOutputLightbox` in
`static/js/workbench/canvas/canvas-app-output-ui.js` (`outputCompareUrlFor` →
`media-tools.outputCompareUrl`), keyed by a node's `imageComparisons`. It is
reachable only after an output already exists on a Canvas node, so a user could
not compare anything while it was still a run result. `grep -rl
"ResultCompare\|result-compare\|resultCompare" static/` returned nothing, and the
two predecessor seams offered no comparison: R8-16 exposes only `{KINDS,
PREVIEWABLE, kindOf, urlOf, createSession, ingest, cardFor, cards, summaryOf,
create}` and R8-17 exposes no comparison capability.

After:

`static/js/workbench/canvas/result-compare-runtime.js` owns the comparison of
staged run results: the bounded ordered selection, the side-by-side column
metadata, and the layout. It owns no preview rendering (delegated to
`WorkbenchCanvasResultPreview`), no classification (the caller's declared kind is
rendered as given), no transport, and no persistence. It is mounted through
`WorkbenchTaskRichNode.mountResultCompare`, which `node-shell.js` wires to a
`data-result-compare-host` section created only when `settings.resultCompareOptions`
is present, and destroyed in the shell's `destroy()`. `static/canvas.html`
registers it after the preview runtime and ahead of the app bootstrap.

Duplicate owner removed:

None was removed, because none existed: the Classic per-output slider is a
different concept (an existing node output, pairwise, unscored but node-bound)
and is untouched by this card, and no module other than
`task-rich-node.js` consumes `WorkbenchCanvasResultCompare`. The comparison
therefore gained a single owner rather than splitting one.

## Developer Verification

Focused suite: `tests/test_result_compare.py`, 14 tests, all passing. It drives
the seam in a Node `vm` sandbox and covers order-preserving bounded multi-select,
toggling off and unknown candidates, the `empty → incomplete → ready` state
transitions, selection preserved across `setCandidates` (including the reported
`omitted` ids), selection surviving a re-render and further toggles, the
side-by-side column metadata plus preview, the mounted workspace, the `item_id`
join, the end-to-end tray → compare path, the seam's forbidden-vocabulary scans,
the page registration order, and both host-integration paths.

Full gate: `./scripts/agent-verify.sh` → **AGENT VERIFY: PASS** with 994 unit
tests (980 before this card), 206 Python files AST-parsed, 138 JavaScript files
syntax-checked, 4 architecture guards, and a clean `git diff --check`.

Mutation testing: 16 mutations were run against the guarded branches this card's
DoD depends on — the capacity guard, selection order, the unknown-candidate
guard, `setCandidates` preservation and its `omitted` reporting, the
`incomplete`/`ready` threshold, the `item_id` join, preview delegation, the
column's retained `preview_url`, the absence of scoring, the absence of a
promotion entry point, the empty-state copy, the missing-module error, the
shell's `destroy()` call, the page registration, and re-classification by
extension — of which **all 16 were caught** and all four touched sources restored
byte-identical. The `item_id`-join mutation is the sharpest one: replacing the
id-keyed lookup with a positional one makes an item-less card borrow its
neighbour's value, and the suite rejects it.

Recorded hashes at verification time: `result-compare-runtime.js` sha256
`27b32f5f50fb308dfa5bb3286f6852db19b84bab1764f32246fe43e91142dd22`,
`task-rich-node.js` `0f2935188f8fdff9bf0738ecae5a82ae189d520ba72cabf9b858c1b1532c2007`,
`node-shell.js` `bc331341a82b6fea0e6264a909b2a8fcf871fea765ed36d83817eec2d4a85521`,
`static/canvas.html` `d3ddc0dc0d23eadd2d82bbca8c015ed56843a29015432dab1c58ba8af14eb972`.

Two defects were found and fixed during implementation, both before the suite was
first run green: `columnFor` omitted `preview_url` even though `columnHtml` reads
`column.preview_url`, and `render()` called `comparison()` twice per render
instead of once. Two test-side defects were found and fixed: rendered columns
were counted by the bare substring `result-compare__column`, which the wrapper
class `workbench-result-compare__columns` also contains and which therefore
reported one column too many, and the node-shell vocabulary scan tripped on the
shell's own `createNodeShell` factory, which contains the forbidden `createNode`
marker as a substring — the scan now scrubs that one known-legitimate token and a
companion assertion proves the scrub is narrow enough that a real
`createNodeFromResult` would still be caught.

Two design decisions worth recording. First, a card whose staged item is absent
still yields a candidate rather than being dropped: its metadata and reference are
real, and silently dropping it would hide a candidate, so `null` is reserved for a
card with no identity at all and the join is pinned by a test proving no
cross-contamination between neighbours. Second, the selection is an ordered list
rather than a set, because comparison here is deliberately unscored — the user's
selection order is the only order the workspace has, and the Out of Scope clause
("No domain-specific scoring") is enforced by a source scan for score, rank,
rating and weight vocabulary.

## Independent Review

Verdict: **PASS**.

Nothing in the developer's verification was taken on trust. The focused suite was
re-run, the full gate was re-run, the page order, ownership and change set were
re-derived from the tree, and two fresh artefacts were built specifically for this
review: a mutation set of 15 targets the developer had *not* used, and an
end-to-end DoD probe fed with a different executor-output mix from the
developer's.

Change set, re-derived from mtimes rather than from the card's claim: R8-18's
window is 19:45–20:02 and contains exactly `result-compare-runtime.js` (new),
`task-rich-node.js`, `node-shell.js`, `static/canvas.html`, `test_result_compare.py`
and the bookkeeping documents. `find workbench main.py -newermt "2026-09-12 19:40"`
returns nothing, so no backend or Core module is in this card's change set and the
industry-neutral Core constraint is untouched; the card touches no Model,
ProviderConnection, ExecutionProfile or Executor, so §13's no-silent-substitution
rule and §15's Codex boundary are not engaged; there is no `fetch(`,
`XMLHttpRequest`, `localStorage` or `sessionStorage` in the module, so §29's
no-Git-hosting-fetch rule is not engaged. The two R8-17 seams that also show a
19:43–19:44 mtime are byte-identical to the hashes recorded when R8-17 was
archived (`result-preview-runtime.js` sha256 `a97239d3…`,
`result-tray-runtime.js` sha256 `4193fc8c…`), so they are R8-17's own work and were
not silently altered by this card.

Focused suite: 14 tests, matching the 14 `def test_` methods in the file, all
passing. Regression check: R8-16 + R8-17 + R8-18 run together green (36 tests).
Full gate re-run: **AGENT VERIFY: PASS** with 994 unit tests, 206 Python AST files,
138 JavaScript files, 4 architecture guards and a clean `git diff --check`,
confirmed against the project virtualenv the gate itself uses. One methodological
note for future runs: invoking `unittest discover` with an interpreter other than
`.venv/bin/python` reports spurious import errors (69 of them here, from missing
`pydantic`), so the gate's own interpreter is the only meaningful baseline.

Independent mutation testing: 15 fresh targets, deliberately disjoint from the
developer's 16 — `escapeHtml` as a pass-through, `select()`'s de-duplication,
capacity and unknown-id guards, `toggle()`'s unknown-candidate flag, `mount()`'s
host guard, `destroy()` as a no-op, the column's registry-vs-bare-reference render
branch, the two bounds constants, `stateOf(0)`, the candidate value clone, the
schema string, `comparison().omitted`, and the column's rendered `attempt` value.
Five were caught (both bounds constants, `stateOf(0)`, the schema string, and
`comparison().omitted`); ten were missed and all ten were then probed against the
unmutated implementation to classify them. Every one of the ten behaves correctly,
so all ten are **coverage gaps rather than defects**: `select(['a1','a1'])`
returns `['a1']`; `select()` of five ids returns four; `select(['a1','nope'])`
returns `['a1']` and `comparison()` does not throw; an unknown `toggle()` returns
`{selected: false, reason: 'unknown_candidate'}`; `mount()` with no host throws
"Result compare requires a host"; `destroy()` empties the host and removes
`data-result-compare`; a ready candidate renders the registry's real
`<img class="result-preview__image">` / `<pre class="result-preview__text">` with
no bare reference span; the candidate's value is not aliased to the staged item
(mutating `item.value.url` leaves the candidate at `/orig.png`); and the rendered
`<dd>` after `<dt>attempt</dt>` carries the real attempt id. The escaping gap was
probed with hostile input — a title of `<img src=x onerror=alert(1)>`, a subtitle
and `item_id` carrying `"><script>alert(2)</script>`, a `run_id` carrying
`" onload="alert(3)`, an `attempt_id` of `<svg onload=alert(4)>`, an
`output_name` of `a&b"c'd<e>`, and a `javascript:` preview reference — and no
script, event-handler attribute or `javascript:` scheme survived into the markup
while `&amp;`, `&quot;`, `&lt;` and `&#39;` all appeared and the unsafe reference
reported `unsafe_reference` with a visible message, so the escaper is correct and
only its pinning is missing.

Independent DoD probe: staged five outputs through the tray with a different mix
from the developer's (Codex raw text, RunningHub `{kind:'video',url,filename}`,
ComfyUI `{kind:'image',filename,subfolder,item_type,url}`, MCP
`{kind:'file',uri,mime_type}`) across two attempts, then compared two of them.
Every column carried its `run_id`/`attempt_id`/`output_name`; the Codex text
rendered a real `<pre>` and the RunningHub video a real `<video src=…>`; the state
moved `incomplete → ready` with the selection in the user's own order; dropping a
selected candidate through `setCandidates` preserved the survivors and reported the
vanished id in `omitted`; the staged tray snapshot stayed byte-identical, every
`materialized` flag stayed `false`, the Canvas graph object was byte-identical, and
neither the tray's nor the workspace's public surface contains any
materialize/promote/create-node/persist key. The DoD — "Users can compare
candidates while they remain run results" — therefore holds independently.

Architecture and ownership, re-checked independently: `WorkbenchCanvasResultCompare`
has exactly one consumer (`task-rich-node.js`) and one definition, so no duplicate
owner was introduced and none needed removing; every `graph`/`canvas`/`node`/
`persist` occurrence in the module is header-comment prose, the IIFE's own name, the
delegated preview global, or the export name, with no graph mutation, node creation,
persistence or transport; the workspace renders into a `data-result-compare-host`
section inside the existing node shell, created only when
`settings.resultCompareOptions` is present and torn down by the shell's `destroy()`,
so the single-Unified-Canvas constraint holds and no second canvas is introduced;
`canvas.html` loads preview (435) → tray (436) → compare (437) → bootstrap (500),
which is the correct dependency order because the compare seam delegates to the
preview registry; the Classic per-output pairwise slider in
`canvas-app-output-ui.js` and `media-tools.js` is untouched and is a different
concept (an output that already exists on a Canvas node), so no behaviour was
duplicated or replaced; and `media-kind.js` remains the only URL/extension
classifier, with the compare seam re-deriving nothing.

Non-blocking observations, recorded for a later tidy rather than as blockers. The
rendered column body is the weakest-pinned part of the card: neither the rendered
preview element nor the rendered metadata *values* are asserted (only the metadata
label `<dt>attempt</dt>` is), so a regression that swapped the preview for the bare
reference, or blanked a metadata value, would pass — two added assertions would
close both. `destroy()` is pinned only as "a function exists" and by the shell's
source scan, exactly as the R8-16 tray seam is, so this is a family-wide convention
gap rather than anything new here; one call-and-assert would close it for all three
seams. `select()`'s de-duplication, capacity and unknown-id guards are correct but
untested, and `comparison()` relies on those guards holding — it indexes
`byId.get(id)` without a null check — so a future edit that weakened `select()`
would turn a silent guard loss into a runtime throw; a single test per guard would
make the invariant explicit. Finally, `mount()`'s host guard and the candidate value
clone are correct but unpinned.

## Next Recommended Card

`R8-19`

Do not execute the next card in the same Agent run.
