# CARD R9-01 — Asset Domain

- Round: R9
- Priority: P0
- Status: DONE — independent Review PASS; archived 2026-09-13
- Depends on: `R8-22` (DONE, independent Review PASS)

## Goal

Define Asset as external/input resource identity.

## Before Owner

file + JSON metadata

## After Owner

Asset

## In Scope

- Define asset identity/project/source/type/status/metadata.
- Separate identity from versions.

## Out of Scope

- No WholeHouse asset subclasses in Core.

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

- [x] Asset can reference multiple immutable versions.

## Developer Verification

Scope decision (asked before implementing, not assumed): this card delivers the
domain record only. R9-03 owns `Build repository/service/API` and
`Map existing assets`, and R9-02 owns the version record and its rules, so
nothing here touches SQLite, `main.py`, the asset library files or any HTTP
surface. "Version" in the DoD therefore means a *reference by id*, not a version
record.

- New: `workbench/domain/asset/models.py` (`Asset`) and
  `workbench/domain/asset/__init__.py`. Nothing else in the tree changed for this
  card.
- Focused suite: `tests/test_asset_domain.py`, **17 tests**, all green.
- Full gate `./scripts/agent-verify.sh`: **PASS — 1145 tests** (1128 → +17),
  229 Python AST files (226 → +3), 146 JavaScript files, 4 architecture guards,
  clean `git diff --check`.
- DoD probe (independent mechanism, two OS processes sharing only a file):
  process 1 builds an Asset, appends two version references and writes
  `model_dump_json()` to disk; a brand-new process reads it back and proves
  `id`/`project_id`/`source`/`type`/`status` and `version_ids ==
  ("version-1", "version-2")` from the stored bytes, plus the literal
  `workbench.asset/1` marker and the absence of any version-content key.
- Mutation review: **18 probes, 17 caught on the first pass, 18/18 after one
  pin**; `workbench/domain/asset/models.py` restored byte-identical by sha256
  after every probe (all 18 runs parsed `Ran 17 tests`, so no probe was credited
  to a broken run).
  - Survivor closed: `with_version`'s duplicate refusal was **masked** —
    `pydantic.ValidationError` is a subclass of `ValueError`, so the record-level
    uniqueness check stood in for the domain guard and the test still passed. The
    test now asserts the refusal is *not* a `ValidationError` and carries the
    seam's own message.
  - Survivor classified non-blocking: `metadata: dict = Field(default_factory=dict)`
    → `metadata: dict = {}` is an **equivalent mutant**; pydantic v2 deep-copies a
    mutable class-level default per instance (shown directly: two instances share
    no metadata object and a write to one does not appear in the other). The
    `default_factory` form is kept as intent and to match `Collection`, and the
    invariant is now pinned by *outcome* (a write to one record never appears in
    another) rather than by object identity alone.
- Defects found and fixed while reviewing my own work: the two above, plus the
  shape of the record is now pinned as a whole —
  `set(Asset.model_fields)` equals exactly the eight identity fields, which is
  what makes "identity carries no version content" a testable claim rather than a
  comment.

Deliberate stops, for the successor to inherit rather than rediscover:

- **No `current_version_id`, no version ordering rule, no checksum.** Which
  version is current and what makes a version immutable are versioning *rules*;
  R9-02 owns them. Appending is the only operation here.
- **No `name`.** The card lists identity/project/source/type/status/metadata, so
  display names stay in `metadata` until a later card promotes them.
- **The Asset record is Core-only and industry-neutral.** The closed sets are the
  enforcement of the out-of-scope clause: `AssetType` has no WholeHouse kind, and
  `tests/test_asset_domain.py` pins all three closed sets by exact equality.
- **The published node-record schema needs no change**: `asset` is already a
  `NodeKind`, and `tests/test_node_record.py` now fails if the published `kind`
  enum ever drifts from `get_args(NodeKind)`.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Independent Review

Verdict: **PASS** (2026-09-13), reviewed while the card was still ACTIVE.

