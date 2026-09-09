import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from workbench.application.node_mutation import (
    NodeDeleteCommand,
    NodeMutationService,
    NodeMutationUnsupportedError,
    NodeUpdateCommand,
)
from workbench.domain.canvas.models import Position
from workbench.domain.project.models import ProjectRecord
from workbench.repositories.canvas_repository import CanvasDeletedError, CanvasNotFoundError, StaleCanvasRevisionError
from workbench.repositories.legacy_json_node_repository import LegacyCanvasProjectAuthorizer, LegacyJsonNodeMutationRepository
from workbench.repositories.sqlite_canvas_compatibility_repository import SqliteCanvasCompatibilityRepository
from workbench.repositories.sqlite_project_canvas_repository import DEFAULT_PROJECT_ID, LOCAL_WORKSPACE_ACTOR_ID, SqliteProjectCanvasRepository


class SqliteCanvasCompatibilityRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.clock = datetime(2026, 9, 5, tzinfo=UTC)
        canonical = SqliteProjectCanvasRepository(Path(self.temp.name) / "workbench.sqlite3", clock=lambda: self.clock)
        canonical.create_project(ProjectRecord(id=DEFAULT_PROJECT_ID, name="Default", workspace_id="local", created_by=LOCAL_WORKSPACE_ACTOR_ID, created_at=self.clock, updated_at=self.clock))
        self.canonical = canonical
        self.repository = SqliteCanvasCompatibilityRepository(canonical, actor_id=LOCAL_WORKSPACE_ACTOR_ID, clock_ms=lambda: 500)

    def tearDown(self):
        self.temp.cleanup()

    def canvas(self, **extra):
        payload = {"id": "canvas-1", "project": "default", "title": "Fixture", "nodes": [], "connections": [], "updated_at": 500, "future": {"kept": True}}
        payload.update(extra)
        return payload

    def test_round_trips_losslessly_through_canonical_revisioned_storage(self):
        canvas = self.canvas()
        self.repository.save(canvas)
        self.assertEqual(canvas["updated_at"], 500)
        self.assertEqual(self.repository.load("canvas-1")["future"], {"kept": True})
        self.assertEqual(self.canonical.load_canvas_record("canvas-1").revision, 1)
        canvas["title"] = "Updated"
        self.repository.save(canvas)
        self.assertEqual((canvas["updated_at"], self.canonical.load_canvas_record("canvas-1").revision), (501, 2))

    def test_legacy_stale_check_and_soft_delete_semantics_are_preserved(self):
        self.repository.save(self.canvas())
        stale = self.canvas(title="Stale")
        with self.assertRaises(StaleCanvasRevisionError):
            self.repository.save_if_current(stale, expected_updated_at=499)
        deleted = self.repository.load("canvas-1")
        deleted["deleted_at"] = 1
        self.repository.save(deleted)
        with self.assertRaises(CanvasDeletedError):
            self.repository.load("canvas-1")
        self.assertEqual(self.repository.load("canvas-1", include_deleted=True)["id"], "canvas-1")

    def test_compat_save_if_current_rejects_interleaved_write(self):
        self.repository.save(self.canvas())
        other = SqliteCanvasCompatibilityRepository(self.canonical, actor_id=LOCAL_WORKSPACE_ACTOR_ID, clock_ms=lambda: 600)
        original_load_snapshot = self.canonical.load_canvas_snapshot
        interleaved = False

        def load_snapshot_with_interleaved_write(canvas_id):
            nonlocal interleaved
            snapshot = original_load_snapshot(canvas_id)
            if not interleaved:
                interleaved = True
                self.canonical.mutate_canvas(
                    actor_id=LOCAL_WORKSPACE_ACTOR_ID,
                    canvas_id=canvas_id,
                    expected_revision=snapshot.revision,
                    mutation=lambda payload: payload.update({"title": "B writer"}),
                )
            return snapshot

        self.canonical.load_canvas_snapshot = load_snapshot_with_interleaved_write
        with self.assertRaises(StaleCanvasRevisionError):
            self.repository.save_if_current(self.canvas(title="A writer"), expected_updated_at=500)
        self.assertEqual(other.load("canvas-1")["title"], "B writer")

    def test_compat_mutate_if_current_rejects_interleaved_write(self):
        self.repository.save(self.canvas())
        original_load_snapshot = self.canonical.load_canvas_snapshot
        interleaved = False

        def load_snapshot_with_interleaved_write(canvas_id):
            nonlocal interleaved
            snapshot = original_load_snapshot(canvas_id)
            if not interleaved:
                interleaved = True
                self.canonical.mutate_canvas(
                    actor_id=LOCAL_WORKSPACE_ACTOR_ID,
                    canvas_id=canvas_id,
                    expected_revision=snapshot.revision,
                    mutation=lambda payload: payload.update({"title": "B writer"}),
                )
            return snapshot

        self.canonical.load_canvas_snapshot = load_snapshot_with_interleaved_write
        with self.assertRaises(StaleCanvasRevisionError):
            self.repository.mutate_if_current(
                "canvas-1", expected_updated_at=500, mutation=lambda payload: payload.update({"title": "A writer"})
            )
        self.assertEqual(self.repository.load("canvas-1")["title"], "B writer")

    def test_future_expected_updated_at_is_rejected(self):
        self.repository.save(self.canvas())
        with self.assertRaises(StaleCanvasRevisionError):
            self.repository.save_if_current(self.canvas(title="A writer"), expected_updated_at=501)
        self.assertEqual(self.repository.load("canvas-1")["title"], "Fixture")

    def test_purge_is_idempotent_and_audited(self):
        self.repository.save(self.canvas())
        self.assertTrue(self.repository.purge("canvas-1"))
        self.assertFalse(self.repository.purge("canvas-1"))
        with self.assertRaises(CanvasNotFoundError):
            self.repository.load("canvas-1")
        self.assertEqual([event["event_type"] for event in self.canonical.outbox_events()], ["canvas.created", "canvas.purged"])

    def test_metadata_save_keeps_legacy_timestamp_but_advances_canonical_revision(self):
        self.repository.save(self.canvas())
        canvas = self.repository.load("canvas-1")
        canvas["pinned"] = True
        self.repository.save_metadata(canvas)
        self.assertEqual(self.repository.load("canvas-1")["updated_at"], 500)
        self.assertEqual(self.canonical.load_canvas_record("canvas-1").revision, 2)

    def test_project_reassignment_is_canonical_and_preserves_legacy_timestamp(self):
        other = ProjectRecord(id="other", name="Other", workspace_id="local", created_by=LOCAL_WORKSPACE_ACTOR_ID, created_at=self.clock, updated_at=self.clock)
        self.canonical.create_project(other)
        self.repository.save(self.canvas(project="other"))
        self.assertEqual(self.repository.reassign_project(source_project_id="other", target_project_id="default"), 1)
        self.assertEqual(self.repository.load("canvas-1")["project"], "default")
        self.assertEqual(self.repository.load("canvas-1")["updated_at"], 500)


