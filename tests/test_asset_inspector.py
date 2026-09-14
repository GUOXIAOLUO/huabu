import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSPECTOR_MODULE = ROOT / "static/js/workbench/canvas/asset-inspector.js"
PANEL_MODULE = ROOT / "static/js/workbench/canvas/asset-query-panel.js"
PAGE_JS = ROOT / "static/js/asset-manager.js"
PAGE_HTML = ROOT / "static/asset-manager.html"
PAGE_CSS = ROOT / "static/css/asset-manager.css"

# Two versions that differ in every content field, so a render that reaches for
# the wrong one is visible: v1 is a servable image, v2 is a `file://` video.
FIXTURE = """
const esc = value => String(value ?? '')
  .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const asset = {id:'asset-1', project_id:'project-1', type:'image', source:'upload',
               status:'ready', version_ids:['v1','v2'],
               metadata:{name:'Hero board', tags:['hero','board']}};
const history = {assetId:'asset-1', currentVersionId:'v2', versions:[
  {id:'v1', asset_id:'asset-1', ordinal:1, created_at:'2026-09-13T10:00:00+08:00',
   content:{location:'https://cdn.example.com/hero.png', checksum:'sha256:'+'a'.repeat(64),
            mime_type:'image/png', size_bytes:2048},
   provenance:{source:'upload', source_ref:'inbox/hero.png', actor_id:'owner'}, metadata:{}},
  {id:'v2', asset_id:'asset-1', ordinal:2, created_at:'2026-09-13T11:30:00+08:00',
   content:{location:'file:///Users/lo/hero-v2.mp4', checksum:'sha256:'+'b'.repeat(64),
            mime_type:'video/mp4', size_bytes:10485760},
   provenance:{source:'import', source_ref:null, actor_id:null}, metadata:{}},
]};
"""

# The page's inspector invariant is a *lifecycle* property: a query reload that
# no longer contains the selected asset must hide the inspector. Asserting that a
# call appears in the file cannot observe which path makes it, so this harness
# drives the shipped lifecycle instead. The page's own functions are extracted
# verbatim from the file (never retyped) and given the page's own state; only the
# DOM elements, the two clients and the icon refresh are stubbed, and the
# presentation module under test is the real one. If a function is renamed or
# moved the extraction fails loudly rather than silently passing.
PAGE_LIFECYCLE_FUNCTIONS = (
    "assetQuerySignature",
    "renderAssetQueryPanel",
    "restoreAssetQueryFocus",
    "loadAssetQuery",
    "selectedQueryAsset",
    "assetInspectorVisible",
    "assetInspectorSignature",
    "renderAssetInspector",
    "loadAssetInspector",
    "syncAssetInspector",
    "selectQueryAsset",
)

