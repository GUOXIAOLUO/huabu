import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main


class CanvasOpenSemanticsTests(unittest.TestCase):
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

    def test_legacy_touch_route_does_not_change_canvas_revision(self):
        created = main.new_canvas("open should be read-only", kind="classic")
        before = main.load_canvas(created["id"])

        response = asyncio.run(main.touch_canvas(created["id"]))
        after = main.load_canvas(created["id"])

        self.assertEqual(response["updated_at"], before["updated_at"])
        self.assertEqual(response["canvas"]["updated_at"], before["updated_at"])
        self.assertEqual(after["updated_at"], before["updated_at"])


if __name__ == "__main__":
    unittest.main()
