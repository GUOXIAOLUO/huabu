import asyncio
from io import BytesIO
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import main


class RepositoryBaselineTests(unittest.TestCase):
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

    def write_canvas(self, canvas_id, updated_at=100):
        value = {
            "id": canvas_id,
            "title": "baseline",
            "icon": "layers",
            "kind": "classic",
            "nodes": [],
            "connections": [],
            "viewport": {"x": 0, "y": 0, "scale": 1},
            "logs": [],
            "settings": {},
            "updated_at": updated_at,
        }
        (self.canvas_dir / f"{canvas_id}.json").write_text(json.dumps(value), encoding="utf-8")
        return value

    def test_save_canvas_advances_revision_when_clock_does_not(self):
        canvas = self.write_canvas("revision", updated_at=500)
        with patch.object(main, "now_ms", return_value=500):
            main.save_canvas(canvas)
        self.assertEqual(canvas["updated_at"], 501)

    def test_stale_save_is_rejected_without_mutating_canvas(self):
        self.write_canvas("stale", updated_at=500)
        request = main.CanvasSaveRequest(
            title="stale overwrite",
            nodes=[],
            connections=[],
            viewport={"x": 0, "y": 0, "scale": 1},
            logs=[],
            settings={},
            base_updated_at=499,
        )
        with self.assertRaises(main.HTTPException) as raised:
            asyncio.run(main.update_canvas("stale", request))
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(main.load_canvas("stale")["title"], "baseline")

    def test_soft_delete_then_restore_keeps_canvas_record(self):
        self.write_canvas("trash")
        asyncio.run(main.delete_canvas("trash"))
        with self.assertRaises(main.HTTPException) as raised:
            main.load_canvas("trash")
        self.assertEqual(raised.exception.status_code, 404)

        restored = asyncio.run(main.restore_canvas("trash"))
        self.assertEqual(restored["canvas"]["id"], "trash")
        self.assertEqual(main.load_canvas("trash")["id"], "trash")

    def test_purge_removes_soft_deleted_canvas_file(self):
        self.write_canvas("purge-me")
        asyncio.run(main.delete_canvas("purge-me"))
        self.assertTrue((self.canvas_dir / "purge-me.json").exists())

        result = asyncio.run(main.purge_canvas("purge-me"))

        self.assertEqual(result, {"ok": True})
        self.assertFalse((self.canvas_dir / "purge-me.json").exists())

    def test_workflow_archive_round_trip_preserves_legacy_graph_fields(self):
        nodes = [{"id": "legacy-1", "type": "workflow-custom", "future_field": {"v": 1}}]
        connections = [{"id": "edge-1", "from": "legacy-1", "to": "legacy-2", "kind": "flow"}]
        archive, metadata = main.build_canvas_workflow_archive(
            main.CanvasWorkflowExportRequest(
                nodes=nodes,
                connections=connections,
                include_resources=False,
            )
        )

        self.assertEqual(metadata, {"resources": [], "node_count": 1, "connection_count": 1})
        with zipfile.ZipFile(BytesIO(archive)) as package:
            self.assertEqual(package.namelist(), ["workflow.json"])
            workflow = json.loads(package.read("workflow.json"))
        self.assertEqual(workflow["nodes"], nodes)
        self.assertEqual(workflow["connections"], connections)

        imported = asyncio.run(
            main.import_canvas_workflow(main.UploadFile(filename="legacy-workflow.zip", file=BytesIO(archive)))
        )
        self.assertEqual(imported["nodes"], nodes)
        self.assertEqual(imported["connections"], connections)
