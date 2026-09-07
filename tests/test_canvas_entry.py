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

    def test_entry_compatibility_keeps_one_normal_entry_and_scopes_smart_handoff(self):
        source = ENTRY_COMPATIBILITY.read_text(encoding="utf-8")
        self.assertNotIn("fetch(", source)
        self.assertNotIn("localStorage", source)
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}, URLSearchParams}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ENTRY_COMPATIBILITY))}, 'utf8'), sandbox);
const E=sandbox.window.WorkbenchCanvasEntryCompatibility;
console.log(JSON.stringify({{
  normal:E.normalCanvasUrl('canvas / 1', 'project / 1'),
  smart:E.legacySmartCanvasUrl('canvas / 1'),
  retained:E.legacySmartCanvasUrl('canvas / 1', '?id=obsolete&unified_canvas=0&node_shell=0'),
  historical:E.requiresLegacySmartHandoff({{kind:'smart'}}),
  normalRecord:E.requiresLegacySmartHandoff({{kind:'classic'}}),
  missingKind:E.requiresLegacySmartHandoff({{}}),
}}));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "normal": "/static/canvas.html?id=canvas%20%2F%201&project=project%20%2F%201",
            "smart": "/static/smart-canvas.html?id=canvas%20%2F%201",
            "retained": "/static/smart-canvas.html?id=canvas%20%2F%201&unified_canvas=0&node_shell=0",
            "historical": True,
            "normalRecord": False,
            "missingKind": False,
        })

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

    def test_product_openers_confine_smart_page_urls_to_the_compatibility_boundary(self):
        compatibility = ENTRY_COMPATIBILITY.read_text(encoding="utf-8")
        self.assertIn("/static/smart-canvas.html", compatibility)
        for name in ("canvas-list.js", "asset-manager.js", "canvas.js"):
            source = (ROOT / "static" / "js" / name).read_text(encoding="utf-8")
            self.assertNotIn("/static/smart-canvas.html", source)

    def test_canvas_editor_routes_every_record_through_the_unified_open_path(self):
        # R4-34: the editor no longer branches on kind. Every record — Classic
        # or Smart — falls through to the unified render/save/selection path.
        source = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        opening = source[source.index("async function openCanvas(id){") : source.index("function applyRemoteCanvasData", source.index("async function openCanvas(id){"))]
        self.assertNotIn("requiresLegacySmartHandoff", opening)
        self.assertNotIn("(canvas.kind || 'classic') === 'smart'", opening)
