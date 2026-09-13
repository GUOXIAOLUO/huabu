# CARD R9-02 — AssetVersion

- Round: R9
- Priority: P0
- Status: DONE — independent Review PASS; archived 2026-09-13
- Depends on: `R9-01` (DONE, independent Review PASS)

## Goal

Add immutable/versioned asset content records with checksums/provenance.

## Before Owner

mutable file metadata

## After Owner

AssetVersion

## In Scope

- Define version/content location/checksum/mime/size/provenance/timestamps.
- Create versioning rules.

## Out of Scope

- Do not duplicate file bytes on Canvas drag.

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

- [x] Version refs are stable and immutable.

## Developer Verification

Scope inherited from R9-01's close: **domain record only** — R9-03 owns
repository/service/API and the migration, so nothing here persists a version.

- New in `workbench/domain/asset/models.py`: `AssetVersion`,
  `AssetVersionContent`, `AssetVersionProvenance`, `AssetVersionRef` and
  `ASSET_VERSION_SCHEMA_VERSION = "workbench.asset-version/1"`. New focused
  suite `tests/test_asset_version.py`.
- Focused suites: `tests/test_asset_version.py` **22 tests** and
  `tests/test_asset_domain.py` **20 tests**, all green.
- Full gate `./scripts/agent-verify.sh`: **PASS — 1170 tests** (1147 → +23: 1 new
  R9-01 test for the repaired metadata guard, 22 for R9-02),
  229 Python AST files, 146 JavaScript files, 4 architecture guards, clean
  `git diff --check`.
- DoD probe (independent mechanism, two OS processes sharing only a file):
  process 1 writes two versions that share an identity and differ in *every*
  content field (location, checksum, mime, size) to disk; a brand-new process
  reads them back and proves `ref()` is equal across that change, from the
  stored bytes, and that the ref is exactly `(asset-1, version-1)`.
- Mutation review: **22 probes, 22/22**; `workbench/domain/asset/models.py`
  restored byte-identical by sha256 after every probe, and every run parsed
  `Ran 42 tests`, so no probe was credited to a broken run.
- Three probes survived the first pass and were closed by pins rather than
  explained away: `mime_type` had no minimum length, `source_ref` had no
  maximum, and `actor_id` had no minimum — three field bounds the record
  claims and nothing tested.

**A versioning rule, and why the ref looks the way it does.** `ref()` is derived
from `asset_id` + `version_id` only — never from content, size or time — so a
version stays addressable when its bytes move, are re-hashed or are
re-described. `AssetVersionRef.model_fields` is pinned to exactly
`{asset_id, version_id}`, which is what makes that stability a testable claim
instead of a comment. Ordinal is a sequence position (`ge=1`), not part of the
address; assigning ordinals and rejecting gaps needs the collection of versions,
so that rule belongs to R9-03's repository.

**Post-close repair to R9-01 (declared, not silent).** While adding
`AssetVersion` next to `Asset` in the same module, the neighbouring canonical
records (`ExecutionAttempt`, `ExecutionRun`, `ExecutionEvent`,
`ExecutionBranch`, `ResultSelection`) all freeze their metadata with
`assert_safe_metadata` + `freeze_value`, and `Asset` did not — a frozen record
with a mutable interior. R9-01 has no consumers yet, so the same treatment was
applied to `Asset.metadata` and both R9-01 probe sets were re-run against it
(19/20 with the known equivalent mutant, 9/11 with the two documented
equivalents, no regression). The DoD and the ownership statement of R9-01 are
unchanged; only the metadata guard tightened, and two R9-01 tests were updated
to assert the frozen behaviour instead of mutating metadata in place.

Deliberate stops, for the successor to inherit rather than rediscover:

- **Ordinal uniqueness per asset and gap-free sequences are not enforced.** A
  single record cannot see its siblings; R9-03's repository must reject a second
  version with the same `(asset_id, ordinal)`.
- **Immutability ends at the record boundary here too.** Nothing stops a new
  `AssetVersion` being built with the same id and different content; only the
  repository can make a version id single-assignment.