PAGE_LIFECYCLE_HARNESS = """
'use strict';
require(__MODULE__);
const I = globalThis.WorkbenchAssetInspector;

/* Only the host page's externals are stubbed: the DOM elements, the two
 * clients, the icon refresh and the usage verdict. Every function below this
 * line is the shipped page's own source. */
function escapeHtml(value){ return String(value == null ? '' : value)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function escapeAttr(value){ return escapeHtml(value); }
function refreshIcons(){}
function setStatus(){}
function assetQueryVisible(){ return true; }
function ensureAssetQueryState(){ return { params: () => '[]' }; }
const assetQueryPanel = { render: () => '<query-panel>' };
const assetInspectorPanel = I.createInspector({ escapeHtml: escapeHtml, escapeAttr: escapeAttr });
function assetInspectorUsage(){ return { available: false, reason: '引用索引尚未接入' }; }

let nextQueryPage = null;
function assetQueryClient(){ return { query: async () => nextQueryPage }; }
const historyByAsset = {};
function assetInspectorClient(){ return { history: async id => historyByAsset[id] }; }

let assetQueryEl = { innerHTML: '' };
let assetInspectorEl = { innerHTML: '' };
let assetQueryPage = null;
let assetQueryLoading = false;
let assetQueryError = '';
let assetQueryRenderSeq = 0;
let assetQueryLastSignature = '';
let assetQueryPendingFocus = null;
let assetInspectorSelection = '';
let assetInspectorAssetId = '';
let assetInspectorVersionId = '';
let assetInspectorHistory = null;
let assetInspectorLoading = false;
let assetInspectorError = '';
let assetInspectorRenderSeq = 0;
let assetInspectorLastSignature = '';

__FUNCTIONS__

const assetA = { id:'asset-A', type:'image', source:'upload', status:'ready', metadata:{name:'甲资产'} };
const assetB = { id:'asset-B', type:'image', source:'upload', status:'ready', metadata:{name:'乙资产'} };
historyByAsset['asset-A'] = { assetId:'asset-A', currentVersionId:'va1', versions:[
    { id:'va1', asset_id:'asset-A', ordinal:1,
      content:{ location:'/static/media/a.png', checksum:'c1', mime_type:'image/png', size_bytes:10 },
      provenance:{ source:'upload' }, created_at:'2026-09-13T10:00:00+08:00', metadata:{} } ] };
historyByAsset['asset-B'] = { assetId:'asset-B', currentVersionId:'vb1', versions:[
    { id:'vb1', asset_id:'asset-B', ordinal:1,
      content:{ location:'/static/media/b.png', checksum:'c2', mime_type:'image/png', size_bytes:20 },
      provenance:{ source:'import' }, created_at:'2026-09-13T09:00:00+08:00', metadata:{} } ] };

const flush = () => new Promise(resolve => setTimeout(resolve, 0));
function resetWorld(){
    assetInspectorSelection = ''; assetInspectorAssetId = ''; assetInspectorVersionId = '';
    assetInspectorHistory = null; assetInspectorError = ''; assetInspectorLoading = false;
    assetInspectorLastSignature = ''; assetInspectorRenderSeq = 0; assetInspectorEl.innerHTML = '';
    assetQueryLastSignature = ''; assetQueryPage = null;
}

(async () => {
    /* Scenario A: the user pages forward to a page without the selected asset. */
    resetWorld();
    assetQueryPage = { total:2, items:[assetA, assetB], limit:20, offset:0 };
    nextQueryPage = assetQueryPage;
    selectQueryAsset('asset-A');
    await flush();
    const selectRendersAsset = assetInspectorEl.innerHTML.indexOf('甲资产') !== -1;

    nextQueryPage = { total:2, items:[assetB], limit:20, offset:20 };
    await loadAssetQuery();
    const pagerHtmlLength = assetInspectorEl.innerHTML.length;

    /* Scenario B: the user narrows the search so the selection drops out. */
    resetWorld();
    assetQueryPage = { total:2, items:[assetA, assetB], limit:20, offset:0 };
    nextQueryPage = assetQueryPage;
    selectQueryAsset('asset-A');
    await flush();
    nextQueryPage = { total:1, items:[assetB], limit:20, offset:0 };
    await loadAssetQuery();
    const searchHtmlLength = assetInspectorEl.innerHTML.length;

    /* Scenario C: switching to a different asset must load *that* asset's
     * history. The two assets differ in every field, including their version ids
     * and provenance, so a history that did not switch is visible. */
    resetWorld();
    assetQueryPage = { total:2, items:[assetA, assetB], limit:20, offset:0 };
    nextQueryPage = assetQueryPage;
    selectQueryAsset('asset-A');
    await flush();
    const showsAAfterSelectA = assetInspectorEl.innerHTML.indexOf('甲资产') !== -1;
    selectQueryAsset('asset-B');
    await flush();
    const switchHtml = assetInspectorEl.innerHTML;

    console.log(JSON.stringify({
        selectRendersAsset,
        pagerHidesInspector: pagerHtmlLength === 0,
        searchHidesInspector: searchHtmlLength === 0,
        pagerHtmlLength,
        searchHtmlLength,
        showsAAfterSelectA,
        switchShowsSecond: switchHtml.indexOf('乙资产') !== -1,
        switchNoStaleFirst: switchHtml.indexOf('甲资产') === -1,
        switchShowsSecondVersion: switchHtml.indexOf('vb1') !== -1,
        switchNoStaleFirstVersion: switchHtml.indexOf('va1') === -1,
    }));
})();
"""


