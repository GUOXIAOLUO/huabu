"""Source-contract tests for the R4-27 Smart capability inventory.

The inventory (`docs/plans/R4_SMART_CAPABILITY_INVENTORY.md`) classifies every
Smart-only, product-relevant capability before the Smart runtime is retired.
These tests anchor that classification to the real source: every inventoried
capability must carry a valid disposition, a target owner, and evidence that
actually names functions present in `static/js/smart-canvas.js`. They also
pin the coverage of the card's In-Scope areas and the disposition vocabulary,
so the inventory cannot silently drift into fiction.
"""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs" / "plans" / "R4_SMART_CAPABILITY_INVENTORY.md"
SMART_SOURCE = ROOT / "static" / "js" / "smart-canvas.js"

ALLOWED_DISPOSITIONS = {"KEEP", "MIGRATE", "COMPAT", "REMOVE", "DEFER-R8"}

# The card's In-Scope areas, expressed as required category substrings.
REQUIRED_CATEGORY_MARKERS = (
    "Composer",
    "Prompt presets",
    "Asset",
    "Media edit",
    "Smart group",
    "Cascade/execution",
    "Provider/media/MiniMax",
)


def _manifest() -> dict:
    text = INVENTORY.read_text(encoding="utf-8")
    # The machine-readable block is the last fenced JSON block in the doc.
    blocks = re.findall(r"```json\n(.*?)\n```", text, flags=re.DOTALL)
    if not blocks:
        raise AssertionError("inventory document has no ```json evidence manifest block")
    return json.loads(blocks[-1])


class SmartCapabilityInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = _manifest()
        cls.source = SMART_SOURCE.read_text(encoding="utf-8")

    def test_manifest_points_at_the_real_smart_source(self):
        self.assertEqual(self.manifest.get("source"), "static/js/smart-canvas.js")
        self.assertTrue(SMART_SOURCE.exists(), "inventory source file must exist")

    def test_every_capability_has_a_valid_disposition_and_owner(self):
        capabilities = self.manifest.get("capabilities", [])
        self.assertGreater(len(capabilities), 0, "inventory must not be empty")
        categories = set(self.manifest.get("categories", []))
        for capability in capabilities:
            with self.subTest(capability=capability.get("id")):
                self.assertIn(capability["disposition"], ALLOWED_DISPOSITIONS)
                self.assertTrue(str(capability.get("target_owner") or "").strip(), "target owner required")
                self.assertIn(capability["category"], categories)

    def test_every_capability_evidence_is_grounded_in_source(self):
        capabilities = self.manifest.get("capabilities", [])
        for capability in capabilities:
            for name in capability.get("evidence", []):
                with self.subTest(capability=capability.get("id"), evidence=name):
                    self.assertIn(
                        name,
                        self.source,
                        f"evidence function {name!r} for {capability['id']!r} is not present in smart-canvas.js",
                    )

    def test_inventory_covers_all_in_scope_areas(self):
        categories = self.manifest.get("categories", [])
        joined = "\n".join(categories)
        for marker in REQUIRED_CATEGORY_MARKERS:
            self.assertIn(marker, joined, f"inventory must cover the In-Scope area {marker!r}")

    def test_classification_is_meaningful_across_dispositions(self):
        # A pure characterization card must actually decide, not default everything.
        dispositions = {capability["disposition"] for capability in self.manifest.get("capabilities", [])}
        self.assertIn("MIGRATE", dispositions)
        self.assertIn("COMPAT", dispositions)
        self.assertIn("DEFER-R8", dispositions)

    def test_no_duplicate_capability_ids(self):
        ids = [capability["id"] for capability in self.manifest.get("capabilities", [])]
        self.assertEqual(len(ids), len(set(ids)), "capability ids must be unique")


if __name__ == "__main__":
    unittest.main()
