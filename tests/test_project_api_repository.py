import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main


class ProjectApiRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.canvas_dir = root / "canvases"
        self.canvas_dir.mkdir()
        self.projects = root / "projects.json"
        self.projects.write_text(json.dumps({"projects": [
            {"id": "default", "name": "默认项目", "order": 0, "created_at": 1000, "updated_at": 1000},
        ]}), encoding="utf-8")
        self.patches = [
            patch.object(main, "PROJECTS_PATH", str(self.projects)),
            patch.object(main, "WORKBENCH_DATABASE_PATH", str(root / "workbench.sqlite3")),
            patch.object(main, "CANVAS_DIR", str(self.canvas_dir)),
            patch.object(main, "WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED", False),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def test_api_project_reads_and_writes_use_sqlite_and_leave_legacy_json_unchanged(self):
        before = self.projects.read_bytes()

        listed = main.list_projects()
        created = main.new_project("新项目")
        updated = asyncio.run(main.update_project(
            created.id, main.ProjectUpdateRequest(name="重命名", order=3),
        ))

        self.assertEqual(listed[0]["name"], "默认项目")
        self.assertEqual(updated["project"]["name"], "重命名")
        self.assertEqual(main.project_repository().load_project(created.id).name, "重命名")
        self.assertEqual(self.projects.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
