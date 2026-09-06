import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "canvas"


class LegacyCanvasFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.canvas_dir = Path(self.temp.name) / "canvases"
        self.canvas_dir.mkdir(parents=True)
        self.canvas_patch = patch.object(main, "CANVAS_DIR", str(self.canvas_dir))
        self.routing_patch = patch.object(main, "WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED", False)
        self.database_patch = patch.object(main, "WORKBENCH_DATABASE_PATH", str(Path(self.temp.name) / "workbench.sqlite3"))
        self.canvas_patch.start()
        self.routing_patch.start()
        self.database_patch.start()

    def tearDown(self):
        self.routing_patch.stop()
        self.canvas_patch.stop()
        self.database_patch.stop()
        self.temp.cleanup()

    def fixture(self, name):
        return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))

    def write_fixture(self, record):
        (self.canvas_dir / f"{record['id']}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def test_classic_fixture_covers_current_node_families(self):
        record = self.fixture("classic-v0.json")
        node_types = {node["type"] for node in record["nodes"]}
        self.assertTrue({
            "image", "prompt", "loop", "group", "promptGroup", "llm", "generator",
            "midjourney", "msgen", "video", "minimax", "rh", "comfy", "ltxDirector", "output",
        }.issubset(node_types))
        self.assertEqual(record["kind"], "classic")
        self.assertTrue(record["connections"])

    def test_smart_fixture_covers_current_node_families(self):
        record = self.fixture("smart-v0.json")
        node_types = {node["type"] for node in record["nodes"]}
        self.assertEqual(
            node_types,
            {"smart-image", "smart-prompt", "smart-loop", "smart-minimax", "smart-group"},
        )
        self.assertEqual(record["kind"], "smart")

    def test_fixtures_cover_graph_and_workspace_contracts(self):
        classic = self.fixture("classic-v0.json")
        smart = self.fixture("smart-v0.json")

        self.assertEqual(classic["project"], "fixture-project")
        self.assertEqual(classic["viewport"], {"x": -50, "y": 80, "scale": 0.8})
        self.assertEqual(classic["settings"], {"fixture": True})
        self.assertEqual(classic["logs"][0]["outputs"], ["/assets/output/fixture.png"])
        self.assertEqual(
            next(node for node in classic["nodes"] if node["id"] == "group-1")["items"],
            ["image-1", "prompt-1"],
        )
        self.assertEqual(
            {(connection["from"], connection["to"]) for connection in classic["connections"]},
            {("image-1", "generator-1"), ("prompt-1", "generator-1"), ("generator-1", "output-1")},
        )
        self.assertEqual(
            next(node for node in smart["nodes"] if node["id"] == "smart-group-1")["items"],
            ["smart-image-1", "smart-prompt-1"],
        )
        self.assertEqual(smart["connections"][0]["kind"], "flow")

    def test_unknown_fixture_keeps_historical_type_and_extensions(self):
        record = self.fixture("legacy-unknown-fields-v0.json")
        node = record["nodes"][0]
        self.assertEqual(node["type"], "workflow-custom")
        self.assertEqual(node["vendor_extension"]["opaque"], [1, 2, 3])
        self.assertEqual(record["settings"]["future_setting"], {"enabled": True})

    def test_load_and_save_preserves_unknown_fields(self):
        original = self.fixture("legacy-unknown-fields-v0.json")
        self.write_fixture(original)

        loaded = main.load_canvas(original["id"])
        self.assertEqual(loaded["top_level_extension"], original["top_level_extension"])
        self.assertEqual(loaded["nodes"][0]["vendor_extension"], original["nodes"][0]["vendor_extension"])

        main.save_canvas(loaded)
        reloaded = main.load_canvas(original["id"])
        self.assertEqual(reloaded["top_level_extension"], original["top_level_extension"])
        self.assertEqual(reloaded["nodes"][0]["future_field"], "preserve-me")
        self.assertGreater(reloaded["updated_at"], original["updated_at"])

    def test_classic_fixture_round_trips_every_node_family_without_schema_loss(self):
        original = self.fixture("classic-v0.json")
        self.write_fixture(original)

        loaded = main.load_canvas(original["id"])
        main.save_canvas(loaded)
        reloaded = main.load_canvas(original["id"])

        self.assertEqual(reloaded["nodes"], original["nodes"])
        self.assertEqual(reloaded["connections"], original["connections"])
        self.assertEqual(reloaded["settings"], original["settings"])
