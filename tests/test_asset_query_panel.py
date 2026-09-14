import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PANEL_MODULE = ROOT / "static/js/workbench/canvas/asset-query-panel.js"
PAGE_JS = ROOT / "static/js/asset-manager.js"
PAGE_HTML = ROOT / "static/asset-manager.html"
PAGE_CSS = ROOT / "static/css/asset-manager.css"


def panel_source():
    return PANEL_MODULE.read_text(encoding="utf-8")


class AssetQueryPanelTests(unittest.TestCase):
    def run_node(self, script):
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        return json.loads(result.stdout)

    def module_prelude(self):
        return f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PANEL_MODULE))}, 'utf8'), sandbox);
const P = sandbox.window.WorkbenchAssetQueryPanel;
"""

    def test_query_state_validates_the_domain_vocabulary_and_resets_the_window(self):
        script = self.module_prelude() + """
const failures = [];
function capture(fn) { try { fn(); return null; } catch (error) { return String(error.message); } }
failures.push(capture(() => P.createQuery({})));
failures.push(capture(() => P.createQuery({projectId:'p', types:['nope']})));
failures.push(capture(() => P.createQuery({projectId:'p', sources:['nope']})));
failures.push(capture(() => P.createQuery({projectId:'p', statuses:['nope']})));
failures.push(capture(() => P.createQuery({projectId:'p', limit:7})));
failures.push(capture(() => P.createQuery({projectId:'p', offset:-1})));
failures.push(capture(() => P.createQuery({projectId:'p', tags:['   ']})));
const query = P.createQuery({projectId:'project-1'});
const initial = query.params();
const initialFiltered = query.isFiltered();
query.setOffset(48);
query.setText('  board  ');
const offsetAfterText = query.offset();
query.toggleType('image');
query.toggleType('video');
const typesOn = query.types();
query.toggleType('image');
const typesOff = query.types();
query.addTag('Hero');
query.addTag('hero');
const tags = query.tags();
query.removeTag('HERO');
const tagsAfter = query.tags();
query.setLimit(48);
const offsetAfterLimit = query.offset();
query.nextPage(); const next = query.offset();
query.previousPage(); const previous = query.offset();
query.previousPage(); const floor = query.offset();
const search = query.toSearch();
const filtered = query.activeFilterCount();
const isFiltered = query.isFiltered();
query.reset();
console.log(JSON.stringify({
  initial, initialFiltered, offsetAfterText, typesOn, typesOff, tags, tagsAfter,
  offsetAfterLimit, next, previous, floor, search, filtered, isFiltered,
  afterReset: query.params(), resetFiltered: query.isFiltered(), failures,
}));
"""
        actual = self.run_node(script)
        self.assertEqual(actual["initial"]["project_id"], "project-1")
        self.assertFalse(actual["initialFiltered"])
        self.assertEqual(actual["offsetAfterText"], 0, "changing what matches must reset the window")
        self.assertEqual(actual["typesOn"], ["image", "video"])
        self.assertEqual(actual["typesOff"], ["video"])
        self.assertEqual(actual["tags"], ["hero"], "tags are folded and de-duplicated")
        self.assertEqual(actual["tagsAfter"], [])
        self.assertEqual(actual["offsetAfterLimit"], 0, "changing the page size must reset the window")
        self.assertEqual((actual["next"], actual["previous"], actual["floor"]), (48, 0, 0))
        self.assertIn("project_id=project-1", actual["search"])
        self.assertIn("q=board", actual["search"])
        self.assertIn("type=video", actual["search"])
        self.assertIn("limit=48", actual["search"])
        self.assertEqual(actual["filtered"], 2)
        self.assertTrue(actual["isFiltered"])
        self.assertEqual(actual["afterReset"]["q"], "")
        self.assertEqual(actual["afterReset"]["type"], [])
        self.assertEqual(actual["afterReset"]["limit"], 24)
        self.assertFalse(actual["resetFiltered"])
        self.assertIn("requires a project id", actual["failures"][0])
        self.assertIn("Unsupported asset type", actual["failures"][1])
        self.assertIn("Unsupported asset source", actual["failures"][2])
        self.assertIn("Unsupported asset status", actual["failures"][3])
        self.assertIn("Unsupported asset page size", actual["failures"][4])
        self.assertIn("offset must be a non-negative integer", actual["failures"][5])
        self.assertIn("tag cannot be empty", actual["failures"][6])

    def test_client_builds_one_canonical_request_and_normalizes_the_reply(self):
        script = self.module_prelude() + """
