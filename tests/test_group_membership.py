import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock

from workbench.application.group_mutation import (
    GroupMembershipCommand,
    GroupMembershipPersistence,
    GroupMembershipService,
    GroupMutationError,
)
from workbench.domain.canvas.models import DefinitionRef, NodeRecord, Position, RendererRef, Size
from workbench.domain.canvas.ports import PortSet
from workbench.domain.canvas.states import NodeState
from workbench.repositories.canvas_repository import StaleCanvasRevisionError
from workbench.repositories.legacy_json_canvas_repository import LegacyJsonCanvasRepository
from workbench.repositories.legacy_json_node_repository import LegacyJsonGroupMembershipRepository


def group_record():
    return NodeRecord(
        id="group", project_id="project", canvas_id="canvas", kind="group",
        definition_ref=DefinitionRef(type="legacy", id="group", version="0"),
        renderer=RendererRef(id="legacy", version="1"), state=NodeState.READY,
        title="Group", position=Position(x=1, y=2), size=Size(width=300, height=220),
        ports=PortSet(), created_by="actor",
        created_at=datetime(2026, 9, 2, tzinfo=UTC), updated_at=datetime(2026, 9, 2, tzinfo=UTC),
    )


class Auth:
    def __init__(self, allowed=True):
        self.allowed = allowed

    def can_edit(self, *args):
        return self.allowed


class Repository:
    def set_group_membership(self, command):
        return GroupMembershipPersistence(group=group_record(), canvas_revision=7)


class Audit:
    def __init__(self):
        self.events = []

    def append(self, event):
        self.events.append(event)


class GroupMembershipServiceTests(unittest.TestCase):
    def command(self, **changes):
        values = dict(
            actor_id="actor", project_id="project", canvas_id="canvas",
            expected_revision=1, group_id="group", member_id="member", operation="add",
        )
        values.update(changes)
        return GroupMembershipCommand(**values)

    def test_authorized_membership_change_delegates_and_audits(self):
        audit = Audit()
        result = GroupMembershipService(authorizer=Auth(), repository=Repository(), audit_sink=audit).set_membership(self.command())
        self.assertEqual(result.canvas_revision, 7)
        self.assertEqual(result.group.id, "group")
        self.assertEqual((audit.events[0].group_id, audit.events[0].member_id, audit.events[0].operation), ("group", "member", "add"))

    def test_rejects_missing_required_fields_before_persistence(self):
        service = GroupMembershipService(authorizer=Auth(), repository=Repository(), audit_sink=Audit())
        for field in ("actor_id", "project_id", "canvas_id", "group_id", "member_id"):
            with self.subTest(field=field), self.assertRaisesRegex(GroupMutationError, "required"):
                service.set_membership(self.command(**{field: " "}))

    def test_rejects_non_positive_revision_and_invalid_operation(self):
        service = GroupMembershipService(authorizer=Auth(), repository=Repository(), audit_sink=Audit())
        for revision in (0, -1):
            with self.subTest(revision=revision), self.assertRaisesRegex(GroupMutationError, "expected_revision must be positive"):
                service.set_membership(self.command(expected_revision=revision))
        with self.assertRaisesRegex(GroupMutationError, "add or remove"):
            service.set_membership(self.command(operation="flip"))

    def test_rejects_self_membership_before_persistence(self):
        service = GroupMembershipService(authorizer=Auth(), repository=Repository(), audit_sink=Audit())
        with self.assertRaisesRegex(GroupMutationError, "cannot contain itself"):
            service.set_membership(self.command(member_id="group"))

    def test_rejects_unauthorized_membership_change(self):
        with self.assertRaisesRegex(GroupMutationError, "not permitted"):
            GroupMembershipService(authorizer=Auth(False), repository=Repository(), audit_sink=Audit()).set_membership(self.command())


class LegacyJsonGroupMembershipRepositoryTests(unittest.TestCase):
    def _canvas(self, group_type="group", member_type="prompt"):
        return {
            "id": "canvas", "project": "project",
            "nodes": [
                {"id": "group", "type": group_type, "items": []},
                {"id": "member", "type": member_type},
            ],
            "connections": [], "updated_at": 99,
        }

    def test_add_and_remove_persist_and_reload_under_one_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = LegacyJsonCanvasRepository(Path(directory), clock_ms=lambda: 100, lock=Lock())
            repository.save(self._canvas("smart-group", "smart-prompt"))
            revision = repository.load("canvas")["updated_at"]
            repo = LegacyJsonGroupMembershipRepository(repository)
            added = repo.set_group_membership(GroupMembershipCommand(
                actor_id="actor", project_id="project", canvas_id="canvas",
                expected_revision=revision, group_id="group", member_id="member", operation="add",
            ))
            self.assertGreater(added.canvas_revision, revision)
            self.assertEqual(added.group.id, "group")
            self.assertEqual(repository.load("canvas")["nodes"][0]["items"], ["member"])
            removed = repo.set_group_membership(GroupMembershipCommand(
                actor_id="actor", project_id="project", canvas_id="canvas",
                expected_revision=added.canvas_revision, group_id="group", member_id="member", operation="remove",
            ))
            self.assertGreater(removed.canvas_revision, added.canvas_revision)
            self.assertEqual(repository.load("canvas")["nodes"][0]["items"], [])

    def test_add_is_idempotent_within_one_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = LegacyJsonCanvasRepository(Path(directory), clock_ms=lambda: 100, lock=Lock())
            repository.save(self._canvas())
            revision = repository.load("canvas")["updated_at"]
            repo = LegacyJsonGroupMembershipRepository(repository)
            first = repo.set_group_membership(GroupMembershipCommand(
                actor_id="actor", project_id="project", canvas_id="canvas",
                expected_revision=revision, group_id="group", member_id="member", operation="add",
            ))
            second = repo.set_group_membership(GroupMembershipCommand(
                actor_id="actor", project_id="project", canvas_id="canvas",
                expected_revision=first.canvas_revision, group_id="group", member_id="member", operation="add",
            ))
            self.assertEqual(second.group.id, "group")
            self.assertEqual(repository.load("canvas")["nodes"][0]["items"], ["member"])

    def test_rejects_stale_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = LegacyJsonCanvasRepository(Path(directory), clock_ms=lambda: 100, lock=Lock())
            repository.save(self._canvas())
            current = repository.load("canvas")["updated_at"]
            repo = LegacyJsonGroupMembershipRepository(repository)
            with self.assertRaises(StaleCanvasRevisionError):
                repo.set_group_membership(GroupMembershipCommand(
                    actor_id="actor", project_id="project", canvas_id="canvas",
                    expected_revision=current - 1, group_id="group", member_id="member", operation="add",
                ))

    def test_rejects_missing_group_or_member(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = LegacyJsonCanvasRepository(Path(directory), clock_ms=lambda: 100, lock=Lock())
            repository.save(self._canvas())
            revision = repository.load("canvas")["updated_at"]
            repo = LegacyJsonGroupMembershipRepository(repository)
            with self.assertRaisesRegex(GroupMutationError, "member node not found"):
                repo.set_group_membership(GroupMembershipCommand(
                    actor_id="actor", project_id="project", canvas_id="canvas",
                    expected_revision=revision, group_id="group", member_id="ghost", operation="add",
                ))
            with self.assertRaisesRegex(GroupMutationError, "group node not found"):
                repo.set_group_membership(GroupMembershipCommand(
                    actor_id="actor", project_id="project", canvas_id="canvas",
                    expected_revision=revision, group_id="ghost", member_id="member", operation="add",
                ))
