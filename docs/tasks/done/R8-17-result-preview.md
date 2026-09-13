# CARD R8-17 — Result Preview

- Round: R8
- Priority: P1
- Status: DONE — independent Review PASS; archived 2026-09-12
- Depends on: R8-16 (DONE, independent Review PASS)

## Goal

Preview text/image/file results generically.

## Before Owner

raw output/log display

## After Owner

Result preview renderers

## In Scope

- Add preview registry.
- Support common result types.
- Handle unavailable/failed output refs.

## Out of Scope

- No R9 formal Asset/Artifact persistence yet.

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

- [x] Common outputs are inspectable in tray.

Proven by `tests/test_result_preview.py`, which drives the seam in a vm
sandbox. Every common result kind (text/image/video/audio/file/json/resource/
link/workflow) resolves to a registered renderer and renders a real element
(`<pre>`, `<img>`, `<video>`, `<audio>`, `<a>`), and the Result Tray renders its
staged cards through that registry: one end-to-end probe stages seven
executor-shaped outputs and the mounted tray produces one `<img>`, one
`<video>`, one text `<pre>`, one json `<pre>`, one anchor, and two explicitly
reasoned unavailable cards. References that cannot be rendered are reported with
a reason (`empty_output`, `failed_output`, `missing_reference`,
`unsafe_reference`, `unsupported_kind`) instead of rendering nothing, and the
composition boundary is pinned from both sides: the tray delegates when a
registry is loaded, and still renders exactly the bare reference marker it
rendered before when it is not.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: the Result Tray owned "how a result is displayed" as well as what it
staged, and what it displayed was not the result. `result-tray-runtime.js`
rendered every staged card as name + kind plus, for a previewable kind only,
`card.previewable ? '<span class="result-card__preview" data-preview-url="…"></span>' : ''`.
A characterized render of a staged image and video produced two **empty** spans
and zero real media elements, and a staged text output produced no preview node
at all. A user could therefore see that a result existed and which kind it was,
but could not inspect its value or its reference — the tray was a raw
output/log display.

After: `static/js/workbench/canvas/result-preview-runtime.js` owns result
preview rendering. It exposes a deterministic renderer registry
(`register`/`resolve`/`all`; highest priority wins, then lowest id, with no
fallback to a different kind), one built-in renderer per common result kind
(text, image, video, audio, file, json, resource, link, workflow), and a
two-state preview descriptor: `ready` carries the owning
`renderer_id`/`renderer_version`, and `unavailable` carries a reason
(`empty_output`, `failed_output`, `missing_reference`, `unsafe_reference`,
`unsupported_kind`) plus a human message. Descriptors are frozen and carry
`schema_version: workbench.result-preview/1`. The tray keeps staging, item
identity, idempotency and the list DOM, and now delegates only the preview body
through `previewBody(card, item)`.

Duplicate owner removed: the tray's inline raw preview markup, which is replaced
by that delegation — the tray no longer owns how a result is displayed, only
what is staged. No second classifier was introduced: the registry renders the
kind the tray already derived rather than re-deriving it from a value shape or a
URL extension, and a source scan rejects extension tokens (`.png`, `.mp4`, …)
and `WorkbenchCanvasMediaKind`, so `media-kind.js` stays the only URL/extension
classifier. No second reference resolver either: the registry consumes the
tray's already-resolved `preview_url` instead of re-implementing reference
extraction. The Classic Canvas output surfaces (`canvas-app-output-ui.js`,
`media-output-renderer.js`, the output lightbox) are a different surface and are
untouched and not duplicated.

## Developer Verification

- Focused: `12` tests covering renderer resolution for every common kind,
  text/json value rendering with escaping, media/reference element rendering,
  the full unavailable/failed reference table with reasons and messages, the
  unsafe-reference guard (a `javascript:` reference never reaches an attribute),
  frozen descriptors with provenance, duplicate registration rejection plus
  priority override, the no-reclassification rule, the
  no-Canvas-mutation/no-transport/no-duplicate-classifier source scan, the tray
  rendering through the registry, the tray's bare-marker composition path, and
  `canvas.html` registration order.
- Full: `./scripts/agent-verify.sh` PASS — `980` tests, `205` Python AST files,
  `137` JavaScript files, `4` architecture guards, and clean diff check.
- Developer Git Review: PASS; the reviewed changes are the new
  `result-preview-runtime.js` module, the new `tests/test_result_preview.py`
  suite, the `result-tray-runtime.js` preview delegation, the `static/canvas.html`
  script registration, and this card plus the status document update. `main.py`
  is untouched by this card and no backend module was modified. R8-16's frozen
  tray behaviour is preserved: its own suite still passes unchanged, including
  the bare-marker path exercised when only the tray module is loaded.
