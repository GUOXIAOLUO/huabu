import pathlib
import unittest


ROOT = pathlib.Path(__file__).parents[1]
CARD = ROOT / "docs/tasks/backlog/UX-15-browser-acceptance-classic-responsibility-gate.md"


class UX15BrowserAcceptanceGateTests(unittest.TestCase):
    def test_current_task_is_the_only_active_ux_card(self):
        pointer = (ROOT / "AGENT_NEXT_TASK.md").read_text()
        self.assertIn("Active Task: `UX-15`", pointer)
        self.assertIn("Status: `ACTIVE — implementation complete; independent Review pending`", pointer)
        for number in range(1, 15):
            card = next(ROOT.glob(f"docs/tasks/done/UX-{number:02d}-*.md"), None)
            self.assertIsNotNone(card, f"UX-{number:02d} must be archived before the UX-15 gate")
        self.assertNotIn("UX-15", "\n".join(path.name for path in (ROOT / "docs/tasks/done").glob("UX-15-*.md")))

    def test_unified_canvas_loader_has_no_second_canvas_page_or_monolith(self):
        page = (ROOT / "static/canvas.html").read_text()
        self.assertIn("canvas-app-bootstrap.js", page)
        self.assertNotIn("static/js/canvas.js", page)
        self.assertFalse((ROOT / "static/smart-canvas.html").exists())
        self.assertFalse((ROOT / "static/js/smart-canvas.js").exists())
        self.assertFalse((ROOT / "static/css/smart-canvas.css").exists())

    def test_gate_card_records_real_acceptance_and_bounded_compatibility(self):
        card = CARD.read_text()
        self.assertIn("Preview", card)
        self.assertIn("Compare", card)
        self.assertIn("Collection", card)
        self.assertIn("Materialization", card)
        self.assertIn("bounded compatibility", card)
        self.assertIn("No blanket deletion", card)

    def test_gate_card_records_checklist_state_and_reference_evidence(self):
        card = CARD.read_text()
        for evidence in (
            "REF-001",
            "REF-017",
            "REF-026",
            "REF-031",
            "REF-035",
            "REF-301",
            "default",
            "hover",
            "selected",
            "editing",
            "running",
            "success",
            "error",
        ):
            self.assertIn(evidence, card, f"UX-15 evidence must record {evidence}")


if __name__ == "__main__":
    unittest.main()