def extract_page_function(source: str, name: str) -> str:
    """Return the verbatim source of a top-level page function, braces balanced.

    The scan tracks quotes, template literals and comments, so a brace inside a
    string or a comment cannot end the function early.
    """
    match = re.search(r"(?m)^(?:async\s+)?function %s\(" % re.escape(name), source)
    if match is None:
        raise AssertionError(f"page function not found at top level: {name}")
    start = match.start()
    position = source.index("{", match.end() - 1)
    depth = 0
    state = "code"
    while position < len(source):
        character = source[position]
        following = source[position + 1] if position + 1 < len(source) else ""
        if state == "code":
            if character == "/" and following == "/":
                state, position = "line", position + 2
                continue
            if character == "/" and following == "*":
                state, position = "block", position + 2
                continue
            if character == "'":
                state = "single"
            elif character == '"':
                state = "double"
            elif character == "`":
                state = "template"
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return source[start:position + 1]
        elif state in ("single", "double", "template"):
            if character == "\\":
                position += 2
                continue
            if (state == "single" and character == "'") \
                    or (state == "double" and character == '"') \
                    or (state == "template" and character == "`"):
                state = "code"
        elif state == "line":
            if character == "\n":
                state = "code"
        elif state == "block" and character == "*" and following == "/":
            state, position = "code", position + 2
            continue
        position += 1
    raise AssertionError(f"unbalanced braces extracting page function: {name}")


def page_lifecycle_harness() -> str:
    source = PAGE_JS.read_text(encoding="utf-8")
    functions = "\n\n".join(
        extract_page_function(source, name) for name in PAGE_LIFECYCLE_FUNCTIONS
    )
    return PAGE_LIFECYCLE_HARNESS.replace(
        "__MODULE__", json.dumps(str(INSPECTOR_MODULE))
    ).replace("__FUNCTIONS__", functions)


class AssetInspectorModuleTests(unittest.TestCase):
    def run_node(self, script):
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        return json.loads(result.stdout)

    def module_prelude(self):
        return f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(INSPECTOR_MODULE))}, 'utf8'), sandbox);
const I = sandbox.window.WorkbenchAssetInspector;
{FIXTURE}
const inspector = I.createInspector({{escapeHtml:esc, escapeAttr:esc}});
"""

    def test_preview_kind_comes_from_the_versions_own_mime_type(self):
        script = self.module_prelude() + """
const kind = mime => I.previewKind({content:{mime_type:mime}});
console.log(JSON.stringify({
  image: kind('image/png'), svg: kind('image/svg+xml'), video: kind('video/mp4'),
  audio: kind('audio/mpeg'), pdf: kind('application/pdf'), json: kind('application/json'),
  upper: kind('IMAGE/PNG'), missing: I.previewKind({}), nothing: I.previewKind(null),
  kinds: I.PREVIEW_KINDS,
}));
"""
        actual = self.run_node(script)
        self.assertEqual(actual["image"], "image")
        self.assertEqual(actual["svg"], "image", "an SVG version is still an image")
        self.assertEqual(actual["video"], "video")
        self.assertEqual(actual["audio"], "audio")
        self.assertEqual(actual["pdf"], "file", "a non-media mime is offered as a file, not guessed at")
        self.assertEqual(actual["json"], "file")
        self.assertEqual(actual["upper"], "image")
        self.assertEqual(actual["missing"], "file")
        self.assertEqual(actual["nothing"], "file")
        self.assertEqual(actual["kinds"], ["image", "video", "audio", "file"])

    def test_only_a_fetchable_location_is_ever_rendered_as_a_request(self):
        script = self.module_prelude() + """
        const locations = {
          https: I.isServableLocation('https://cdn.example.com/a.png'),
          http: I.isServableLocation('http://cdn.example.com/a.png'),
          rootRelative: I.isServableLocation('/static/a.png'),
          protocolRelative: I.isServableLocation('//evil.example.com/a.png'),
          file: I.isServableLocation('file:///Users/lo/a.png'),
          asset: I.isServableLocation('asset://a.png'),
          relative: I.isServableLocation('a.png'),
          blank: I.isServableLocation(''),
        };
        const servable = inspector.render(asset, history, {selectedVersionId:'v1'});
        const local = inspector.render(asset, history, {selectedVersionId:'v2'});
        console.log(JSON.stringify({
          locations,
          servableSrc: servable.includes('src="https://cdn.example.com/hero.png"'),
          localSrc: local.includes('src="file://'),
          localText: local.includes('file:///Users/lo/hero-v2.mp4'),
          servableOpenEnabled: !/data-asset-inspector-open="https:\\/\\/cdn\\.example\\.com\\/hero\\.png" disabled/.test(servable),
          localOpenDisabled: /data-asset-inspector-open="file:\\/\\/\\/Users\\/lo\\/hero-v2\\.mp4" disabled/.test(local),
          localDraggable: local.includes('data-asset-inspector-drag="1"'),
        }));