- Mutation verification: eleven guarded behaviours were mutated and, after
  closing one gap, all eleven were caught by the intended test with the sources
  restored byte-identical (`result-preview-runtime.js` sha256 `a97239d3…`,
  `result-tray-runtime.js` sha256 `4193fc8c…`) — removing the `failed_output`,
  `missing`, empty-reference, unsafe-reference and empty-value guards, making
  `isSafeRef` always accept, making `resolve` silently substitute any renderer
  for an unregistered kind, removing the tray's registry delegation, removing
  the tray's no-registry composition branch, and two DoD source-scan probes
  (injecting a node factory and injecting an extension classifier). Mutation
  testing found one real coverage gap: the `missing` flag guard was initially
  unpinned, so explicit `missing_ref` and `missing_item` cases were added and the
  mutation is now caught. The DoD source-scan guard was probed separately and is
  not toothless.
- Independent Review: PASS on 2026-09-12. The review reproduced the focused suite
  (`12` tests) and the full gate (`980` tests, `205` Python AST files, `137`
  JavaScript files, `4` architecture guards, clean diff check), and re-confirmed
  that R8-16's own `10` tests still pass unchanged against the modified tray. An
  independent DoD probe staged six real-executor-shaped outputs (Codex/
  DirectModel raw text, RunningHub `{kind, url}`, ComfyUI
  `{kind, filename, subfolder}`, MCP `{kind, uri}`, an unclassified object, and a
  `javascript:` link) and mounted the tray: every staged card was either rendered
  with a real element (text `<pre>`, image `<img>`, resource `<a>`, json `<pre>`)
  or reported `unavailable` with a reason, so "all inspected" and "every
  unavailable card carries a reason" both hold; no `javascript:` reached an
  attribute; no raw `data-preview-url` marker leaked into the registry path; the
  probe's Canvas graph object was byte-identical; and the tray controller still
  exposes exactly six keys. Ten further mutations were run on targets the
  developer had not covered — media kinds skipping the reference requirement,
  `escapeHtml` as a pass-through, `reasonMessage` empty, descriptors left
  unfrozen, schema drift, unavailable previews rendering nothing, the tray
  dropping the staged value, duplicate registration allowed, `resolve` ignoring
  priority, and the external link losing `rel="noopener"` — of which eight were
  caught and both sources restored byte-identical (`result-preview-runtime.js`
  sha256 `a97239d3…`, `result-tray-runtime.js` sha256 `4193fc8c…`). The two
  misses were investigated and are coverage gaps rather than defects:
  `Object.isFrozen` is asserted only for a `ready` preview, so the `unavailable`
  descriptor's frozen-ness is unpinned (a probe confirms it is in fact frozen);
  and the "priority override" test passes coincidentally because the custom
  renderer's id sorts before the built-in's, so it does not actually pin priority
  ordering (a probe with a custom renderer whose id sorts *after* the built-in
  shows priority does win, and a negative-priority renderer whose id sorts first
  correctly loses). Architecture and ownership were re-checked independently: no
  backend or Core module is in this card's change set (`main.py` mtime 13:53,
  before this card's 19:31–19:44 window); the module mentions no wholehouse
  vocabulary; its only `graph` occurrence is the header comment's prose, with no
  node creation or graph mutation; the only reference to
  `WorkbenchCanvasResultPreview` outside the module is the tray, so no duplicate
  owner exists; the module contains no extension tokens and no
  `WorkbenchCanvasMediaKind` reference, leaving `media-kind.js` the only
  URL/extension classifier; the Classic output surfaces
  (`canvas-app-output-ui.js` 2026-09-09, `media-output-renderer.js` 2026-09-08,
  `media-kind.js` 2026-09-09) are untouched; an unregistered kind resolves to an
  explicit `unsupported_kind` with a visible message rather than silently
  substituting another renderer, so the no-fallback claim holds; and
  `canvas.html` registers the registry (line 435) before the tray (line 436),
  both ahead of the app bootstrap (line 499), with that order pinned by a test.
  Two non-blocking observations are recorded: the `unavailable` descriptor's
  frozen-ness and the priority ordering are unpinned by tests (one added case
  each would close them, and the card's "priority override" wording overstates
  what that test proves), and the tray's staging-side `previewable` hint and the
  registry's `state: ready` answer different questions without being consumed by
  one another, though the overlapping naming is worth a tidy in a later card.

## Next Recommended Card

`R8-18`

Do not execute the next card in the same Agent run.