class _ListAuditSink:
    def __init__(self):
        self.events = []

    def append(self, event):
        self.events.append(event)


class SqlitePathNodeMutationBoundaryTests(unittest.TestCase):
    """The versioned mutation boundary must hold on the canonical SQLite store too."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.canonical = SqliteProjectCanvasRepository(Path(self.temp.name) / "workbench.sqlite3")
        self.canonical.create_project(ProjectRecord(
            id=DEFAULT_PROJECT_ID, name="Default", workspace_id="local",
            created_by=LOCAL_WORKSPACE_ACTOR_ID, created_at=self.canonical._clock(), updated_at=self.canonical._clock(),
        ))
        self.repository = SqliteCanvasCompatibilityRepository(self.canonical, actor_id=LOCAL_WORKSPACE_ACTOR_ID, clock_ms=lambda: 500)
        self.repository.save({"id": "canvas-1", "project": "default", "owner": "", "title": "Fixture", "nodes": [], "connections": [], "updated_at": 500})
        self.service = NodeMutationService(
            authorizer=LegacyCanvasProjectAuthorizer(self.repository, allow_unowned_local=True),
            repository=LegacyJsonNodeMutationRepository(self.repository),
            audit_sink=_ListAuditSink(),
        )

    def tearDown(self):
        self.temp.cleanup()

    def seed_node(self, node):
        revision = self.canonical.load_canvas_record("canvas-1").revision
        self.repository.mutate_if_current("canvas-1", expected_updated_at=None, mutation=lambda canvas: canvas["nodes"].append(node))
        return self.repository.load("canvas-1")["updated_at"]

    def test_blank_image_update_and_delete_keep_the_sqlite_revision_contract(self):
        revision = self.seed_node({"id": "blank-1", "type": "image", "name": "Image", "x": 20, "y": 30})
        updated = self.service.update(NodeUpdateCommand(
            actor_id="local", project_id="default", canvas_id="canvas-1", node_id="blank-1",
            expected_revision=revision, position=Position(x=44, y=55),
        ))
        self.assertEqual(self.repository.load("canvas-1")["nodes"][0]["x"], 44)
        self.assertGreater(updated.canvas_revision, revision)
        deleted = self.service.delete(NodeDeleteCommand(
            actor_id="local", project_id="default", canvas_id="canvas-1", node_id="blank-1",
            expected_revision=updated.canvas_revision,
        ))
        self.assertEqual(self.repository.load("canvas-1")["nodes"], [])
        self.assertGreater(deleted.canvas_revision, updated.canvas_revision)

    def test_content_bearing_and_grouped_deletes_are_rejected_without_payload_change(self):
        revision = self.seed_node({"id": "rich-1", "type": "image", "name": "导入图片", "url": "/output/a.png", "x": 20, "y": 30})
        with self.assertRaises(NodeMutationUnsupportedError):
            self.service.delete(NodeDeleteCommand(
                actor_id="local", project_id="default", canvas_id="canvas-1", node_id="rich-1", expected_revision=revision,
            ))
        stored = self.repository.load("canvas-1")
        self.assertEqual(stored["updated_at"], revision)
        self.assertEqual(stored["nodes"][0]["url"], "/output/a.png")
        self.repository.mutate_if_current("canvas-1", expected_updated_at=None, mutation=lambda canvas: canvas["nodes"].append({"id": "group-1", "type": "group", "title": "Group", "items": ["member-1"], "x": 0, "y": 0}))
        revision = self.repository.load("canvas-1")["updated_at"]
        self.seed_node({"id": "member-1", "type": "image", "name": "Image", "x": 5, "y": 5})
        with self.assertRaises(NodeMutationUnsupportedError):
            self.service.delete(NodeDeleteCommand(
                actor_id="local", project_id="default", canvas_id="canvas-1", node_id="member-1",
                expected_revision=self.repository.load("canvas-1")["updated_at"],
            ))
        self.assertEqual(
            next(node for node in self.repository.load("canvas-1")["nodes"] if node["id"] == "group-1")["items"],
            ["member-1"],
        )

    def test_stale_mutation_is_rejected_through_sqlite(self):
        revision = self.seed_node({"id": "blank-2", "type": "image", "name": "Image", "x": 20, "y": 30})
        with self.assertRaises(StaleCanvasRevisionError):
            self.service.update(NodeUpdateCommand(
                actor_id="local", project_id="default", canvas_id="canvas-1", node_id="blank-2",
                expected_revision=revision - 1, position=Position(x=44, y=55),
            ))
        self.assertEqual(self.repository.load("canvas-1")["nodes"][0]["x"], 20)
