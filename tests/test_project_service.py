import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from workbench.application.project_service import ProjectService, ProjectServiceError
from workbench.repositories.project_repository import SqliteProjectRepository


class ProjectServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repository = SqliteProjectRepository(Path(self.temp.name) / "workbench.sqlite3")
        self.now = datetime(2026, 9, 10, tzinfo=UTC)
        self.moved = []
        self.service = ProjectService(
            self.repository,
            canvas_reassigner=self._reassign,
            clock=lambda: self.now,
        )

    def tearDown(self):
        self.temp.cleanup()

    def _reassign(self, *, source_project_id, target_project_id):
        self.moved.append((source_project_id, target_project_id))
        return 3

    def test_lifecycle_uses_repository_and_preserves_archive_compatibility(self):
        created = self.service.create("  客户项目  ")
        updated = self.service.update(created.id, name="重命名", order=2)
        archived = self.service.archive(created.id)

        self.assertEqual((created.name, updated.name, updated.revision), ("客户项目", "重命名", 2))
        self.assertEqual(archived.moved_canvas_count, 3)
        self.assertEqual(self.moved, [(created.id, "default")])

    def test_service_owns_basic_validation(self):
        with self.assertRaises(ProjectServiceError) as raised:
            self.service.update("missing", name="")
        self.assertEqual(raised.exception.code, "not_found")

        with self.assertRaises(ProjectServiceError) as raised:
            self.service.archive("default")
        self.assertEqual(raised.exception.code, "invalid_request")


if __name__ == "__main__":
    unittest.main()