"""
        actual = self.run_node(script)
        for key, expected in (
            ("https", True), ("http", True), ("rootRelative", True),
            # A protocol-relative URL borrows the page's scheme; a `file://` or
            # `asset://` location is not something this page can fetch at all.
            ("protocolRelative", False), ("file", False), ("asset", False),
            ("relative", False), ("blank", False),
        ):
            self.assertEqual(actual["locations"][key], expected, f"{key} servability")

        self.assertTrue(actual["servableSrc"], "a servable location is previewed inline")
        self.assertFalse(actual["localSrc"], "a file:// location must never reach a src")
        self.assertTrue(actual["localText"], "...it is shown as text instead")
        self.assertTrue(actual["servableOpenEnabled"])
        self.assertTrue(actual["localOpenDisabled"])
        self.assertTrue(actual["localDraggable"], "a version with no servable location is still addressable")

    def test_the_shown_version_is_the_selection_else_the_one_the_reply_names(self):
        script = self.module_prelude() + """
        const noSelection = inspector.render(asset, history, {});
        const selected = inspector.render(asset, history, {selectedVersionId:'v1'});
        const stale = inspector.render(asset, history, {selectedVersionId:'v9'});
        const unknownCurrent = inspector.render(asset,
          {assetId:'asset-1', currentVersionId:'nope', versions:history.versions}, {});
        const noVersions = inspector.render(asset, {assetId:'asset-1', currentVersionId:null, versions:[]}, {});
        console.log(JSON.stringify({
          noSelectionShowsCurrentLocation: noSelection.includes('file:///Users/lo/hero-v2.mp4'),
          noSelectionIssuesNoRequest: !noSelection.includes('src="file://')
            && !noSelection.includes('src="https://cdn.example.com/hero.png"'),
          noSelectionPressed: noSelection.includes('data-asset-inspector-version="v2" aria-pressed="true"'),
          selectedPressed: selected.includes('data-asset-inspector-version="v1" aria-pressed="true"'),
          selectedImage: selected.includes('src="https://cdn.example.com/hero.png"'),
          staleFollowsCurrent: stale.includes('data-asset-inspector-version="v2" aria-pressed="true"'),
          unknownCurrentNote: unknownCurrent.includes('无法确定要显示的版本。'),
          unknownCurrentNoVersion: !/src="(file|https):/.test(unknownCurrent),
          noVersionsNote: noVersions.includes('该资产还没有任何版本。'),
          noVersionsHistoryNote: noVersions.includes('该资产还没有版本，因此没有历史可追溯。'),
        }));
