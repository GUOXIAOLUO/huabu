"""Executable characterization and close gate for R4-39."""

import json
import re
import subprocess
import unittest
from pathlib import Path

from tests.canvas_app_source import canvas_app_paths, read_canvas_app_source


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "plans" / "R4_39_CLASSIC_RUNTIME_REMOVAL.md"
CARD = ROOT / "docs" / "tasks" / "done" / "R4-39-remove-classic-runtime.md"
CLASSIC_RUNTIME = ROOT / "static" / "js" / "canvas.js"


def _manifest() -> dict:
    text = PLAN.read_text(encoding="utf-8")
    blocks = re.findall(r"```json\n(.*?)\n```", text, flags=re.DOTALL)
    if len(blocks) != 1:
        raise AssertionError("R4-39 plan must contain exactly one JSON manifest")
    return json.loads(blocks[0])


class R439ClassicRuntimeRemovalTests(unittest.TestCase):
    def test_canvas_app_modules_are_natively_loaded_in_order(self):
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        expected = [f"/{path.relative_to(ROOT)}" for path in canvas_app_paths(ROOT)]
        actual = re.findall(
            r'<script src="(/static/js/workbench/canvas/canvas-app-[^"]+)\?v=[^"]+"></script>',
            page,
        )
        self.assertEqual(actual, expected)
        self.assertNotIn("canvas-app-loader.js", page)
        for path in canvas_app_paths(ROOT):
            with self.subTest(path=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertNotIn("eval(", source)
                self.assertNotIn("new Function(", source)

    def test_canvas_inline_handlers_are_exported_by_the_small_bootstrap(self):
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        bootstrap = canvas_app_paths(ROOT)[-1].read_text(encoding="utf-8")
        handlers = set(re.findall(r'onclick="([A-Za-z_$][A-Za-z0-9_$]*)', page)) - {"event"}
        export_block = bootstrap[bootstrap.index("Object.assign(window, {"):bootstrap.index("const startCanvasApp")]
        for handler in handlers:
            with self.subTest(handler=handler):
                self.assertIn(f"    {handler},", export_block)

    def test_residual_clusters_are_grounded_while_runtime_exists(self):
        manifest = _manifest()
        self.assertEqual(manifest["schema"], "workbench.r4-39-classic-runtime-removal/2")
        self.assertEqual(tuple(manifest["sources"]), tuple(str(path.relative_to(ROOT)) for path in canvas_app_paths(ROOT)))
        clusters = manifest["clusters"]
        self.assertEqual(len(clusters), 8)
        self.assertEqual(len({item["id"] for item in clusters}), len(clusters))
        for cluster in clusters:
            with self.subTest(cluster=cluster["id"]):
                self.assertIn(cluster["status"], {"MIGRATE", "MIGRATED"})
                self.assertTrue(cluster["final_owner"].strip())
                self.assertTrue(cluster["evidence"])

        for cluster in clusters:
            target_rel = cluster["evidence_target"]
            target = ROOT / target_rel
            self.assertTrue(target.exists(), f"missing evidence target for {cluster['id']}: {target_rel}")
            source = target.read_text(encoding="utf-8")
            for evidence in cluster["evidence"]:
                with self.subTest(cluster=cluster["id"], evidence=evidence):
                    self.assertIn(evidence, source)

    def test_card_closes_only_after_classic_runtime_is_removed(self):
        card_text = CARD.read_text(encoding="utf-8")
        status = re.search(r"^- Status:\s*(\S+)", card_text, flags=re.MULTILINE)
        self.assertIsNotNone(status)
        self.assertFalse(CLASSIC_RUNTIME.exists())
        self.assertEqual(status.group(1), "DONE")

    def test_neutral_bootstrap_owns_startup_order_and_routing(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "app-bootstrap.js"
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        editor = read_canvas_app_source(ROOT)
        script = r"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {window: {}, URLSearchParams};
vm.runInNewContext(fs.readFileSync(process.argv[1], 'utf8'), sandbox);
const factory = sandbox.window.WorkbenchCanvasAppBootstrap;
const events = [];
let navigated = '';
const host = {
  initializeTheme: () => events.push('theme'),
  initializeToolbar: () => events.push('toolbar'),
  applyTranslations: () => events.push('translations'),
  updateDocumentTitle: () => events.push('title'),
  initializeOutputCompare: () => events.push('compare'),
  initializeOutputPreview: () => events.push('preview'),
  applyViewport: () => events.push('viewport'),
  revealAssetControls: () => events.push('assets'),
  loadConfiguration: async () => events.push('load-config'),
  pruneConfiguration: () => events.push('prune-config'),
  openCanvas: async id => events.push('open:' + id),
  canvasListUrl: () => '/static/canvas-list.html?project=p1',
  navigate: url => { navigated = url; events.push('navigate'); },
};
(async () => {
  const app = factory.create(host);
  const canvasResult = await app.start({search: '?id=c%201&unified_canvas=0'});
  const canvasEvents = events.splice(0);
  const listResult = await app.start({search: '?unified_canvas=0'});
  let missing = 0;
  for (const name of factory.REQUIRED_OPS) {
    const partial = Object.assign({}, host); delete partial[name];
    try { factory.create(partial); } catch (error) { if (error.name === 'TypeError') missing += 1; }
  }
  console.log(JSON.stringify({
    frozen: Object.isFrozen(app),
    methods: Object.keys(app),
    required: factory.REQUIRED_OPS.length,
    missing,
    canvasEvents,
    canvasResult,
    listEvents: events,
    listResult,
    navigated,
  }));
})().catch(error => { console.error(error); process.exit(1); });
"""
        result = subprocess.run(
            ["node", "-e", script, str(module)],
            check=True,
            text=True,
            capture_output=True,
        )
        actual = json.loads(result.stdout)
        prefix = [
            "theme", "toolbar", "translations", "title", "compare", "preview",
            "viewport", "assets", "load-config", "prune-config",
        ]
        self.assertTrue(actual["frozen"])
        self.assertEqual(actual["methods"], ["start"])
        self.assertEqual(actual["required"], 13)
        self.assertEqual(actual["missing"], 13)
        self.assertEqual(actual["canvasEvents"], prefix + ["open:c 1"])
        self.assertEqual(actual["canvasResult"], {"destination": "canvas", "canvasId": "c 1"})
        self.assertEqual(actual["listEvents"], prefix + ["navigate"])
        self.assertEqual(actual["listResult"], {"destination": "list", "url": "/static/canvas-list.html?project=p1"})
        self.assertEqual(actual["navigated"], "/static/canvas-list.html?project=p1")

        self.assertLess(page.index("workbench/canvas/app-bootstrap.js"), page.index("workbench/canvas/canvas-app-bootstrap.js"))
        self.assertNotIn("/static/js/canvas.js", page)
        self.assertIn("canvas-app-bootstrap.js?v=2026.09.09.2", page)
        self.assertIn("WorkbenchCanvasAppBootstrap.create", editor)
        self.assertIn("const startCanvasApp = () => canvasAppBootstrap.start", editor)
        self.assertNotIn("window.onload = async () =>", editor)

    def test_canvas_session_owns_record_save_and_remote_sync_lifecycle(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-session.js"
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        editor = read_canvas_app_source(ROOT)
        script = r"""
const fs = require('fs');
const vm = require('vm');
const events = [];
const saves = [];
let cursor = 4;
let scheduled = 0;
let cancelled = 0;
let markedAgain = 0;
let remoteStarted = 0;
let remoteStopped = 0;
let remoteRunning = false;
let remoteApplyDelay = 0;
let saveCalls = 0;
let local = {
  title: 'local', icon: 'x', nodes: [{id:'n1'}], connections: [],
  viewport: {x:9, y:8, scale:2}, logs: [],
};
const loads = [
  {ok:true, status:200, revision:4, canvas:{id:'c1', title:'loaded', nodes:[], connections:[], viewport:{x:1,y:2,scale:1}, updated_at:10}},
  {ok:true, status:200, revision:10, canvas:{id:'c1', title:'remote', nodes:[{id:'n2'}], connections:[], viewport:{x:3,y:4,scale:1}, updated_at:30}},
];
const sandbox = {window: {}};
sandbox.window.WorkbenchCanvasPersistence = {
  load: async () => loads.shift(),
  save: async (id, payload) => {
    saves.push({id, payload}); saveCalls += 1;
    if (saveCalls === 2) {
      return {ok:false, status:409, revision:12, updatedAt:40,
        canvas:{id:'c1', title:'conflicting-remote', updated_at:40}};
    }
    cursor = 5;
    return {ok:true, status:200, revision:5, updatedAt:20,
      payload:{canvas:{id:'c1', title:'server', viewport:{x:0,y:0,scale:1}, updated_at:20}}};
  },
  metadata: async () => ({ok:true, status:200, revision:10, updatedAt:30}),
  revisionOf: () => cursor,
  adoptRevision: (record, revision, fallback) => {
    cursor = Number(revision) || cursor;
    record.updated_at = Number(revision) || Number(record.updated_at) || Number(fallback) || 0;
    return record.updated_at;
  },
};
sandbox.window.WorkbenchCanvasSaveScheduler = {
  create: options => ({
    schedule(){ scheduled += 1; },
    flush(){ return options.run(); },
    drain(){ return Promise.resolve(false); },
    cancel(){ cancelled += 1; },
    markAgain(){ markedAgain += 1; },
    hasPendingAgain: () => false,
    hasScheduled: () => false,
    isInFlight: () => false,
  }),
  createRemoteApply: options => ({
    schedule(delay){ remoteApplyDelay = delay; },
    cancel(){},
    hasPending: () => false,
  }),
};
sandbox.window.WorkbenchCanvasRemoteSync = {
  create: options => ({
    check: () => options.onNewer(),
    start(){ if (!remoteRunning) { remoteRunning = true; remoteStarted += 1; } },
    stop(){ if (remoteRunning) { remoteRunning = false; remoteStopped += 1; } },
    isRunning: () => remoteRunning,
  }),
};
sandbox.window.WorkbenchCanvasUpdateMessage = {
  newerForCanvas: data => data.accept ? data : null,
};
vm.runInNewContext(fs.readFileSync(process.argv[1], 'utf8'), sandbox);
(async () => {
  const session = sandbox.window.WorkbenchCanvasSession.create({
    clientId: 'self',
    serialize: () => local,
    applyRecord: async (record, context) => {
      events.push(context.source + ':' + record.title);
      if (context.source !== 'saved') local = {...record};
    },
    setStatus: status => events.push('status:' + status),
    isVisible: () => true,
  });
  await session.open('c1');
  session.scheduleSave();
  await session.flush();
  const afterSave = session.snapshot();
  session.scheduleSave();
  await session.flush();
  const afterConflict = session.snapshot();
  const adopted = session.adoptRevision(9, 99);
  const handled = session.handleUpdate({accept:true, canvas_id:'c1'});
  const afterHandle = session.snapshot();
  session.scheduleSave();
  await session.flush();
  await session.sync();
  const afterRemote = session.snapshot();
  await session.close();
  console.log(JSON.stringify({
    frozen:Object.isFrozen(session), methods:Object.keys(session).sort(), events, saves,
    scheduled, cancelled, markedAgain, remoteStarted, remoteStopped,
    remoteApplyDelay, adopted, handled, afterSave, afterConflict, afterHandle, afterRemote,
  }));
})().catch(error => { console.error(error); process.exit(1); });
"""
        result = subprocess.run(
            ["node", "-e", script, str(module)],
            check=True,
            text=True,
            capture_output=True,
        )
        actual = json.loads(result.stdout)
        self.assertTrue(actual["frozen"])
        self.assertEqual(actual["methods"], [
            "adoptRevision", "close", "flush", "handleUpdate", "open",
            "scheduleSave", "snapshot", "sync",
        ])
        self.assertEqual(actual["scheduled"], 3)
        self.assertEqual(actual["remoteStarted"], 1)
        self.assertEqual(actual["remoteStopped"], 1)
        self.assertEqual(actual["remoteApplyDelay"], 120)
        self.assertTrue(actual["handled"])
        self.assertEqual(actual["adopted"], 9)
        self.assertEqual(actual["saves"][0]["id"], "c1")
        self.assertEqual(actual["saves"][0]["payload"]["client_id"], "self")
        self.assertEqual(actual["saves"][0]["payload"]["base_updated_at"], 10)
        self.assertEqual(actual["afterSave"]["updatedAt"], 20)
        self.assertFalse(actual["afterSave"]["dirty"])
        self.assertEqual(actual["afterConflict"]["revision"], 5)
        self.assertTrue(actual["afterConflict"]["dirty"])
        self.assertTrue(actual["afterHandle"]["dirty"])
        self.assertEqual(actual["markedAgain"], 0)
        self.assertEqual(actual["afterRemote"]["updatedAt"], 30)
        self.assertIn("open:loaded", actual["events"])
        self.assertIn("saved:server", actual["events"])
        self.assertIn("status:Save conflict", actual["events"])
        self.assertIn("remote:remote", actual["events"])
        self.assertLess(page.index("workbench/canvas/canvas-session.js"), page.index("workbench/canvas/canvas-app-bootstrap.js"))
        self.assertIn("WorkbenchCanvasSession.create", editor)
        self.assertNotIn("let localCanvasDirty", editor)
        self.assertNotIn("let applyingRemoteCanvas", editor)
        self.assertNotIn("WorkbenchCanvasPersistence.save", editor)
        self.assertNotIn("WorkbenchCanvasPersistence.metadata", editor)
        self.assertNotIn("WorkbenchCanvasRemoteSync.create", editor)
        self.assertNotIn("WorkbenchCanvasUpdateMessage.newerForCanvas", editor)


if __name__ == "__main__":
    unittest.main()
