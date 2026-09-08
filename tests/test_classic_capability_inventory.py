"""Source-contract tests for the R4-31 Classic capability inventory.

The inventory (`docs/plans/R4_CLASSIC_CAPABILITY_INVENTORY.md`) classifies every
Classic-only, product-relevant capability before the Classic runtime is
retired. These tests anchor that classification to the real source: every
inventoried capability must carry a valid disposition, a target owner, and
evidence grounded in the declared owner source. They also pin the exact R4-38
owner mapping, reject non-delegating same-name bodies in `static/js/canvas.js`,
and cover the card's In-Scope areas and disposition vocabulary so the inventory
cannot silently drift into fiction.
"""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs" / "plans" / "R4_CLASSIC_CAPABILITY_INVENTORY.md"
CLASSIC_SOURCE = ROOT / "static" / "js" / "canvas.js"

ALLOWED_DISPOSITIONS = {"KEEP", "MIGRATE", "MIGRATED", "COMPAT", "REMOVE", "DEFER-R8"}

# The card's In-Scope areas, expressed as required category substrings.
REQUIRED_CATEGORY_MARKERS = (
    "Provider cards",
    "Comfy",
    "RunningHub",
    "MiniMax",
    "LTX",
    "Video",
    "Output",
    "Asset",
    "Cascade",
)

EXPECTED_CAPABILITY_OWNERS = {
    "provider-node-creation": "static/js/workbench/canvas/classic-node-factories.js",
    "provider-card-body": "static/js/workbench/canvas/classic-card-body-renderer.js",
    "comfy-controls": "static/js/workbench/canvas/classic-comfy-controls.js",
    "comfy-result-normalization": "static/js/workbench/canvas/classic-executor-runtime.js",
    "runninghub": "static/js/workbench/canvas/classic-runninghub-controls.js",
    "minimax": "static/js/workbench/canvas/classic-minimax-controls.js",
    "ltx": "static/js/workbench/canvas/classic-ltx-controls.js",
    "video-node-creation": "static/js/workbench/canvas/classic-node-factories.js",
    "video-card-body": "static/js/workbench/canvas/classic-video-card-body.js",
    "video-provider-params": "static/js/workbench/canvas/classic-video-provider-params.js",
    "output-node-creation": "static/js/workbench/canvas/classic-node-factories.js",
    "output-grid-renderer": "static/js/workbench/canvas/classic-output-grid.js",
    "generation-log": "static/js/workbench/canvas/classic-generation-log.js",
    "asset-library": "static/js/workbench/canvas/classic-asset-runtime.js",
    "cascade": "static/js/workbench/canvas/classic-cascade-orchestrator.js",
}


def _manifest() -> dict:
    text = INVENTORY.read_text(encoding="utf-8")
    # The machine-readable block is the last fenced JSON block in the doc.
    blocks = re.findall(r"```json\n(.*?)\n```", text, flags=re.DOTALL)
    if not blocks:
        raise AssertionError("inventory document has no ```json evidence manifest block")
    return json.loads(blocks[-1])


class ClassicCapabilityInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = _manifest()
        cls.source = CLASSIC_SOURCE.read_text(encoding="utf-8")

    def test_manifest_points_at_the_real_classic_source(self):
        self.assertEqual(self.manifest.get("source"), "static/js/canvas.js")
        self.assertTrue(CLASSIC_SOURCE.exists(), "inventory source file must exist")

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
        # Capabilities may declare an `evidence_target` pointing at a
        # shared seam module file. Defaults to canvas.js so legacy
        # MIGRATE / COMPAT / DEFER-R8 entries that still live on the
        # page-side don't need to migrate the manifest schema.
        for capability in capabilities:
            target_rel = capability.get("evidence_target", "static/js/canvas.js")
            target_path = ROOT / target_rel
            self.assertTrue(target_path.exists(),
                f"evidence_target file does not exist for capability {capability['id']!r}: {target_rel}")
            target_source = target_path.read_text(encoding="utf-8")
            for name in capability.get("evidence", []):
                with self.subTest(capability=capability.get("id"), evidence=name, target=target_rel):
                    self.assertIn(
                        name,
                        target_source,
                        f"evidence function {name!r} for {capability['id']!r} is not present in {target_rel}",
                    )

    def test_inventory_covers_all_in_scope_areas(self):
        categories = self.manifest.get("categories", [])
        joined = "\n".join(categories)
        for marker in REQUIRED_CATEGORY_MARKERS:
            self.assertIn(marker, joined, f"inventory must cover the In-Scope area {marker!r}")

    def test_classification_is_meaningful_across_dispositions(self):
        # A pure characterization card must actually decide, not default everything.
        dispositions = {capability["disposition"] for capability in self.manifest.get("capabilities", [])}
        # COMPAT + DEFER-R8 are the foundational invariants — COMPAT is the
        # R4-wide "kept as compat until R8 replaces it" disposition, DEFER-R8
        # is the R8 governance assertion. An inventory without either would
        # be missing the R8 boundary.
        self.assertIn("COMPAT", dispositions)
        self.assertIn("DEFER-R8", dispositions)
        # MIGRATE / MIGRATED are R4-state — they may legitimately both be
        # zero once every MIGRATE-eligible capability has been promoted by
        # an R4-38 wave. When MIGRATE rows are present they must coexist
        # with at least one MIGRATED row so the inventory still drives
        # forward work rather than only recording completions.
        migrated = {c["id"] for c in self.manifest.get("capabilities", []) if c["disposition"] == "MIGRATED"}
        migrate = {c["id"] for c in self.manifest.get("capabilities", []) if c["disposition"] == "MIGRATE"}
        if migrate:
            self.assertTrue(migrated, "MIGRATE rows must coexist with at least one MIGRATED row")

    def test_no_duplicate_capability_ids(self):
        ids = [capability["id"] for capability in self.manifest.get("capabilities", [])]
        self.assertEqual(len(ids), len(set(ids)), "capability ids must be unique")
    def test_no_capability_body_is_grounded_in_the_monolith(self):
        # R4-38 Wave 16, Owner-approved structural re-baseline (2026-09-07):
        # the bootstrap-only contract is structural — every R4-31 capability
        # row must ground its evidence OUTSIDE static/js/canvas.js (in a
        # bounded compat seam module or a unified boundary). canvas.js keeps
        # only dispatch, wiring, state access and bootstrap sequencing.
        capabilities = self.manifest.get("capabilities", [])
        actual_owners = {
            capability["id"]: capability.get("evidence_target", "static/js/canvas.js")
            for capability in capabilities
        }
        self.assertEqual(
            actual_owners,
            EXPECTED_CAPABILITY_OWNERS,
            "R4-38 ownership is a pinned source contract, not a freely movable manifest pointer",
        )
        for capability in capabilities:
            target = capability.get("evidence_target", "static/js/canvas.js")
            with self.subTest(capability=capability.get("id"), target=target):
                self.assertNotEqual(
                    target, "static/js/canvas.js",
                    f"capability {capability['id']!r} still grounds its body in the monolith; "
                    "move it behind a bounded compat seam before R4-38 can stay closed")
                self.assertTrue(
                    (ROOT / target).exists(),
                    f"evidence_target missing for {capability['id']!r}: {target}")

                # If an evidence marker names a function, canvas.js may retain
                # only a one-line seam delegator for caller compatibility.  A
                # multiline function declaration under the old name is still
                # an owned body and must keep this card open.
                for evidence in capability.get("evidence", []):
                    match = re.fullmatch(r"([A-Za-z_$][\w$]*)(?:\()?", evidence)
                    if not match:
                        continue
                    name = match.group(1)
                    declarations = list(re.finditer(
                        rf"^(?:async\s+)?function\s+{re.escape(name)}\([^\n]*",
                        self.source,
                        flags=re.MULTILINE,
                    ))
                    for declaration in declarations:
                        declaration_source = self.source[declaration.start():]
                        self.assertIsNotNone(
                            re.match(
                                rf"^(?:async\s+)?function\s+{re.escape(name)}\([^\n]*\)\s*\{{\s*"
                                rf"(?:return\s+)?ensureClassic[A-Za-z0-9_$]+\(\)\."
                                rf"[A-Za-z0-9_$]+\([^;]*\);?\s*\}}",
                                declaration_source,
                            ),
                            f"canvas.js still owns a non-delegating body for {name!r}",
                        )

if __name__ == "__main__":
    unittest.main()
