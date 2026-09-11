import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from workbench.domain.project.models import ProjectMember, ProjectRecord
from workbench.repositories.project_repository import SqliteProjectRepository
from workbench.repositories.sqlite_project_canvas_repository import CanonicalNotFoundError


class SqliteProjectRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.database = root / "workbench.sqlite3"
        self.legacy = root / "projects.json"
        self.legacy.write_text(json.dumps({"projects": [
            {"id": "default", "name": "默认项目", "order": 0, "created_at": 1000, "updated_at": 2000},
            {"id": "legacy-project", "name": "Legacy", "order": 2, "created_at": 3000, "updated_at": 4000},
        ]}), encoding="utf-8")
        self.repository = SqliteProjectRepository(self.database, legacy_projects_path=self.legacy)

    def tearDown(self):
        self.temp.cleanup()

    def test_legacy_projects_are_read_compatibly_into_sqlite_without_writing_json(self):
        before = self.legacy.read_bytes()

        projects = self.repository.list_projects()

        self.assertEqual([project.id for project in projects], ["default", "legacy-project"])
        self.assertEqual(projects[1].metadata["legacy"]["order"], 2)
        self.assertEqual(self.legacy.read_bytes(), before)
        self.assertEqual(self.repository.load_project("legacy-project").name, "Legacy")

    def test_project_crud_and_membership_stay_in_sqlite(self):
        now = datetime(2026, 9, 10, tzinfo=UTC)
        project = self.repository.create_project(ProjectRecord(
            id="new-project", name="New", workspace_id="local", created_by="actor",
            created_at=now, updated_at=now, metadata={"legacy": {"order": 4}},
        ))
        self.assertEqual(project.id, "new-project")

        updated = self.repository.update_project("new-project", name="Renamed", order=1)
        self.assertEqual((updated.name, updated.revision), ("Renamed", 2))
        self.repository.add_member(ProjectMember(
            project_id="new-project", actor_id="editor", role="editor", created_at=updated.updated_at,
        ))
        self.assertEqual(self.repository.member_role("new-project", "editor"), "editor")

        self.repository.delete_project("new-project")
        with self.assertRaises(CanonicalNotFoundError):
            self.repository.load_project("new-project")
        self.assertEqual(json.loads(self.legacy.read_text(encoding="utf-8"))["projects"][1]["name"], "Legacy")
        self.assertEqual(
            [event["event_type"] for event in self.repository._canonical.outbox_events() if event["project_id"] == "new-project"],
            ["project.created", "project.updated", "project.member_added", "project.deleted"],
        )

    def test_deleting_a_legacy_project_does_not_resurrect_it_on_compatibility_read(self):
        self.repository.list_projects()

        self.repository.delete_project("legacy-project")

        self.assertEqual([project.id for project in self.repository.list_projects()], ["default"])
        self.assertTrue(self.repository._canonical.legacy_project_excluded("legacy-project"))


if __name__ == "__main__":
    unittest.main()
