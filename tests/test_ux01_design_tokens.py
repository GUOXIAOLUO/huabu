import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "static/css/workbench-canvas-tokens.css"
CANVAS_CSS = ROOT / "static/css/canvas.css"
CANVAS_HTML = ROOT / "static/canvas.html"
RECORDS_JS = ROOT / "static/js/workbench/canvas/canvas-app-records.js"
MEDIA_EDITOR_JS = ROOT / "static/js/workbench/canvas/canvas-app-media-editor.js"


class UX01DesignTokenTests(unittest.TestCase):
    def test_canvas_loads_shared_tokens_before_component_styles(self):
        page = CANVAS_HTML.read_text(encoding="utf-8")
        token_link = '<link rel="stylesheet" href="/static/css/workbench-canvas-tokens.css?v=2026.09.14.2">'
        canvas_link = '<link rel="stylesheet" href="/static/css/canvas.css?v=2026.09.11.1&ux02=2026.09.14.3&ux03=2026.09.14.2&ux04=2026.09.14.1">'
        self.assertIn(token_link, page)
        self.assertLess(page.index(token_link), page.index(canvas_link))

    def test_token_layer_owns_canvas_baseline_and_dark_theme(self):
        tokens = TOKENS.read_text(encoding="utf-8")
        for name, value in {
            "--wb-canvas-bg": "#f8fafc",
            "--wb-surface": "#ffffff",
            "--wb-border": "#e8edf3",
            "--wb-selection": "#2563eb",
            "--wb-edge": "#d9e1ea",
            "--wb-radius-card": "16px",
            "--wb-shadow-low": "rgba(15,23,42,.08)",
        }.items():
            self.assertRegex(tokens, rf"{re.escape(name)}\s*:\s*{re.escape(value)}")
        self.assertIn(".theme-dark", tokens)
        self.assertIn("--wb-canvas-bg: #0b1020", tokens)

    def test_canvas_root_shell_consumes_semantic_tokens_without_duplicate_root_owner(self):
        tokens = TOKENS.read_text(encoding="utf-8")
        canvas_css = CANVAS_CSS.read_text(encoding="utf-8")
        self.assertIn("background:var(--wb-canvas-bg)", canvas_css)
        self.assertIn("background:var(--wb-surface-panel)", canvas_css)
        self.assertNotRegex(canvas_css, r"^:root\s*\{", re.MULTILINE)
        self.assertNotRegex(canvas_css, r"^\.theme-dark\s*\{", re.MULTILINE)
        self.assertIn("--wb-canvas-bg", tokens)

    def test_canvas_bootstrap_preserves_late_media_editor_owner(self):
        records = RECORDS_JS.read_text(encoding="utf-8")
        media_editor = MEDIA_EDITOR_JS.read_text(encoding="utf-8")
        page = CANVAS_HTML.read_text(encoding="utf-8")
        self.assertIn("event => beginEditDraw(event)", records)
        self.assertIn("event => moveEditDraw(event)", records)
        self.assertIn("event => beginEditText(event)", records)
        self.assertIn("event => moveEditText(event)", records)
        self.assertIn("event => syncSelectedEditTextStyleFromBrush(event)", records)
        self.assertIn("typeof window.canvasInspectorPanel.render !== 'function'", media_editor)
        self.assertIn("canvas-app-records.js?v=2026.09.14.5", page)
        self.assertIn("canvas-app-media-editor.js?v=2026.09.15.1", page)


if __name__ == "__main__":
    unittest.main()