const requests = [];
const okFetch = async (url, options) => {
  requests.push({url, options});
  return {ok:true, status:200, json:async () => ({
    items:[{id:'a1', project_id:'project-1', source:'upload', type:'image', status:'draft',
            version_ids:['v1'], metadata:{name:'Hero'}}],
    total:3, limit:24, offset:0, has_more:true,
  })};
};
const client = P.createClient({fetch:okFetch, actorId:'local-workspace-actor'});
const query = P.createQuery({projectId:'project-1'});
query.setText('board'); query.toggleType('image'); query.addTag('hero');
const badActor = (() => { try { P.createClient({fetch:okFetch}); return null; } catch (error) { return String(error.message); } })();
const denied = P.createClient({
  fetch:async () => ({ok:false, status:403, json:async () => ({detail:'denied'})}),
  actorId:'stranger',
});
Promise.resolve()
  .then(() => client.query(null).then(() => null, error => String(error.message)))
  .then(badQuery => Promise.all([badQuery, client.query(query)])
    .then(([badQuery, page]) => denied.query(query).then(() => null, error => String(error.message))
      .then(error => ({badQuery, page, error}))))
  .then(({badQuery, page, error}) => {
    console.log(JSON.stringify({
      requests, page, error, badActor, badQuery,
      basePath: client.basePath(),
      exported: {types:P.TYPES.length, sources:P.SOURCES.length, statuses:P.STATUSES.length,
                 sizes:P.PAGE_SIZES, defaultSize:P.DEFAULT_PAGE_SIZE},
    }));
  })
  .catch(error => { console.log(JSON.stringify({fatal:String(error && error.message)})); });
"""
        actual = self.run_node(script)
        self.assertEqual(len(actual["requests"]), 1, "one page is one request")
        request = actual["requests"][0]
        self.assertTrue(request["url"].startswith("/api/v1/assets/query?"))
        self.assertIn("project_id=project-1", request["url"])
        self.assertIn("q=board", request["url"])
        self.assertIn("type=image", request["url"])
        self.assertIn("tag=hero", request["url"])
        self.assertEqual(request["options"]["method"], "GET")
        self.assertEqual(request["options"]["headers"]["X-User-ID"], "local-workspace-actor")
        self.assertEqual(actual["page"]["items"][0]["id"], "a1")
        self.assertEqual(actual["page"]["total"], 3)
        self.assertTrue(actual["page"]["hasMore"])
        self.assertEqual(actual["page"]["limit"], 24)
        self.assertEqual(actual["error"], "denied")
        self.assertIn("requires an actor id", actual["badActor"])
        self.assertIn("requires an asset query", actual["badQuery"])
        self.assertEqual(actual["basePath"], "/api/v1/assets/query")
        self.assertEqual(actual["exported"]["defaultSize"], 24)
        self.assertEqual(actual["exported"]["sizes"], [24, 48, 96])

    def test_panel_renders_filters_results_and_pagination(self):
        script = self.module_prelude() + """
const escapeHtml = value => String(value ?? '')
  .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const panel = P.createPanel({escapeHtml, escapeAttr:escapeHtml});
const query = P.createQuery({projectId:'project-1'});
query.setText('board'); query.toggleType('image'); query.addTag('hero');
const page = {items:[{id:'hero-board', type:'image', source:'upload', status:'ready',
                      version_ids:['v1','v2'], metadata:{name:'Hero board'}}],
              total:9, limit:24, offset:0, hasMore:true};
const html = panel.render(query, page, {});
const empty = panel.render(P.createQuery({projectId:'p'}),
  {items:[], total:0, limit:24, offset:0, hasMore:false}, {});
const loading = panel.render(P.createQuery({projectId:'p'}), null, {loading:true});
const errored = panel.render(P.createQuery({projectId:'p'}), null, {error:'资产检索失败（403）'});
const last = panel.render(P.createQuery({projectId:'p', offset:24, limit:24}),
  {items:[{id:'clip-01', type:'video', source:'import', status:'draft', version_ids:[], metadata:{}}],
   total:26, limit:24, offset:24, hasMore:false}, {});