"""
        actual = self.run_node(script)
        # With no selection the inspector follows the version the *reply* names
        # as current (v2), and the row it marks is that same version — so the
        # preview and the highlighted row can never disagree. v2's location is a
        # `file://` path, so it is shown as text and never requested.
        self.assertTrue(actual["noSelectionShowsCurrentLocation"])
        self.assertTrue(actual["noSelectionIssuesNoRequest"])
        self.assertTrue(actual["noSelectionPressed"])
        self.assertTrue(actual["selectedPressed"])
        self.assertTrue(actual["selectedImage"])
        # A selection that no longer resolves falls back to the reply's current
        # version rather than showing a version that is not there.
        self.assertTrue(actual["staleFollowsCurrent"])
        # A reply that names a current version its own list does not contain
        # shows no version at all: the alternative is guessing, and the message
        # must not claim the asset has no versions when it has two.
        self.assertTrue(actual["unknownCurrentNote"])
        self.assertTrue(actual["unknownCurrentNoVersion"])
        self.assertTrue(actual["noVersionsNote"])
        self.assertTrue(actual["noVersionsHistoryNote"])

    def test_render_shows_preview_metadata_history_provenance_and_actions(self):
        script = self.module_prelude() + """
        const html = inspector.render(asset, history, {selectedVersionId:'v1'});
        const rows = [...html.matchAll(/data-asset-inspector-version="([^"]+)"/g)].map(m => m[1]);
        console.log(JSON.stringify({
          name: html.includes('Hero board'),
          id: html.includes('asset-1'),
          typeBadge: html.includes('>图片<'),
          sourceBadge: html.includes('>上传<'),
          statusBadge: html.includes('>就绪<'),
          countBadge: html.includes('>v2<'),
          metaKey: html.includes('>tags<'),
          metaValue: html.includes('hero') && html.includes('board'),
          rows, newestFirst: html.indexOf('data-asset-inspector-version="v2"')
                             < html.indexOf('data-asset-inspector-version="v1"'),
          ordinals: html.includes('>v1<') && html.includes('>v2<'),
          currentBadgeCount: (html.match(/asset-inspector-current/g) || []).length,
          checksum: html.includes('sha256:' + 'a'.repeat(64)),
          mime: html.includes('image/png'),
          size: html.includes('2.0 KB'),
          timestamp: html.includes('2026-09-13 10:00'),
          provenanceSource: html.includes('>来源<'),
          provenanceRef: html.includes('inbox/hero.png'),
          provenanceActor: html.includes('>引入者<') && html.includes('owner'),
          usageHeading: html.includes('>被引用于<'),
          openAction: html.includes('data-asset-inspector-open='),
          dragAction: html.includes('data-asset-inspector-drag-hint'),
          escaped: !html.includes('<script'),
        }));
"""
        actual = self.run_node(script)
        for key in ("name", "id", "typeBadge", "sourceBadge", "statusBadge", "countBadge",
                    "metaKey", "metaValue", "newestFirst", "ordinals", "checksum", "mime",
                    "size", "timestamp", "provenanceSource", "provenanceRef",
                    "provenanceActor", "usageHeading", "openAction", "dragAction", "escaped"):
            self.assertTrue(actual[key], f"{key} must hold")
        self.assertEqual(actual["rows"], ["v2", "v1"], "newest first")
        # Exactly one row carries the current badge — the version the reply named.
        self.assertEqual(actual["currentBadgeCount"], 1)

    def test_usage_distinguishes_unavailable_from_no_references(self):
        script = self.module_prelude() + """
        const unavailable = inspector.render(asset, history,
          {usage:{available:false, reason:'引用索引尚未接入'}});
        const availableEmpty = inspector.render(asset, history, {usage:{available:true, references:[]}});
        const withRefs = inspector.render(asset, history,
          {usage:{available:true, references:[{kind:'canvas', id:'canvas-1', label:'主画布'}]}});
        const defaulted = inspector.render(asset, history, {});
        console.log(JSON.stringify({
          unavailableReason: unavailable.includes('引用索引尚未接入'),
          unavailableIsNotNone: unavailable.includes('尚未被任何记录引用'),
          availableEmptyIsNone: availableEmpty.includes('尚未被任何记录引用'),
          availableEmptyHasNoReason: availableEmpty.includes('引用索引尚未接入'),
          refLabel: withRefs.includes('主画布'),
          refId: withRefs.includes('canvas-1'),
          refKind: withRefs.includes('>canvas<'),
          defaultReason: defaulted.includes('尚未接入'),
          defaultIsNotNone: defaulted.includes('尚未被任何记录引用'),
        }));
"""
        actual = self.run_node(script)
        # "We did not look" must never render as "we looked and found nothing":
        # the second tells a user their asset is unused when nobody has checked.
        self.assertTrue(actual["unavailableReason"])
        self.assertFalse(actual["unavailableIsNotNone"])
        self.assertTrue(actual["availableEmptyIsNone"])
        self.assertFalse(actual["availableEmptyHasNoReason"])
        self.assertTrue(actual["refLabel"])
        self.assertTrue(actual["refId"])
        self.assertTrue(actual["refKind"])
        self.assertTrue(actual["defaultReason"])
        self.assertFalse(actual["defaultIsNotNone"])

    def test_drag_payload_addresses_the_version_and_carries_no_bytes(self):
        script = self.module_prelude() + """
        const payload = I.dragPayload(asset, history.versions[0]);
        const keys = Object.keys(payload).sort();
        const capture = fn => { try { fn(); return null; } catch (error) { return String(error.message); } };
        console.log(JSON.stringify({
          keys, payload,
          noAsset: capture(() => I.dragPayload(null, history.versions[0])),
          noVersion: capture(() => I.dragPayload(asset, null)),
        }));
