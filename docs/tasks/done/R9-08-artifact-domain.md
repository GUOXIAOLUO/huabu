# CARD R9-08 — Artifact Domain

- Round: R9
- Priority: P0
- Status: DONE — independent Review PASS (third review, 2026-09-14); archived 2026-09-14
- Depends on: R9-07

## Goal

Define Artifact as identity for Workbench-produced formal outputs.

## Before Owner

legacy output/result records

## After Owner

Artifact

## In Scope

- Define identity/type/project/title/state/metadata.
- Separate versions.

## Out of Scope

- No approval/frozen lifecycle yet beyond placeholder state.

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

- [x] Artifact exists independently from Canvas node.

## Developer Verification

Scope decision (the same one R9-01 made, and for the same reason): this card
delivers the domain record only. R9-09 owns the ArtifactVersion record *and*
`repository/service/API`, so nothing here touches SQLite, `main.py`, the
execution/result services or any HTTP surface. "Separate versions" therefore
means a *reference by id*, not a version record — exactly as R9-01's `version_ids`
did before R9-02.

- New: `workbench/domain/artifact/models.py` (`Artifact`, `ArtifactType`,
  `ArtifactState`, `ARTIFACT_SCHEMA_VERSION`) and
  `workbench/domain/artifact/__init__.py`. Nothing else in the tree changed for
  this card.