console.log(JSON.stringify({
  text: html.includes('data-asset-query-text') && html.includes('value="board"'),
  typeActive: html.includes('data-asset-query-type="image" aria-pressed="true"'),
  typeIdle: html.includes('data-asset-query-type="video" aria-pressed="false"'),
  sourceChips: [...html.matchAll(/data-asset-query-source="([^"]+)"/g)].map(m => m[1]),
  tagChip: html.includes('data-asset-query-tag="hero"'),
  tagInput: html.includes('data-asset-query-tag-input'),
  row: html.includes('Hero board') && html.includes('hero-board') && html.includes('v2'),
  rowType: html.includes('>图片<'),
  rowSource: html.includes('>上传<'),
  range: html.includes('1-1 / 9'),
  prevDisabled: html.includes('data-asset-query-page="prev" disabled'),
  nextEnabled: !html.includes('data-asset-query-page="next" disabled'),
  sizeOptions: [...html.matchAll(/data-asset-query-size[^>]*>([\\s\\S]*?)<\\/select>/g)].length,
  filtersOn: html.includes('已启用 3 个筛选条件'),
  resetEnabled: !html.includes('data-asset-query-reset disabled'),
  emptyNote: empty.includes('没有匹配的资产'),
  loadingNote: loading.includes('正在检索'),
  errorNote: errored.includes('asset-query-note danger') && errored.includes('403'),
  lastRange: last.includes('25-25 / 26'),
  lastPrevEnabled: !last.includes('data-asset-query-page="prev" disabled'),
  lastNextDisabled: last.includes('data-asset-query-page="next" disabled'),
  escaped: !html.includes('<script'),
  missingQuery: (() => { try { panel.render(null, page, {}); return null; } catch (e) { return String(e.message); } })(),
}));
"""
        actual = self.run_node(script)
        for key in ("text", "typeActive", "typeIdle", "tagChip", "tagInput", "row", "rowType",
                    "rowSource", "range", "prevDisabled", "nextEnabled", "filtersOn",
                    "resetEnabled", "emptyNote", "loadingNote", "errorNote", "lastRange",
                    "lastPrevEnabled", "lastNextDisabled", "escaped"):
            self.assertTrue(actual[key], f"{key} must hold")
        self.assertEqual(actual["sourceChips"], ["upload", "url", "local_path", "provider", "import", "execution"])
        self.assertEqual(actual["sizeOptions"], 1)
        self.assertIn("requires an asset query", actual["missingQuery"])

    def test_asset_manager_mounts_the_query_panel_and_owns_the_events(self):
        page = PAGE_JS.read_text(encoding="utf-8")
        html = PAGE_HTML.read_text(encoding="utf-8")
        css = PAGE_CSS.read_text(encoding="utf-8")

        self.assertIn('<div id="assetQueryPanel" class="asset-query-host"', html)
        self.assertIn("asset-query-panel.js", html)
        self.assertLess(
            html.index("asset-query-panel.js"),
            html.index("asset-manager.js"),
            "the panel module must load before the page script",
        )

        self.assertIn("const assetQueryEl = document.getElementById('assetQueryPanel');", page)
        self.assertIn("window.WorkbenchAssetQueryPanel.createPanel({", page)
        self.assertIn("window.WorkbenchAssetQueryPanel.createClient({", page)
        self.assertIn("window.WorkbenchAssetQueryPanel.createQuery({projectId})", page)
        self.assertIn("function ensureAssetQueryState(){", page)
        self.assertIn("function assetQuerySignature(){", page)
        self.assertIn("function renderAssetQueryPanel(){", page)
        self.assertIn("function loadAssetQuery(){", page)
        self.assertIn("function syncAssetQueryPanel(){", page)
        self.assertIn("syncAssetQueryPanel();", page)
        self.assertIn("descriptor.surface === 'library' && descriptor.kind === 'asset'", page)
        for event in ("'click'", "'input'", "'compositionstart'", "'compositionend'", "'change'", "'keydown'"):
            self.assertIn(f"assetQueryEl?.addEventListener({event}", page, f"the page must own the {event} path")
        self.assertIn("assetQueryState.setText(event.target.value || '')", page)
        self.assertIn("scheduleAssetQuerySearch();", page)
        self.assertIn("assetQueryPendingFocus", page)

        # The transport and the request shape stay in the module: the page never
        # builds a canonical query URL and never reaches into the legacy store.
        self.assertNotIn("/api/v1/assets/query", page)
        self.assertIn(".asset-query-host", css)
        self.assertIn(".asset-query-row", css)

    def test_query_panel_module_stays_a_pure_presentation_and_query_seam(self):
        source = panel_source()

        self.assertNotIn("/api/asset-library", source)
        self.assertNotIn("assetLibrary", source)
        self.assertNotIn("localStorage", source)
        self.assertNotIn("document.", source)
        self.assertIn("global.WorkbenchAssetQueryPanel = Object.freeze({", source)
        self.assertIn("throw new TypeError('AssetQueryClient requires an actor id')", source)
        # The vocabulary mirrors the domain's closed sets rather than inventing
        # a parallel one.
        for value in ("'image', 'video', 'audio', 'document', 'model', 'workflow', 'other'",
                      "'upload', 'url', 'local_path', 'provider', 'import', 'execution'",
                      "'draft', 'ready', 'archived'"):
            self.assertIn(value, source)

    def test_panel_filter_vocabulary_is_exactly_the_domain_closed_sets(self):
        from typing import get_args

        from workbench.application.asset_query import MAX_PAGE_SIZE, MAX_TAG_LENGTH, MAX_TEXT_LENGTH
        from workbench.domain.asset import AssetSource, AssetStatus, AssetType

        script = self.module_prelude() + """