"""
        actual = self.run_node(script)
        # Identity and the labels a drop target needs to describe the payload —
        # and nothing that would make the drop a copy of the file.
        self.assertEqual(actual["keys"], [
            "asset_id", "kind", "label", "mime_type", "ordinal", "type", "version_id",
        ])
        payload = actual["payload"]
        self.assertEqual(payload["kind"], "asset_version")
        self.assertEqual(payload["asset_id"], "asset-1")
        self.assertEqual(payload["version_id"], "v1")
        self.assertEqual(payload["ordinal"], 1)
        self.assertEqual(payload["label"], "Hero board")
        for absent in ("location", "checksum", "size_bytes", "content"):
            self.assertNotIn(absent, payload, "a drag payload must not carry the bytes or their address")
        self.assertIn("requires an asset and a version", actual["noAsset"])
        self.assertIn("requires an asset and a version", actual["noVersion"])

    def test_client_builds_one_canonical_request_and_normalizes_the_reply(self):
        script = self.module_prelude() + """
        const requests = [];
        const okFetch = async (url, options) => {
          requests.push({url, options});
          return {ok:true, status:200, json:async () => ({
            asset_id:'asset-1', current_version_id:'v2', versions:history.versions,
          })};
        };
        const client = I.createClient({fetch:okFetch, actorId:'local-workspace-actor'});
        const bare = I.createClient({fetch:async () => ({ok:true, status:200,
          json:async () => ({versions:[]})}), actorId:'a'});
        const denied = I.createClient({fetch:async () => ({ok:false, status:403,
          json:async () => ({detail:'denied'})}), actorId:'stranger'});
        const capture = fn => { try { fn(); return null; } catch (error) { return String(error.message); } };
        const badActor = capture(() => I.createClient({fetch:okFetch}));
        Promise.resolve()
          .then(() => client.history('asset-1'))
          .then(loaded => Promise.all([
            loaded, bare.history('asset-9'),
            denied.history('asset-1').then(() => null, error => String(error.message)),
            client.history('').then(() => null, error => String(error.message)),
          ]))
          .then(([loaded, barePage, error, noId]) => console.log(JSON.stringify({
            requests, loaded, barePage, error, noId, badActor, basePath: client.basePath(),
          })))
          .catch(error => console.log(JSON.stringify({fatal:String(error && error.message)})));
"""
        actual = self.run_node(script)
        self.assertEqual(len(actual["requests"]), 1, "one history read is one request")
        request = actual["requests"][0]
        self.assertEqual(request["url"], "/api/v1/assets/asset-1/versions")
        self.assertEqual(request["options"]["method"], "GET")
        self.assertEqual(request["options"]["headers"]["X-User-ID"], "local-workspace-actor")
        self.assertEqual(actual["loaded"]["assetId"], "asset-1")
        self.assertEqual(actual["loaded"]["currentVersionId"], "v2")
        self.assertEqual([item["id"] for item in actual["loaded"]["versions"]], ["v1", "v2"])
        # A reply that names no current version stays `null` rather than being
        # filled in with a guess by the client.
        self.assertIsNone(actual["barePage"]["currentVersionId"])
        self.assertEqual(actual["barePage"]["versions"], [])
        self.assertEqual(actual["error"], "denied")
        self.assertIn("requires an asset id", actual["noId"])
        self.assertIn("requires an actor id", actual["badActor"])
        self.assertEqual(actual["basePath"], "/api/v1/assets")

    def test_inspector_label_maps_are_exactly_the_domain_closed_sets(self):
        from typing import get_args

        from workbench.domain.asset import AssetSource, AssetStatus, AssetType

        actual = self.run_node(self.module_prelude() + """
