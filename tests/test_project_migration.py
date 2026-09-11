import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from workbench.application.project_migration import ProjectMigrationService
from workbench.repositories.project_repository import SqliteProjectRepository


class ProjectMigrationTests(unittest.TestCase):
    def test_migration_compares_counts_and_preserves_unknown_fields_before_cutover(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = SqliteProjectRepository(Path(directory) / "workbench.sqlite3")
            projects = [{
                "id": "default", "name": "Default", "order": 0,
                "members": [{"actor_id": "local-workspace-actor", "role": "owner"}],
                "future_field": {"preserve": True},
            }]
            service = ProjectMigrationService(repository)

            report = service.migrate_and_compare(projects, now=datetime.now(UTC))

            self.assertEqual((report.source_project_count, report.sqlite_project_count), (1, 1))
            self.assertEqual((report.source_member_count, report.sqlite_member_count), (1, 1))
            self.assertEqual(report.differences, ())
            self.assertEqual(repository.project_authority(), "legacy_json")
            self.assertEqual(repository.list_canonical_projects()[0].metadata["legacy"]["source"]["future_field"], {"preserve": True})

    def test_cutover_requires_clean_comparison_and_stops_legacy_compat_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "projects.json"
            repository = SqliteProjectRepository(root / "workbench.sqlite3", legacy_projects_path=legacy)
            projects = [{"id": "default", "name": "Default", "order": 0}]
            service = ProjectMigrationService(repository)
            report = service.migrate_and_compare(projects, now=datetime.now(UTC))
            service.activate_after_compare(projects, report)

            legacy.write_text('{"projects":[{"id":"default","name":"Changed"}]}', encoding="utf-8")

            self.assertEqual(repository.project_authority(), "sqlite")
            self.assertEqual(repository.load_project("default").name, "Default")

    def test_cutover_is_blocked_when_comparison_drifts(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = SqliteProjectRepository(Path(directory) / "workbench.sqlite3")
            projects = [{"id": "default", "name": "Default", "order": 0}]
            service = ProjectMigrationService(repository)
            report = service.migrate_and_compare(projects, now=datetime.now(UTC))
            drifted = [{"id": "default", "name": "Drift", "order": 0}]

            with self.assertRaises(ValueError):
                service.activate_after_compare(drifted, report)
            self.assertEqual(repository.project_authority(), "legacy_json")

    def test_member_role_drift_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = SqliteProjectRepository(Path(directory) / "workbench.sqlite3")
            projects = [{"id": "default", "name": "Default", "members": [{"actor_id": "local-workspace-actor", "role": "owner"}]}]
            service = ProjectMigrationService(repository)
            service.migrate_and_compare(projects, now=datetime.now(UTC))

            drifted = [{"id": "default", "name": "Default", "members": [{"actor_id": "local-workspace-actor", "role": "viewer"}]}]
            self.assertIn("default.members", repository.compare_legacy_projects(drifted))


if __name__ == "__main__":
    unittest.main()