const maxText = __MAX_TEXT__;
const maxTag = __MAX_TAG__;
function capture(fn) { try { fn(); return null; } catch (error) { return String(error.message); } }
const boundary = {
  textAtLimit: capture(() => P.createQuery({projectId:'p', text:'x'.repeat(maxText)})),
  textOverLimit: capture(() => P.createQuery({projectId:'p', text:'x'.repeat(maxText + 1)})),
  tagAtLimit: capture(() => P.createQuery({projectId:'p', tags:['x'.repeat(maxTag)]})),
  tagOverLimit: capture(() => P.createQuery({projectId:'p', tags:['x'.repeat(maxTag + 1)]})),
};
console.log(JSON.stringify({
  types: P.TYPES, sources: P.SOURCES, statuses: P.STATUSES,
  pageSizes: P.PAGE_SIZES, boundary,
}));
""".replace("__MAX_TEXT__", str(MAX_TEXT_LENGTH)).replace("__MAX_TAG__", str(MAX_TAG_LENGTH))
        actual = self.run_node(script)

        # The panel mirrors the domain's closed sets rather than owning them.
        # Pin the mirror against the domain source for exact equality so the next
        # widening cannot drift silently — the same comparison
        # `test_node_record.test_published_node_kinds_are_exactly_the_domain_closed_set`
        # makes for the published node kinds. Asserting the literals inside the JS
        # file instead would only be tautological: it would stay green while the
        # canonical search UI lost the ability to filter a canonical member.
        self.assertEqual(actual["types"], list(get_args(AssetType)))
        self.assertEqual(actual["sources"], list(get_args(AssetSource)))
        self.assertEqual(actual["statuses"], list(get_args(AssetStatus)))

        # The client-side bounds are driven from the Python constants, so a drift
        # on either side fails here rather than as a server 422 the user sees.
        self.assertIsNone(actual["boundary"]["textAtLimit"])
        self.assertIn("at most", actual["boundary"]["textOverLimit"])
        self.assertIsNone(actual["boundary"]["tagAtLimit"])
        self.assertIn("at most", actual["boundary"]["tagOverLimit"])

        # Every page size the panel can build must be one the server accepts.
        self.assertTrue(actual["pageSizes"])
        self.assertLessEqual(max(actual["pageSizes"]), MAX_PAGE_SIZE)
        self.assertGreaterEqual(min(actual["pageSizes"]), 1)

    def test_asset_query_panel_scripts_are_valid_javascript(self):
        for path in (PANEL_MODULE, PAGE_JS):
            result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
