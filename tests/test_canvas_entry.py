import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRY_COMPATIBILITY = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-entry-compatibility.js"


class CanvasEntryTests(unittest.TestCase):
    def test_new_canvas_flow_has_one_normal_creation_choice(self):
        source = (ROOT / "static" / "js" / "canvas-list.js").read_text(encoding="utf-8")
        create_flow = source[source.index("function openCreateCard") : source.index("/* ===== Card context menu")]
        self.assertNotIn("ws-create-toggle", create_flow)
        self.assertNotIn("createKind", create_flow)
        self.assertIn("kind: 'classic'", create_flow)
        self.assertNotIn("kind: 'smart'", create_flow)

    def test_canvas_list_does_not_display_legacy_source_kind_labels(self):
        source = (ROOT / "static" / "js" / "canvas-list.js").read_text(encoding="utf-8")
        self.assertNotIn("智能画布", source)
        self.assertNotIn("普通画布", source)
        self.assertNotIn("ws-card-kind", source)

    def test_canvas_list_uses_one_normal_open_entry(self):
        source = (ROOT / "static" / "js" / "canvas-list.js").read_text(encoding="utf-8")
        opening = source[source.index("function openCanvas(c){") : source.index("/* ===== Card create flow")]
        self.assertIn("/static/canvas.html", opening)
        self.assertNotIn("/static/smart-canvas.html", opening)

    def test_asset_manager_uses_the_same_normal_canvas_entry(self):
        source = (ROOT / "static" / "js" / "asset-manager.js").read_text(encoding="utf-8")
        page = (ROOT / "static" / "asset-manager.html").read_text(encoding="utf-8")
        opening = source[source.index("function canvasAssetOpenUrl(canvas){") : source.index("function activeCanvasAssetCanvas", source.index("function canvasAssetOpenUrl(canvas){"))]
        self.assertIn("WorkbenchCanvasEntryCompatibility.normalCanvasUrl", opening)
        self.assertNotIn("/static/smart-canvas.html", opening)
        self.assertLess(page.index("workbench/canvas/canvas-entry-compatibility.js"), page.index("asset-manager.js"))

    def test_asset_manager_hides_legacy_canvas_source_categories(self):
        source = (ROOT / "static" / "js" / "asset-manager.js").read_text(encoding="utf-8")
        categories = source[source.index("function canvasAssetCategories(){") : source.index("function activeCanvasAssetCategoryInfo", source.index("function canvasAssetCategories(){"))]
        self.assertIn("id:'all', name:'画布'", categories)
        self.assertNotIn("智能画布", source)
        self.assertNotIn("普通画布", source)

    def test_entry_compatibility_keeps_one_normal_entry_with_no_handoff_surface(self):
        # R4-35: the Smart handoff surface is retired. The module only exports
        # the normal entry URL + the list-project helpers; the handoff helpers
        # (requiresLegacySmartHandoff / legacySmartCanvasUrl) and the
        # /static/smart-canvas.html URL string are gone.
        source = ENTRY_COMPATIBILITY.read_text(encoding="utf-8")
        self.assertNotIn("fetch(", source)
        self.assertNotIn("localStorage", source)
        self.assertNotIn("requiresLegacySmartHandoff", source)
        self.assertNotIn("legacySmartCanvasUrl", source)
        self.assertNotIn("/static/smart-canvas.html", source)
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}, URLSearchParams}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ENTRY_COMPATIBILITY))}, 'utf8'), sandbox);
const E=sandbox.window.WorkbenchCanvasEntryCompatibility;
const keys = Object.keys(E).sort();
const hasHandoff = (typeof E.requiresLegacySmartHandoff !== 'undefined') || (typeof E.legacySmartCanvasUrl !== 'undefined');
const remembered = E.rememberedCanvasListProject({{storage:{{getItem:() => 'pX'}}, defaultProject:'p1'}});
const listUrl = E.canvasListUrl('p1');
console.log(JSON.stringify({{
  keys,
  hasHandoff,
  normal: E.normalCanvasUrl('canvas / 1', 'project / 1'),
  remembered,
  listUrl,
}}));
"""], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["keys"], [
            "canvasListUrl", "normalCanvasUrl", "rememberCanvasListProject", "rememberedCanvasListProject",
        ])
        self.assertFalse(out["hasHandoff"])
        self.assertEqual(out["normal"], "/static/canvas.html?id=canvas%20%2F%201&project=project%20%2F%201")
        self.assertEqual(out["remembered"], "pX")
        self.assertTrue(out["listUrl"].startswith("/static/canvas-list.html?"))

    def test_canvas_editor_opens_every_record_without_the_smart_handoff(self):
        # R4-34: openCanvas no longer contains the Smart handoff redirect;
        # openSmartCanvasPage is dead code; the new-canvas gate navigates a
        # freshly created Smart-kind record to canvas.html via the shared
        # normalCanvasUrl helper. The editor is the single entry.
        source = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        opening = source[source.index("async function openCanvas(id){") : source.index("function applyRemoteCanvasData", source.index("async function openCanvas(id){"))]
        self.assertNotIn("requiresLegacySmartHandoff", opening)
        self.assertNotIn("openSmartCanvasPage", opening)
        self.assertNotIn("smart-canvas.html", source)
        self.assertNotIn("openSmartCanvasPage", source)
        self.assertNotIn("legacySmartCanvasUrl(", source)
        # The new-canvas gate routes Smart-kind creations to canvas.html.
        self.assertIn("WorkbenchCanvasEntryCompatibility.normalCanvasUrl(", source)

    def test_no_smart_product_page_routing_remains_in_static_js(self):
        # R4-35: with the handoff helpers removed from the compatibility
        # module, no JS file constructs a navigation to smart-canvas.html.
        # The smart-canvas.html product page still exists on disk and is
        # reachable only by direct navigation (R4-36 retires it after the
        # Smart-capability migration is verified).
        for name in ("canvas-entry-compatibility.js", "canvas-list.js", "asset-manager.js", "canvas.js", "smart-canvas.js"):
            source = (ROOT / "static" / "js" / "workbench" / "canvas" / name).read_text(encoding="utf-8") if name == "canvas-entry-compatibility.js" else (ROOT / "static" / "js" / name).read_text(encoding="utf-8")
            self.assertNotIn("/static/smart-canvas.html", source, f"{name} must not construct a smart-canvas.html URL (R4-35)")

    def test_canvas_editor_routes_every_record_through_the_unified_open_path(self):
        # R4-34: the editor no longer branches on kind. Every record — Classic
        # or Smart — falls through to the unified render/save/selection path.
        source = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        opening = source[source.index("async function openCanvas(id){") : source.index("function applyRemoteCanvasData", source.index("async function openCanvas(id){"))]
        self.assertNotIn("requiresLegacySmartHandoff", opening)
        self.assertNotIn("(canvas.kind || 'classic') === 'smart'", opening)