- **`Asset.version_ids` (R9-01) and `AssetVersionRef` coexist on purpose.** The
  parent names its versions by id; a ref is the self-contained address used when
  something outside the Asset has to point at one version (a Collection cell, an
  execution input). R9-03 should keep `asset.version_ids == [v.id for v in
  versions]` rather than pick one and drop the other.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Independent Review

Verdict: **PASS** (2026-09-13), reviewed while the card was still ACTIVE.

Reviewer probe set: **12 probes on axes disjoint from the developer's 22** —
schema shape (a record silently gaining a field), nested immutability,
record-degrades-to-dict, defaults appearing on fields that must be supplied,
ref semantics, ref shape. **9/12 on the first pass, 11/12 after two pins**; the
one survivor is an equivalent mutant, classified below. Every probe restored
byte-identical by sha256 across both touched files (`models.py` and
`value_types.py`), and every run parsed `Ran 44 tests`.

Blocking findings — both were missing pins, not defects in the record:

- **`AssetVersion` had no test pinning its own shape.** Adding a `url` field to
  the record passed the whole suite: the DoD turns on what a version *is*, and
  nothing asserted that. Pinned by `test_version_shape_is_pinned`, which also
  pins `AssetVersionProvenance`. (The provenance probe happened to be caught for
  an accidental reason — a test already passes a `wholehouse_kind` key — which
  is exactly the kind of coverage that should not be left to accident.)
- **Metadata was only proven frozen one level deep.** A shallow freeze would
  leave a mutable dict nested one step down — precisely the hole this round's
  post-close repair to `Asset` was closing. Pinned by
  `test_nested_metadata_is_frozen_too`.

Non-blocking survivor:

- `Field(default_factory=dict)` versus a bare `{}` default on the version's
  metadata is an **equivalent mutant**: pydantic gives each instance its own
  dict and the record freezes it on construction, so no aliasing can occur
  (measured). `default_factory` is kept to match the neighbouring records.

Observations for later cards — none of them defects in this one:

- **`workbench/domain/value_types.py` has no test file of its own**, although
  `assert_safe_metadata` and `freeze_value` are load-bearing in 11 domain
  modules. The nested-freeze probe above survived its first pass partly because
  no suite owns that shared guard.
- **The published node-record schema addresses `asset_version` by a single
  `id`** (`$defs.output_ref`, `input_binding`), while `AssetVersionRef` here
  addresses a version by `asset_id` + `version_id`, and R9-01's
  `Asset.version_ids` names versions by a single id. R9-03 must decide whether
  node and Collection refs adopt the two-part ref or stay on the single id —
  today the record and the published contract disagree, and adding a version ref
  to a node is not covered by either.
- **Nothing in production constructs an `AssetVersion` yet**; R9-03 owns the
  repository, the service and the API.

## Final Ownership Evidence

Before:

`mutable file metadata`. One asset had one mutable record
(`{id, name, url, kind, created_at}`) in `data/asset_library.json`; re-uploading
or replacing a file rewrote that record in place, so the previous bytes were
addressable by nothing — no checksum, no provenance, no way to say "the version
as of yesterday". Identity, content and history were the same mutable row.

After:

`AssetVersion` (+ `AssetVersionContent`, `AssetVersionProvenance`,
`AssetVersionRef`) in `workbench/domain/asset/models.py`. A version is a frozen
record: an address and a digest (`location`, `checksum`, `mime_type`,
`size_bytes`), where it came from (`provenance`, speaking the `AssetSource`
vocabulary), when it was created, and an `ordinal` position in its asset's
sequence. Nothing in it can be changed after construction — the record, its
content and its provenance are all frozen and reject unknown fields — and the
ref that addresses it is derived from identity alone, so it survives the content
moving or being re-hashed.

Duplicate owner removed:

Partly, and the rest is R9-03's by design. What this card removed is the
**mutable record as the owner of version facts**: content, checksum, provenance
and creation time now have exactly one Core definition, and it is immutable. What
it deliberately did not remove is the legacy file metadata in
`data/asset_library.json`, which is still what the existing UI reads — R9-03
owns `Map existing assets` and this card's compatibility clause forbids an
unauthorized migration, so the second owner is retired there, not here.

## Next Recommended Card

`R9-03`

Do not execute the next card in the same Agent run.
