import sqlite3
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from workbench.application.authorization import AuthorizationError
from workbench.application.project_canvas_migration import ProjectCanvasMigrationService
from workbench.domain.project.models import ProjectRecord
from workbench.repositories.sqlite_project_canvas_repository import (
    DEFAULT_PROJECT_ID,
    LOCAL_WORKSPACE_ACTOR_ID,
    CanonicalStaleRevisionError,
    LegacyIdentityMapper,
    SqliteProjectCanvasRepository,
)


class SqliteProjectCanvasRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "workbench.sqlite3"
        self.clock = datetime(2026, 9, 5, tzinfo=UTC)
        self.repository = SqliteProjectCanvasRepository(self.path, clock=lambda: self.clock)
        self.default_project = ProjectRecord(
            id=DEFAULT_PROJECT_ID, name="默认项目", workspace_id="local",
            created_by=LOCAL_WORKSPACE_ACTOR_ID, created_at=self.clock, updated_at=self.clock,
        )
        self.repository.create_project(self.default_project)

    def tearDown(self):
        self.temp.cleanup()

    def legacy_canvas(self, canvas_id="canvas-1", **overrides):
        canvas = {
            "id": canvas_id, "project": "default", "owner": "", "title": "Legacy",
            "kind": "classic", "created_at": 1_000, "updated_at": 2_000,
            "nodes": [{"id": "n-1", "type": "future-node", "opaque": {"v": 1}}],
            "connections": [], "viewport": {"x": 1, "y": 2, "scale": 1},
            "future_canvas_field": ["preserve"],
        }
        canvas.update(overrides)
        return canvas

    def mapper(self):
        return LegacyIdentityMapper({DEFAULT_PROJECT_ID})

    def test_import_survives_reopen_and_preserves_unknown_legacy_payload(self):
        legacy = self.legacy_canvas()
        report = self.repository.import_legacy_canvases([legacy], self.mapper())

        self.assertEqual(report.imported_canvas_ids, ("canvas-1",))
        self.assertEqual(report.identity_resolutions["canvas-1"].owner_state, "local_unowned")
        self.assertIsNone(report.identity_resolutions["canvas-1"].owner_actor_id)
        reopened = SqliteProjectCanvasRepository(self.path, clock=lambda: self.clock)
        record = reopened.load_canvas_record("canvas-1")
        self.assertEqual((record.project_id, record.revision), ("default", 1))
        self.assertEqual(reopened.export_legacy_payload("canvas-1"), legacy)
        self.assertEqual(reopened.compare_legacy_payload(legacy), (True, ()))

    def test_non_empty_owner_maps_to_stable_local_actor_without_rewriting_payload(self):
        legacy = self.legacy_canvas(owner="designer-a")
        report = self.repository.import_legacy_canvases([legacy], self.mapper())

        resolution = report.identity_resolutions["canvas-1"]
        self.assertEqual(resolution.owner_actor_id, "legacy-owner:designer-a")
        self.assertEqual(self.repository.member_role("default", resolution.owner_actor_id), "editor")
        self.assertEqual(self.repository.export_legacy_payload("canvas-1")["owner"], "designer-a")

    def test_project_mismatch_is_reported_and_not_imported(self):
        report = self.repository.import_legacy_canvases([self.legacy_canvas(project="missing")], self.mapper())

        self.assertEqual(report.imported_canvas_ids, ())
        self.assertEqual(report.skipped_canvas_ids, ("canvas-1",))
        self.assertEqual(report.identity_resolutions["canvas-1"].issues, ("project_mismatch",))

    def test_mutation_uses_logical_revision_and_action_authorization(self):
        self.repository.import_legacy_canvases([self.legacy_canvas()], self.mapper())
        updated, payload = self.repository.mutate_canvas(
            actor_id=LOCAL_WORKSPACE_ACTOR_ID, canvas_id="canvas-1", expected_revision=1,
            mutation=lambda value: value.update({"title": "Canonical title"}),
        )
        self.assertEqual((updated.revision, payload["title"]), (2, "Canonical title"))
        with self.assertRaises(CanonicalStaleRevisionError) as stale:
            self.repository.mutate_canvas(actor_id=LOCAL_WORKSPACE_ACTOR_ID, canvas_id="canvas-1", expected_revision=1, mutation=lambda _: None)
        self.assertEqual(stale.exception.current_revision, 2)
        with self.assertRaises(AuthorizationError):
            self.repository.mutate_canvas(actor_id="viewer", canvas_id="canvas-1", expected_revision=2, mutation=lambda _: None)

    def test_sqlite_connections_enable_foreign_keys(self):
        with self.repository._connection() as connection:
            self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_invalid_foreign_key_write_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with self.repository._connection() as connection:
                connection.execute(
                    "INSERT INTO project_members VALUES (?, ?, ?, ?)",
                    ("missing-project", "actor", "editor", "2026-09-10T00:00:00Z"),
                )

    def test_mutation_rejects_a_write_that_loses_the_sqlite_compare_and_swap(self):
        self.repository.import_legacy_canvases([self.legacy_canvas()], self.mapper())
        connection = sqlite3.connect(self.path)
        try:
            connection.execute(
                """CREATE TRIGGER force_canvas_cas_conflict BEFORE UPDATE ON canvases
                   WHEN OLD.id = 'canvas-1' AND OLD.revision = 1
                   BEGIN
                     UPDATE canvases SET revision = 2 WHERE id = OLD.id;
                     SELECT RAISE(IGNORE);
                   END"""
            )
            connection.commit()
        finally:
            connection.close()

        with self.assertRaises(CanonicalStaleRevisionError) as stale:
            self.repository.mutate_canvas(
                actor_id=LOCAL_WORKSPACE_ACTOR_ID,
                canvas_id="canvas-1",
                expected_revision=1,
                mutation=lambda value: value.update({"title": "must not overwrite"}),
            )

        self.assertEqual(stale.exception.current_revision, 2)
        self.assertEqual(self.repository.load_canvas_payload("canvas-1")["title"], "Legacy")

    def test_audit_failure_rolls_back_the_canonical_mutation(self):
        self.repository.import_legacy_canvases([self.legacy_canvas()], self.mapper())
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("CREATE TRIGGER fail_canvas_audit BEFORE INSERT ON audit_outbox WHEN NEW.event_type = 'canvas.mutated' BEGIN SELECT RAISE(ABORT, 'audit unavailable'); END")
            connection.commit()
        finally:
            connection.close()
        with self.assertRaises(sqlite3.IntegrityError):
            self.repository.mutate_canvas(
                actor_id=LOCAL_WORKSPACE_ACTOR_ID, canvas_id="canvas-1", expected_revision=1,
                mutation=lambda value: value.update({"title": "must roll back"}),
            )
        record = self.repository.load_canvas_record("canvas-1")
        self.assertEqual(record.revision, 1)
        self.assertEqual(self.repository.load_canvas_payload("canvas-1")["title"], "Legacy")

    def test_project_read_and_canvas_edit_are_action_scoped(self):
        self.repository.import_legacy_canvases([self.legacy_canvas()], self.mapper())
        authorization = self.repository.authorization()
        self.assertTrue(authorization.allows(LOCAL_WORKSPACE_ACTOR_ID, "project.read", "default"))
        self.assertTrue(authorization.allows(LOCAL_WORKSPACE_ACTOR_ID, "canvas.edit", "default"))
        self.assertFalse(authorization.allows("unknown", "project.read", "default"))

    def test_authority_switch_requires_compare_and_rollback_exports_losslessly(self):
        legacy = self.legacy_canvas()
        self.repository.import_legacy_canvases([legacy], self.mapper())
        self.assertEqual(self.repository.canvas_authority(), "legacy_json")
        self.repository.activate_sqlite_authority([legacy])
        self.assertEqual(self.repository.canvas_authority(), "sqlite")
        self.assertEqual(self.repository.rollback_to_legacy_authority(), [legacy])
        self.assertEqual(self.repository.canvas_authority(), "legacy_json")

    def test_migration_service_backfills_projects_compares_then_activates(self):
        repository = SqliteProjectCanvasRepository(Path(self.temp.name) / "migration.sqlite3", clock=lambda: self.clock)
        service = ProjectCanvasMigrationService(repository)
        legacy = self.legacy_canvas()
        report, comparisons = service.backfill([{"id": "default", "name": "默认项目", "order": 0}], [legacy], now=self.clock)
        self.assertEqual(report.imported_canvas_ids, ("canvas-1",))
        self.assertEqual(comparisons[0].differences, ())
        service.activate_after_compare([legacy], comparisons)
        self.assertEqual(repository.canvas_authority(), "sqlite")
