import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "static/css/workbench-canvas-tokens.css"
CANVAS_CSS = ROOT / "static/css/canvas.css"
CANVAS_HTML = ROOT / "static/canvas.html"
INTERACTION = ROOT / "static/js/workbench/canvas/canvas-app-interaction.js"


class UX02CanvasSurfaceTests(unittest.TestCase):
    def test_surface_uses_shared_tokens_for_background_and_persistent_chrome(self):
        tokens = TOKENS.read_text(encoding="utf-8")
        styles = CANVAS_CSS.read_text(encoding="utf-8")
        page = CANVAS_HTML.read_text(encoding="utf-8")
        for name in (
            "--wb-canvas-grid-size",
            "--wb-canvas-dot-size",
            "--wb-shell-inset",
            "--wb-control-height",
            "--wb-control-radius",
        ):
            self.assertRegex(tokens, rf"{re.escape(name)}\s*:")
        self.assertIn("background-color:var(--wb-canvas-bg)", styles)
        self.assertIn("background-size:var(--wb-canvas-grid-size) var(--wb-canvas-grid-size)", styles)
        self.assertIn("top:var(--wb-shell-top)", styles)
        self.assertIn("right:var(--wb-shell-inset)", styles)
        self.assertIn("height:var(--wb-control-height)", styles)
        self.assertIn("workbench-canvas-tokens.css?v=2026.09.14.2", page)
        self.assertIn('id="canvasSurfaceControls"', page)
        self.assertIn('id="canvasZoomOutBtn"', page)
        self.assertIn('id="canvasFitBtn"', page)
        self.assertIn('id="canvasZoomInBtn"', page)

    def test_surface_keeps_existing_single_runtime_interaction_owners(self):
        page = CANVAS_HTML.read_text(encoding="utf-8")
        interaction = INTERACTION.read_text(encoding="utf-8")
        self.assertEqual(page.count("id=\"board\""), 1)
        self.assertEqual(page.count("id=\"world\""), 1)
        self.assertIn("board.onwheel", interaction)
        self.assertIn("startBoardPan", interaction)
        self.assertIn("ensureCanvasViewportController().zoomAt", interaction)
        self.assertIn("ensureMinimapController", interaction)
        self.assertIn("adjustCanvasViewportScale(.88)", interaction)
        self.assertIn("fitAllNodesViewport()", interaction)
        self.assertIn("adjustCanvasViewportScale(1.14)", interaction)


if __name__ == "__main__":
    unittest.main()
