"""R4-04 split-brain regression suite.

Turns the 2026-09-06 dual-writer incident into permanent behavioral coverage:
normal routing under SQLite authority, refusal of the disabled routing flag,
supported legacy migration/read/write state while authority is inactive,
authority persistence across restarts, and one-store write isolation.
"""

import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import main
from workbench.application.canvas_authority_policy import CanvasAuthoritySplitBrainError
from workbench.application.project_canvas_migration import ProjectCanvasMigrationService
from workbench.repositories.legacy_json_canvas_repository import LegacyJsonCanvasRepository
from workbench.repositories.sqlite_canvas_compatibility_repository import SqliteCanvasCompatibilityRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


class SplitBrainRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.canvas_dir = self.root / "canvases"
        self.canvas_dir.mkdir()
        self.database = self.root / "workbench.sqlite3"
        self.patches = [
            patch.object(main, "CANVAS_DIR", str(self.canvas_dir)),
            patch.object(main, "WORKBENCH_DATABASE_PATH", str(self.database)),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def _set_flag(self, enabled):
        patcher = patch.object(main, "WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED", enabled)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _legacy_payload(self, canvas_id, title):
        return {
            "id": canvas_id,
            "project": "default",
            "owner": "",
            "title": title,
            "kind": "classic",
            "created_at": 1788000000000,
            "updated_at": 1788000001000,
            "viewport": {"x": 0, "y": 0, "scale": 1},
            "nodes": [],
            "connections": [],
        }

    def _activate_sqlite_authority(self):
        payload = self._legacy_payload("canvas-1", "One")
        (self.canvas_dir / "canvas-1.json").write_text(json.dumps(payload), encoding="utf-8")
        service = main.project_canvas_migration_service()
        service.backfill([{"id": "default", "name": "Default"}], [payload], now=datetime.now(UTC))
        main.canonical_project_canvas_repository().activate_sqlite_authority([payload])

    def test_sqlite_authority_routes_normal_runtime_to_sqlite(self):
        self._activate_sqlite_authority()
        self._set_flag(True)

        repository = main.canvas_repository()
        self.assertIsInstance(repository, SqliteCanvasCompatibilityRepository)
        self.assertEqual([canvas["id"] for canvas in repository.list_payloads()], ["canvas-1"])
        decision = main.canvas_authority_decision()
        self.assertTrue(decision.use_sqlite)
        self.assertFalse(decision.split_brain_forbidden)
        self.assertEqual(decision.reason, "sqlite_authority_with_canonical_routing")

    def test_sqlite_authority_refuses_disabled_routing_flag(self):
        self._activate_sqlite_authority()
        self._set_flag(False)

        with self.assertRaises(CanvasAuthoritySplitBrainError):
            main.canvas_repository()
        with self.assertRaises(CanvasAuthoritySplitBrainError):
            main.enforce_canvas_authority_policy()

    def test_inactive_authority_supports_legacy_migration_read_and_write(self):
        main.canonical_project_canvas_repository()
        legacy_payload = self._legacy_payload("canvas-legacy", "Legacy")
        (self.canvas_dir / "canvas-legacy.json").write_text(json.dumps(legacy_payload), encoding="utf-8")
        self._set_flag(False)

        self.assertIsInstance(main.canvas_repository(), LegacyJsonCanvasRepository)
        self.assertIsInstance(main.project_canvas_migration_service(), ProjectCanvasMigrationService)

        created = main.new_canvas("runtime legacy write", kind="classic")
        self.assertTrue((self.canvas_dir / f"{created['id']}.json").exists())
        self.assertEqual(main.canonical_project_canvas_repository().list_canvas_payloads(), [])

        import_report, comparisons = main.project_canvas_migration_service().backfill(
            [{"id": "default", "name": "Default"}],
            [json.loads((self.canvas_dir / "canvas-legacy.json").read_text(encoding="utf-8"))],
            now=datetime.now(UTC),
        )
        self.assertEqual(list(import_report.imported_canvas_ids), ["canvas-legacy"])
        self.assertEqual(import_report.skipped_canvas_ids, ())
        self.assertTrue(all(comparison.matches for comparison in comparisons))

    def test_authority_persists_across_restart_and_decides_routing(self):
        self._activate_sqlite_authority()

        reopened = SqliteProjectCanvasRepository(self.database)
        self.assertEqual(reopened.canvas_authority(), "sqlite")

        self._set_flag(True)
        decision = main.canvas_authority_decision()
        self.assertTrue(decision.use_sqlite)
        self.assertIsInstance(main.canvas_repository(), SqliteCanvasCompatibilityRepository)

        self._set_flag(False)
        self.assertTrue(main.canvas_authority_decision().split_brain_forbidden)
        with self.assertRaises(CanvasAuthoritySplitBrainError):
            main.canvas_repository()

    def test_routed_writes_land_in_exactly_one_store(self):
        self._activate_sqlite_authority()
        self._set_flag(True)

        legacy_files_before = set(self.canvas_dir.glob("*.json"))
        created = main.new_canvas("canonical write", kind="classic")
        canonical_ids = [
            payload["id"] for payload in SqliteProjectCanvasRepository(self.database).list_canvas_payloads()
        ]
        self.assertIn(created["id"], canonical_ids)
        self.assertEqual(set(self.canvas_dir.glob("*.json")), legacy_files_before)

        self._set_flag(False)
        with self.assertRaises(CanvasAuthoritySplitBrainError):
            main.new_canvas("forbidden legacy write under sqlite authority", kind="classic")


if __name__ == "__main__":
    unittest.main()
