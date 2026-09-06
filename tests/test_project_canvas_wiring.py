import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main
from workbench.application.project_canvas_migration import ProjectCanvasMigrationService
from workbench.repositories.legacy_json_canvas_repository import LegacyJsonCanvasRepository
from workbench.repositories.sqlite_canvas_compatibility_repository import SqliteCanvasCompatibilityRepository


class ProjectCanvasWiringTests(unittest.TestCase):
    def test_main_wires_the_r3_repository_without_replacing_legacy_canvas_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "workbench.sqlite3"
            with patch.object(main, "WORKBENCH_DATABASE_PATH", str(database)):
                canonical = main.canonical_project_canvas_repository()
                migration = main.project_canvas_migration_service()

            self.assertEqual(canonical.canvas_authority(), "legacy_json")
            self.assertTrue(database.exists())
            self.assertIsInstance(migration, ProjectCanvasMigrationService)

    def test_r4_routing_requires_both_feature_flag_and_sqlite_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "workbench.sqlite3"
            with patch.object(main, "WORKBENCH_DATABASE_PATH", str(database)), patch.object(main, "WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED", False):
                self.assertIsInstance(main.canvas_repository(), LegacyJsonCanvasRepository)
                self.assertFalse(database.exists())
            with patch.object(main, "WORKBENCH_DATABASE_PATH", str(database)), patch.object(main, "WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED", True):
                canonical = main.canonical_project_canvas_repository()
                canonical.activate_sqlite_authority([])
                self.assertIsInstance(main.canvas_repository(), SqliteCanvasCompatibilityRepository)

    def test_r4_canonical_routing_is_enabled_by_default(self):
        self.assertTrue(main.WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED)

    def test_r4_split_brain_guard_refuses_writable_legacy_under_sqlite_authority(self):
        from workbench.application.canvas_authority_policy import CanvasAuthoritySplitBrainError

        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "workbench.sqlite3"
            with patch.object(main, "WORKBENCH_DATABASE_PATH", str(database)):
                main.canonical_project_canvas_repository().activate_sqlite_authority([])
            with patch.object(main, "WORKBENCH_DATABASE_PATH", str(database)), patch.object(main, "WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED", False):
                with self.assertRaises(CanvasAuthoritySplitBrainError):
                    main.canvas_repository()
                with self.assertRaises(CanvasAuthoritySplitBrainError):
                    main.enforce_canvas_authority_policy()

    def test_r4_guard_detects_authority_activated_after_a_legacy_routed_start(self):
        from workbench.application.canvas_authority_policy import CanvasAuthoritySplitBrainError

        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "workbench.sqlite3"
            with patch.object(main, "WORKBENCH_DATABASE_PATH", str(database)), patch.object(main, "WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED", False):
                self.assertIsInstance(main.canvas_repository(), LegacyJsonCanvasRepository)
                main.canonical_project_canvas_repository().activate_sqlite_authority([])
                with self.assertRaises(CanvasAuthoritySplitBrainError):
                    main.canvas_repository()

    def test_r4_legacy_recovery_and_migration_paths_stay_available_when_authority_inactive(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "workbench.sqlite3"
            with patch.object(main, "WORKBENCH_DATABASE_PATH", str(database)), patch.object(main, "WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED", False):
                main.canonical_project_canvas_repository()
                self.assertIsInstance(main.canvas_repository(), LegacyJsonCanvasRepository)
                self.assertIsInstance(main.project_canvas_migration_service(), ProjectCanvasMigrationService)

    def test_r4_split_brain_guard_is_wired_into_startup_and_entry(self):
        import inspect

        self.assertIn("enforce_canvas_authority_policy()", inspect.getsource(main.startup_event))
        self.assertIn("enforce_canvas_authority_policy()", inspect.getsource(main))