Reviewer probe set: **11 probes on axes disjoint from the developer's 18** —
requiredness of every identity field, append vs prepend, aliasing between a
record and the copy it produces, dump mode, element-level bounds, closed-set
narrowing. **9/11 on the first pass, 9/11 after four pins**; the two survivors
are equivalent mutants and are classified below. `workbench/domain/asset/models.py`
was restored byte-identical by sha256 after all 29 probes across both sets, and
every run parsed `Ran 19 tests`, so no probe was credited to a broken run.

Blocking findings — all four were missing pins, not defects in the record, and
all four are now closed:

- `id`, `project_id`, `source` and `type` had **no test proving they are
  required**. Giving any of them a default passed the whole suite, so an Asset
  could exist while answering "which asset is this?" with a placeholder. Pinned
  by `test_every_identity_field_is_required`.

Non-blocking survivors, both proven equivalent rather than assumed:

- `with_version` copying `dict(self.__dict__)` instead of dumping: pydantic's
  validation builds a new metadata dict, so the aliasing never materialises —
  measured both ways, `grown.metadata is a.metadata` is `False` and a write to
  the copy does not appear in the source. The invariant is still pinned by
  outcome in `test_a_grown_asset_shares_no_mutable_state_with_its_source`.
- `model_dump(mode="json")` instead of `mode="python"`: identical for every
  JSON-shaped metadata payload the record accepts (measured). Python mode is
  kept; whether metadata must be JSON-shaped at all is R9-03's call.

Observations for later cards — none of them defects in this one:

- **Nothing in production constructs an Asset yet.** R9-03 owns
  repository/service/API, so the record is deliberately un-wired.
- **A second published closed set drifts from `NodeKind`.**
  `schemas/renderer/renderer-manifest.v1.schema.json` `supported_kinds` lacks
  `collection` and `result`. Pre-existing, and this card adds no node kind, but
  it is the same drift class that `tests/test_node_record.py` now makes
  impossible for the node-record schema.
- **`AssetType` and the canvas `asset.*` port types are two Core closed sets
  naming asset kinds** (`image/video/audio/document/model/workflow/other` vs
  `asset.image/video/audio/file/cad`). R9-03 should decide whether they map to
  each other or stay independent.
- **"Immutable" ends at the record boundary.** Nothing stops a new Asset being
  built with fewer version ids; append-only holds only through `with_version`.
  That is the repository's job (R9-03), and the immutability of the version
  record itself is R9-02's.

## Final Ownership Evidence

Before:

`file + JSON metadata`. One asset was one mutable record inside
`data/asset_library.json` (`libraries → categories → items`, each item
`{id, name, url, kind, created_at}`), written and interpreted by `main.py`
(`load_asset_library` / `save_asset_library` / `make_asset_library_item` /
`migrate_asset_library_into_dirs`) and rendered by `static/js/asset-manager.js`.
Identity, content location and display name lived in the same record, and the
record had no notion of a version at all.

After:

`Asset` — `workbench/domain/asset/models.py`. It is the only definition of asset
identity in Core: `id` + `project_id` + `source` + `type` + `status` +
`metadata`, and `version_ids` naming the versions it references. The record is
frozen, rejects unknown fields, and carries no content, checksum or storage
location, so a version cannot be edited through the Asset that names it.

Duplicate owner removed:

Partly, and the remainder is another card's by design. What this card removed is
the **duplicate definition of identity**: no other Core record defines what an
asset is, and `data/asset_library.json` is no longer the thing that decides it —
it is now only where the legacy file metadata happens to live. What this card
deliberately did **not** remove is the legacy store itself: R9-03 explicitly owns
`Build repository/service/API` and `Map existing assets`, and this card's
compatibility clause forbids an unauthorized migration, so `main.py`'s asset
library read/write path is untouched and still serves the existing UI. R9-03 is
where that second owner is retired — it should read and write through
`Asset`/`AssetVersion` instead of the JSON item shape, and then delete the
duplicate.

## Next Recommended Card

`R9-02`

Do not execute the next card in the same Agent run.