console.log(JSON.stringify({types:I.TYPES, sources:I.SOURCES, statuses:I.STATUSES}));
""")

        # The label maps are the inspector's mirror of the domain's closed sets.
        # Pin the mirror against the domain source for exact equality — in order —
        # so the next widening cannot drift silently and leave a canonical member
        # unrenderable. Asserting the literals inside the JS file instead would be
        # tautological; the same comparison is made by
        # `test_node_record.test_published_node_kinds_are_exactly_the_domain_closed_set`
        # and by R9-05's panel guard, whose review is why this one exists.
        self.assertEqual(actual["types"], list(get_args(AssetType)))
        self.assertEqual(actual["sources"], list(get_args(AssetSource)))
        self.assertEqual(actual["statuses"], list(get_args(AssetStatus)))

    def test_module_stays_a_pure_presentation_and_read_seam(self):
        source = INSPECTOR_MODULE.read_text(encoding="utf-8")

        # No DOM, no persistence, no legacy store, no second transport.
        self.assertNotIn("document.", source)
        self.assertNotIn("localStorage", source)
        self.assertNotIn("/api/asset-library", source)
        self.assertNotIn("assetLibrary", source)
        self.assertIn("global.WorkbenchAssetInspector = Object.freeze({", source)
        self.assertIn("throw new TypeError('AssetInspectorClient requires an actor id')", source)
        self.assertIn("throw new TypeError('AssetInspector requires escapeHtml')", source)
        # The inspector exposes the drag but never installs a drop target or an
        # event listener: the Canvas accepting the payload is R9-07's, and a
        # handler here would be a second owner of that behavior. (`drop` also
        # appears in this module's prose, so pin the code, not the word.)
        self.assertNotIn("addEventListener", source)
        self.assertNotIn("'drop'", source)
        self.assertNotIn('"drop"', source)
        self.assertNotIn("dataTransfer", source)

    def test_asset_inspector_scripts_are_valid_javascript(self):
        for path in (INSPECTOR_MODULE, PANEL_MODULE, PAGE_JS):
            result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


class AssetInspectorPageTests(unittest.TestCase):
    def test_asset_manager_mounts_the_inspector_and_owns_the_events(self):
        page = PAGE_JS.read_text(encoding="utf-8")
        html = PAGE_HTML.read_text(encoding="utf-8")
        css = PAGE_CSS.read_text(encoding="utf-8")

        self.assertIn('<div id="assetInspector" class="asset-inspector-host"', html)
        self.assertIn("asset-inspector.js", html)
        self.assertLess(
            html.index("asset-inspector.js"),
            html.index("asset-manager.js"),
            "the inspector module must load before the page script",
        )

        self.assertIn("const assetInspectorEl = document.getElementById('assetInspector');", page)
        self.assertIn("window.WorkbenchAssetInspector.createInspector({", page)
        self.assertIn("window.WorkbenchAssetInspector.createClient({", page)
        self.assertIn("window.WorkbenchAssetInspector.dragPayload(", page)
        self.assertIn("function selectedQueryAsset(){", page)
        self.assertIn("function assetInspectorVisible(){", page)
        self.assertIn("function assetInspectorSignature(){", page)
        self.assertIn("function renderAssetInspector(){", page)
        self.assertIn("function loadAssetInspector(){", page)
        self.assertIn("function syncAssetInspector(){", page)
        self.assertIn("function selectQueryAsset(assetId){", page)
        self.assertIn("function openAssetInspectorLocation(location){", page)
        self.assertIn("function startAssetInspectorDrag(event){", page)
        self.assertIn("syncAssetInspector();", page)
        self.assertIn("selectedAssetId:assetInspectorSelection", page)
        for event in ("'click'", "'dragstart'"):
            self.assertIn(f"assetInspectorEl?.addEventListener({event}", page, f"the page must own the {event} path")

        # The transport and the request shape stay in the module: the page never
        # builds the version URL and never reaches into the legacy store.
        self.assertNotIn("/api/v1/assets", page)
        self.assertIn(".asset-inspector-host", css)
        self.assertIn(".asset-inspector-version", css)
        self.assertIn(".asset-inspector-usage", css)

    def test_query_panel_rows_expose_the_selection_the_inspector_follows(self):
        # R9-06 made the result rows selectable: selecting one is what gives the
        # inspector an asset to show. The panel owns the markup, the page owns
        # the click.
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PANEL_MODULE))}, 'utf8'), sandbox);
const P = sandbox.window.WorkbenchAssetQueryPanel;
const escapeHtml = value => String(value ?? '')
  .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const panel = P.createPanel({{escapeHtml, escapeAttr:escapeHtml}});
const query = P.createQuery({{projectId:'project-1'}});
const page = {{items:[
  {{id:'hero-board', type:'image', source:'upload', status:'ready', version_ids:['v1'], metadata:{{name:'Hero'}}}},
  {{id:'clip-01', type:'video', source:'import', status:'draft', version_ids:[], metadata:{{}}}},
], total:2, limit:24, offset:0, hasMore:false}};
const none = panel.render(query, page, {{}});
const one = panel.render(query, page, {{selectedAssetId:'hero-board'}});
console.log(JSON.stringify({{
  selects: [...none.matchAll(/data-asset-query-select="([^"]+)"/g)].map(m => m[1]),
  nonePressed: none.includes('data-asset-query-select="hero-board" aria-pressed="false"'),
  onePressed: one.includes('data-asset-query-select="hero-board" aria-pressed="true"'),
  oneOtherIdle: one.includes('data-asset-query-select="clip-01" aria-pressed="false"'),
  oneActive: /class="asset-query-row active"/.test(one),
  noneActive: /class="asset-query-row active"/.test(none),
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        actual = json.loads(result.stdout)

        self.assertEqual(actual["selects"], ["hero-board", "clip-01"], "every row is selectable")
        self.assertTrue(actual["nonePressed"])
        self.assertTrue(actual["onePressed"])
        self.assertTrue(actual["oneOtherIdle"])
        self.assertTrue(actual["oneActive"])
        self.assertFalse(actual["noneActive"])

    def test_a_query_reload_that_drops_the_selection_hides_the_inspector(self):
        # The page documents one invariant for the inspector: it shows an asset
        # from the *current* result page, and paging away from that asset hides it
        # rather than showing another page's asset. Asserting that
        # `syncAssetInspector();` appears in the file says nothing about which
        # paths call it, so the reload path could stop syncing and the suite would
        # stay green — which is exactly how a stale inspector shipped once. This
        # drives the shipped lifecycle functions instead of grepping for them.
        result = subprocess.run(
            ["node", "-e", page_lifecycle_harness()],
            check=True, capture_output=True, text=True,
        )
        actual = json.loads(result.stdout)

        self.assertTrue(actual["selectRendersAsset"], "selecting an asset renders it")
        self.assertTrue(
            actual["pagerHidesInspector"],
            f"paging away must hide the inspector (it rendered {actual['pagerHtmlLength']} bytes)",
        )
        self.assertTrue(
            actual["searchHidesInspector"],
            f"a narrowed search must hide the inspector (it rendered {actual['searchHtmlLength']} bytes)",
        )

    def test_selecting_a_different_asset_loads_that_assets_history(self):
        # The inspector's promise is that the versions on screen belong to the
        # asset on screen. Switching assets is the panel's most ordinary
        # interaction, and only the reset inside `syncAssetInspector` keeps the
        # previous asset's history from being rendered under the new heading —
        # without it the panel shows A's versions under B and never loads B's at
        # all, because the "already have a history" short-circuit sees one. The
        # shipped code is correct here, but nothing pinned it, so this drives the
        # switch. The two assets differ in every field, so the version-id
        # assertions prove the *history* switched and not merely the title.
        result = subprocess.run(
            ["node", "-e", page_lifecycle_harness()],
            check=True, capture_output=True, text=True,
        )
        actual = json.loads(result.stdout)

        self.assertTrue(actual["showsAAfterSelectA"], "selecting A renders A")
        self.assertTrue(actual["switchShowsSecond"], "selecting B must render B")
        self.assertTrue(actual["switchNoStaleFirst"], "B's view must carry no A content")
        self.assertTrue(
            actual["switchShowsSecondVersion"],
            "selecting B must load B's own version history",
        )
        self.assertTrue(
            actual["switchNoStaleFirstVersion"],
            "B's version list must not still be A's",
        )


if __name__ == "__main__":
    unittest.main()
