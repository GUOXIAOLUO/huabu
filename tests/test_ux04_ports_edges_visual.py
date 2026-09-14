import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "static/css/canvas.css"
TOKENS = ROOT / "static/css/workbench-canvas-tokens.css"
HTML = ROOT / "static/canvas.html"
GRAPH_INTERACTION = ROOT / "static/js/workbench/canvas/graph-interaction.js"
CANVAS_INTERACTION = ROOT / "static/js/workbench/canvas/canvas-app-interaction.js"


class UX04PortsEdgesVisualTests(unittest.TestCase):
    def test_shared_edge_presentation_class_projects_generic_states(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'),vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(GRAPH_INTERACTION))}, 'utf8'), sandbox);
const I=sandbox.window.WorkbenchCanvasGraphInteraction;
console.log(JSON.stringify({{
  idle:I.edgePresentationClass({{fromNode:{{state:'ready'}},toNode:{{state:'ready'}}}}),
  hovered:I.edgePresentationClass({{fromNode:{{state:'ready'}},toNode:{{state:'ready'}},hovered:true}}),
  selected:I.edgePresentationClass({{fromNode:{{state:'ready'}},toNode:{{state:'ready'}},selected:true}}),
  running:I.edgePresentationClass({{fromNode:{{state:'running'}},toNode:{{state:'ready'}}}}),
  legacyRunning:I.edgePresentationClass({{fromNode:{{running:true}},toNode:{{state:'ready'}}}})
}}));
"""], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {
            "idle": "link",
            "hovered": "link link-hover",
            "selected": "link link-active",
            "running": "link link-running",
            "legacyRunning": "link link-running",
        })

    def test_canvas_renders_edge_state_through_shared_owner_and_keeps_ports_accessible(self):
        source = CANVAS_INTERACTION.read_text(encoding="utf-8")
        styles = CSS.read_text(encoding="utf-8")
        tokens = TOKENS.read_text(encoding="utf-8")
        page = HTML.read_text(encoding="utf-8")
        self.assertIn("edgePresentationClass", source)
        self.assertIn("hovered:hoveredConnectionId === c.id", source)
        self.assertIn("selected:isConnectionSelected(c)", source)
        self.assertIn("graph-interaction.js?v=2026.09.14.1", page)
        self.assertIn("canvas.css?v=2026.09.11.1&ux02=2026.09.14.3&ux03=2026.09.14.2&ux04=2026.09.14.1", page)
        for selector in (
            ".link.link-hover",
            ".link.link-active",
            ".link.link-running",
            ".node.node-shell-mounted:hover > .workbench-node-shell__port",
            ".node.node-shell-mounted.selected > .workbench-node-shell__port",
            ".node.node-shell-mounted > .workbench-node-shell__port:focus-visible",
        ):
            self.assertIn(selector, styles)
        self.assertIn("--wb-edge-hover:", tokens)
        self.assertIn("--wb-edge-active:", tokens)
        self.assertIn("opacity:.38", styles)
        self.assertIn("opacity:1", styles)


if __name__ == "__main__":
    unittest.main()
