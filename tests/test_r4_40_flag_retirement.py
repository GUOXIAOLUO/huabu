"""Behavior and boundary checks for the R4-40 flag retirement."""

import re
import unittest
from pathlib import Path

from tests.canvas_app_source import read_canvas_app_source


ROOT = Path(__file__).resolve().parents[1]
RETIRED_FLAGS = (
    "unified_canvas",
    "node_shell",
    "media_renderer",
    "legacy_renderer",
    "semantic_zoom",
    "screen_space_controls",
)


class R440FlagRetirementTests(unittest.TestCase):
    def test_retired_flags_cannot_select_a_canvas_runtime_branch(self):
        source = read_canvas_app_source(ROOT)
        for flag in RETIRED_FLAGS:
            with self.subTest(flag=flag):
                self.assertNotRegex(source, rf"(?:get|has)\(['\"]{flag}['\"]\)")

        state = (ROOT / "static/js/workbench/canvas/canvas-app-state.js").read_text(encoding="utf-8")
        media = (ROOT / "static/js/workbench/canvas/canvas-app-media-editor.js").read_text(encoding="utf-8")
        self.assertIn("const canvasUnifiedRuntimeEnabled = Boolean(window.WorkbenchCanvasRuntime);", state)
        self.assertIn("return canvasNodeShellBaseEnabled()", media)

    def test_performance_harness_does_not_forward_retired_flags(self):
        harness = (ROOT / "static/canvas-performance-harness.html").read_text(encoding="utf-8")
        self.assertNotIn("rendererFlags", harness)
        self.assertNotIn("rendererQuery", harness)
        self.assertIn("frame.src = `/static/canvas.html?id=${encodeURIComponent(canvasId)}&benchmark=1&benchmark_nonce=${benchmarkNonce}`;", harness)
        self.assertIn("'renderer_flags=stable'", harness)

    def test_canvas_html_declares_one_stable_script_path(self):
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        for flag in RETIRED_FLAGS:
            with self.subTest(flag=flag):
                self.assertNotIn(f"{flag}=", page)
        scripts = re.findall(r'<script src="(/static/js/workbench/canvas/canvas-app-[^"]+)\?v=[^"]+"></script>', page)
        self.assertEqual(len(scripts), 9)
        self.assertEqual(scripts[-1], "/static/js/workbench/canvas/canvas-app-bootstrap.js")


if __name__ == "__main__":
    unittest.main()