- Focused suite: `tests/test_artifact_domain.py`, **28 tests**, all green (26 as
  delivered, +1 for the first review's required change, +1 for the second
  review's; see below).
- Full gate `./scripts/agent-verify.sh`: **PASS — 1286 tests** (1258 → +28),
  254 Python AST files (251 → +3), 150 JavaScript files, 4 architecture guards,
  clean `git diff --check`.
- DoD probe (independent mechanism, two OS processes sharing only a file):
  process 1 builds an Artifact, appends two version references and writes
  `model_dump_json()` to disk; a brand-new process reads it back and proves
  `schema_version` / `id` / `project_id` / `type` / `title` / `state` and
  `version_ids == ("version-1", "version-2")` from the stored bytes, plus the
  absence of any canvas/node key and of any content/checksum/location key.
- Mutation review: **19 probes, 17 caught**; `workbench/domain/artifact/models.py`
  restored byte-identical by sha256 after every probe (all 19 runs of that review
  parsed `Ran 26 tests`, so no probe was credited to a broken run). The two survivors
  are the same two equivalent mutants R9-01's independent reviewer already
  classified, and both are measured equivalent here rather than assumed:
  - `payload = dict(self.__dict__)` instead of `model_dump(mode="python")` in
    `with_version`: the two payloads have identical keys and produce equal
    records, and the grown record shares no metadata object with its source
    either way (measured). The `model_dump` form is kept as intent.
  - `metadata: dict[str, Any] = {}` instead of `Field(default_factory=dict)`:
    pydantic v2 deep-copies a mutable class-level default per instance, so two
    artifacts still share no metadata object (measured: `is` → `False`). The
    `default_factory` form is kept as intent and to match `Asset`.

What the record deliberately does **not** carry, so the successor inherits the
decision instead of rediscovering it:

- **No version content, checksum, location or lineage.** `version_ids` names
  versions by id and nothing else; R9-09 owns the immutable version record and
  the run/attempt/input/prompt/model/skill lineage that hangs off it.
- **No `current_version_id` and no ordering rule.** Which version is current is
  a versioning rule; R9-09 owns it. Appending is the only operation here.
- **No approval or frozen lifecycle.** `state` is a placeholder: `ArtifactState`
  is `draft/ready/archived` with no approved/frozen member, and the record
  exposes no transition member — pinned by
  `test_no_approval_or_frozen_state_is_modelled` so a later card adds the
  lifecycle on purpose rather than by drift.
- **No Canvas.** The DoD is pinned twice: the field set contains no
  canvas/node/position/renderer key, and
  `test_the_artifact_module_imports_nothing_from_the_canvas_domain` fails if
  `workbench/domain/artifact/*` ever imports `workbench.domain.canvas`.
- **Nothing in production constructs an Artifact yet.** No repository, service,
  route or UI is wired; the legacy output/result records are untouched, so this
  card adds no behavior and migrates no data.

One divergence left for a later card, recorded rather than resolved: the Canvas
port vocabulary in `workbench/domain/canvas/port_type_registry.py`
(`artifact.file` / `artifact.image` / `artifact.video`) is a *port* closed set
naming what flows between nodes, while `ArtifactType` names what a produced
output *is*. They are different concepts and stay independent here — the same
drift class R9-01's reviewer flagged for `AssetType` vs the `asset.*` port
types, and still open.

## Independent Review

Verdict: **CHANGES_REQUIRED** (2026-09-14), reviewed while the card was still
ACTIVE. One required change, listed below; no defect was found in the record
itself.

Reviewer probe set: **16 probes on axes disjoint from the developer's 19** —
defaulted title, upper bounds on the *other* opaque ids, shallow metadata copy,
closed-set **narrowing** (not widening), required state, copy-instead-of-validate
in `with_version`, and two meta-probes that attack the DoD guards themselves.
**14/16 caught**, both files restored byte-identical by sha256 after every probe,
and every run parsed `Ran 26 tests`, so no probe was credited to a broken run.

The two DoD guards were attacked directly and both held: adding a `canvas_id`
field to the record fails three tests, and adding an unused
`from workbench.domain.canvas.models import NodeRecord` to `models.py` fails the
import-scan test. The DoD is therefore enforced, not merely asserted. An
independent cross-process probe (fresh process, nested metadata, non-ASCII title,
`state="ready"`) also confirms the record round-trips with no canvas/node key and
no content key.

### Required change

1. **The upper bound of every opaque id the record carries is not pinned.**
   `test_identity_bounds_are_enforced` proves 255 accepted / 256 rejected for `id`
   only. Widening `project_id` to `max_length=5000` (**V3**) or widening the
   version-id element bound to `max_length=5000` (**V3b**) both leave the whole
   suite green, while the two control probes on `id` (**V3c**) and `title`
   (**V3d**) are caught. The record is *correct* — measured: 255 accepted, 300
   rejected for both fields — but the bound is unguarded, so a future edit can
   widen the identity contract with no test signal. This is the same class as
   R9-01's four blocking findings, which were missing pins rather than defects.
   Close it by extending the existing test to assert the 255/256 boundary for
   `project_id` and for a version id, not only for `id`.

   **Closed 2026-09-14** (Authorized by the Owner; implemented by the developer,
   so the card is **not** self-PASSed — re-Review pending).
   `test_identity_bounds_are_enforced` now loops the 255/256 boundary over `id`
   and `project_id` and adds the same boundary for a version id, and a new
   `test_a_version_reference_is_bounded_through_the_append_seam` proves the bound
   also holds through `with_version` — the seam that re-validates the record —
   rather than only through the constructor. Re-running the probes: **V3 caught**
   (1 failure) and **V3b caught** (2 failures, constructor and append seam), with
   the `id` (V3c) and `title` (V3d) controls still caught. Focused suite
   **26 → 27 tests**; full gate **PASS — 1285 tests** (1258 → +27), 254 Python
   AST files, 150 JavaScript files, 4 architecture guards, clean
   `git diff --check`. `workbench/domain/artifact/models.py` is unchanged by the
   closure — only the test file moved.

### Non-blocking survivors and observations

- **Nested metadata immutability is unguarded, but not by this card.** Mutating
  the shared `freeze_value` list branch from `tuple(...)` to `list(...)`
  (**V13**) survives the artifact, asset and collection suites alike: a nested
  list inside `metadata` would become mutable while the record still claims a
  frozen interior. `freeze_value` is shared Core that predates this card and is
  used identically by `Asset` and `Collection`, so it fails the "is it this
  card's?" test and does not block. Worth pinning wherever `value_types` is next
  owned, or in R9-09 when metadata starts carrying real payloads.
- **`model_copy(update=...)` bypasses validation** on this frozen record (measured:
  it yields `state="ready"`, `project_id="p2"` from a `draft`/`p1` record). This
  is pydantic behaviour shared with every canonical record, not a contract this
  card introduced.
- **"Append-only" ends at the record boundary.** A new `Artifact` can be
  constructed with a shorter `version_ids` than an existing one of the same id;
  append-only holds only through `with_version`. The repository's job (R9-09),
  and the same observation R9-01's review recorded for `Asset`.
- **Nothing in production constructs an Artifact** — verified by import scan: no
  module outside `tests/test_artifact_domain.py` imports `workbench.domain.artifact`.
  Expected on this card; R9-09 wires it.
- **`ArtifactType` and the Canvas `artifact.*` port types remain two Core closed
  sets**, already recorded in the developer verification above.

### Second independent Review — CHANGES_REQUIRED (2026-09-14)

A second review, run after the first required change was closed, on axes
disjoint from both the developer's 19 probes and the first review's 16.

What it proved rather than assumed:

- **The DoD holds at runtime, not just on the page.** The first review only
  scanned the source for Canvas imports. This one installs an import hook that
  makes `workbench.domain.canvas*` *unimportable*, drops every `workbench`
  module from `sys.modules`, then imports the artifact package fresh and builds,
  appends, dumps and reloads a record. It succeeds, and `workbench.domain.canvas`
  never enters `sys.modules`. That is the card's DoD proven positively rather
  than by the absence of a line of source.
- **Concept separation is pinned** (AGENTS.md §2): making `Artifact` actually
  inherit `Asset` is **caught** (21 failures/errors), colliding its schema marker
  with `workbench.asset/1` is **caught**, and at runtime it is not an `Asset`
  subclass and rejects both `source` and `canvas_id`.
- **The first required change is genuinely closed**: re-running its two probes
  independently, widening `project_id` is **caught** and widening the version-id
  bound is **caught** (constructor and append seam).

### Required change (second review)

1. **Append order through `with_version` is not pinned.** The suite's
   `test_json_round_trip_preserves_identity_and_version_order` only sets
   `version_ids` *at construction*; nothing proves the append seam preserves
   order. A `sorted([...])` mutation of `with_version` (**R2-1**) leaves all 27
   tests green, and it is **not** an equivalent mutant: measured with uuid-style
   ids, appending `("c3f9", "a1b2", "b7c8")` yields
   `("a1b2", "b7c8", "c3f9")` — the version history is silently reordered. Real
   ids are opaque (`uuid4().hex` in the existing materialization service), so
   append order and lexicographic order disagree in ordinary use, and the record
   documents that "versions are appended and never rewritten". Close it by
   appending two ids whose lexicographic order differs from their append order
   and asserting the tuple is the append order.

   **Closed 2026-09-14** (Owner-authorized; implemented by the developer, so the
   card is **not** self-PASSed — re-Review pending). New
   `test_append_order_is_the_append_order_not_the_lexicographic_one` appends
   `version-2` then `version-1` and asserts the tuple is the append order.
   Re-running the probe: **R2-1 caught** (1 failure), and seven regression probes
   from earlier rounds (prepend, replace, `project_id` bound, version-id bound,
   unfrozen record, unknown fields allowed, duplicate version allowed) are all
   still caught. Focused suite **27 → 28 tests**; full gate **PASS — 1286 tests**
   (1258 → +28), 254 Python AST files, 150 JavaScript files, 4 architecture
   guards, clean `git diff --check`. As with the first closure,
   `workbench/domain/artifact/models.py` was unchanged — only the test file moved.

### Non-blocking (second review)

- **Two more shared-code probes survive, both in `workbench/domain/value_types.py`**
  — the nested-`dict` freeze (**R2-5**) and the recursive credential check
  (**R2-6**), so a nested `{"origin": {"api_key": ...}}` would be accepted and a
  nested dict would stay mutable. Same classification as the first review's V13:
  shared Core that predates this card, used identically by `Asset` and
  `Collection`, so it fails the "is it this card's?" test. Recommended pin for
  whoever next owns `value_types`, or for R9-09 when metadata starts carrying
  real payloads — the artifact suite can also pin its own claim cheaply.

### Third independent Review — PASS (2026-09-14)

Run after both required changes were closed, on axes disjoint from the
developer's 19 probes and from both earlier reviews. **No required change.**

The axis that mattered most was **whether the two closures are load-bearing** —
a pin that passes only because some other test happens to cover it is not a pin.
Both were attacked by *weakening the test that was added*, then re-running the
mutation:

- Weakening the append-order test to ascending ids makes the `sorted(...)`
  mutation (**R2-1**) survive again → the new test is the sole carrier of that
  invariant.
- Stripping the added `project_id` / version-id bound assertions makes the
  widened-`project_id` mutation (**V3**) survive again → likewise the sole
  carrier.

Suite robustness: the 28 tests pass when run from a foreign working directory
(`/tmp`), so nothing depends on the CWD, and each of the 28 also passes when run
individually, so there is no shared state between them.

Remaining record probes: defaulting `type` is **caught**. Two further survivors
are equivalent mutants today and are recorded rather than closed — dropping
`ARTIFACT_SCHEMA_VERSION` from the package exports (**R3-2**) changes no
behaviour because nothing consumes the constant yet (R9-09's repository will, and
should pin it then); and `state="ready"` with zero versions is accepted, which is
the out-of-scope placeholder state behaving as designed.

Ownership re-verified: **zero** references to `workbench.domain.artifact` outside
the test module, and no legacy result-path file was touched by any run on this
card. Ownership therefore stands exactly as the Final Ownership Evidence
describes — one new Core owner for produced-output identity, no duplicate
retired yet, which is R9-09's job.

Non-blocking nit: the developer-verification bullet "Nothing else in the tree
changed for this card" is literally false — the focused test file is new. It is
house phrasing carried over from R9-01 and means *no production file*, but the
next card should say so.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

`legacy output/result records`. A produced output had no identity of its own. It
was named only by the four-part execution address
(`ExecutionResultIdentity` — run/attempt/output_name/ordinal), and the moment it
was shown on a board it became a Canvas node: `ResultMaterializationService`
keeps the lineage inside the node's `config` (`result`) and `provenance_ref`,
while `NodeRecord.output_refs` names `artifact_version` ids that no Core record
defines yet. Whether a produced output existed, and what it was called, was
therefore answered by the Canvas node that happened to present it — delete the
node or move it to another board and the answer went with it.

After:

`Artifact` — `workbench/domain/artifact/models.py`. It is the only definition of
produced-output identity in Core: `id` + `project_id` + `type` + `title` +
`state` + `metadata`, and `version_ids` naming the versions it references. The
record is frozen, rejects unknown fields (including `canvas_id`), carries no
content, no storage location, no lineage and no Canvas reference, and is
validated and persisted without any Canvas — which is the card's DoD. Its
`workbench.artifact/1` marker separates it from `Asset`'s
`workbench.asset/1`: an input resource and a produced output are different
records and one cannot be reloaded as the other.

Duplicate owner removed:

Partly, and the remainder is another card's by design. What this card removed is
the **duplicate definition of identity**: "what one produced output is" now has
exactly one Core owner, and a Canvas node that presents an Artifact can no longer
be the thing that decides it. What this card deliberately did **not** remove is
the legacy result path itself — R9-09 explicitly owns `Add repository/service/API`
for versions, and this card's compatibility clause forbids an unauthorized
migration, so `ExecutionResultIdentity`, `ResultSelection`, the `result` node
definition and `ResultMaterializationService` are untouched and still own today's
behavior. R9-09 is where the second owner is retired: it should hang
`ArtifactVersion` off this identity and then give the legacy result records a
single successor.

## Next Recommended Card

`R9-09`

Do not execute the next card in the same Agent run.
