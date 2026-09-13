import json
import tempfile
import unittest
from pathlib import Path
from threading import Lock

from workbench.application.legacy_definitions import LegacyDefinitionRegistry
from workbench.application.node_creation import NodeCreationService
from workbench.application.node_mutation import (
    NodeDeleteCommand,
    NodeMutationService,
    NodeMutationUnsupportedError,
    NodeUpdateCommand,
)
from workbench.domain.canvas.models import ModelBinding, Position
from workbench.repositories.jsonl_audit_sink import JsonlAuditSink
from workbench.repositories.canvas_repository import StaleCanvasRevisionError
from workbench.repositories.legacy_json_canvas_repository import LegacyJsonCanvasRepository
from workbench.repositories.legacy_json_node_repository import (
    LegacyCanvasProjectAuthorizer,
    LegacyJsonNodeCreationRepository,
    LegacyJsonNodeLookup,
    LegacyJsonNodeMutationRepository,
)
from workbench.application.node_creation import NodeCreateCommand, NodeCreationSource


class CompatibleNoModel:
    def is_compatible(self, definition, binding):
        return False


class LegacyNodeAdaptersTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.lock = Lock()
        self.clock = 100
        self.canvas_repository = LegacyJsonCanvasRepository(self.root / "canvases", clock_ms=lambda: self.clock, lock=self.lock)
        self.canvas_repository.save({
            "id": "canvas-1", "project": "project-1", "owner": "user-1", "nodes": [], "connections": [], "updated_at": 99,
        })
        self.authorizer = LegacyCanvasProjectAuthorizer(self.canvas_repository)
        self.node_repository = LegacyJsonNodeCreationRepository(self.canvas_repository)
        self.audit_path = self.root / "audit" / "events.jsonl"
        self.service = NodeCreationService(
            authorizer=self.authorizer,
            definitions=LegacyDefinitionRegistry(),
            model_policy=CompatibleNoModel(),
            repository=self.node_repository,
            audit_sink=JsonlAuditSink(self.audit_path, lock=Lock()),
            node_id_factory=lambda: "created-image-1",
        )
        self.mutations = NodeMutationService(
            authorizer=self.authorizer,
            repository=LegacyJsonNodeMutationRepository(self.canvas_repository),
            audit_sink=JsonlAuditSink(self.audit_path, lock=Lock()),
        )

    def tearDown(self):
        self.temp.cleanup()

    def command(self, **overrides):
        values = {
            "request_id": "request-1", "actor_id": "user-1", "project_id": "project-1", "canvas_id": "canvas-1",
            "source": NodeCreationSource.LEGACY, "definition_ref": LegacyDefinitionRegistry.IMAGE, "position": Position(x=20, y=30),
            "expected_revision": 100,
        }
        values.update(overrides)
        return NodeCreateCommand(**values)

    def test_creates_one_legacy_image_with_persistent_idempotency_and_audit(self):
        first = self.service.create(self.command())
        second = self.service.create(self.command())
        canvas = self.canvas_repository.load("canvas-1")
        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(len(canvas["nodes"]), 1)
        self.assertEqual(canvas["nodes"][0]["type"], "image")
        self.assertEqual(canvas["nodes"][0]["_workbench_node_create_request_id"], "request-1")
        self.assertEqual(first.node.kind, "asset")
        self.assertEqual(second.node.kind, "asset")
        events = [json.loads(line) for line in self.audit_path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(events), 1)
        self.assertNotIn("config", events[0])

    def test_creates_a_smart_image_in_its_durable_smart_shape(self):
        self.canvas_repository.save({
            "id": "smart-canvas-1", "project": "project-1", "owner": "user-1", "kind": "smart",
            "nodes": [], "connections": [], "updated_at": 100,
        })
        result = self.service.create(self.command(
            canvas_id="smart-canvas-1", request_id="smart-image-request", expected_revision=101,
        ))
        node = self.canvas_repository.load("smart-canvas-1")["nodes"][0]
        self.assertTrue(result.created)
        self.assertEqual((node["type"], node["title"], node["images"]), ("smart-image", "Image", []))
        self.assertNotIn("name", node)

    def test_lookup_enforces_project_and_owner_scope(self):
        self.service.create(self.command())
        lookup = LegacyJsonNodeLookup(self.canvas_repository, self.authorizer)
        record = lookup.get(actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="created-image-1")
        self.assertEqual(record.definition_ref.id, "image")
        with self.assertRaises(LookupError):
            lookup.get(actor_id="other", project_id="project-1", canvas_id="canvas-1", node_id="created-image-1")

    def test_creates_approved_legacy_prompt_with_its_text_config(self):
        result = self.service.create(self.command(
            request_id="prompt-request", definition_ref=LegacyDefinitionRegistry.PROMPT,
            initial_config={"text": ""},
        ))
        canvas = self.canvas_repository.load("canvas-1")
        self.assertTrue(result.created)
        self.assertEqual(canvas["nodes"][0]["type"], "prompt")
        self.assertEqual(canvas["nodes"][0]["text"], "")

    def test_creates_smart_prompt_with_only_whitelisted_initial_config(self):
        self.service.create(self.command(request_id="smart-prompt-request", definition_ref=LegacyDefinitionRegistry.SMART_PROMPT, initial_config={"text": "", "promptResult": "generated", "promptResultOutdated": True, "llmProvider": "provider", "llmModel": "model", "promptSkillPack": "MiniMax H3 Skills", "promptSkillDefinition": "3D动画短片生成器", "secret": "must-not-persist"}))
        node = self.canvas_repository.load("canvas-1")["nodes"][0]
        self.assertEqual(node["type"], "smart-prompt")
        self.assertEqual(node["llmProvider"], "provider")
        self.assertEqual(node["promptSkillPack"], "MiniMax H3 Skills")
        self.assertEqual(node["promptSkillDefinition"], "3D动画短片生成器")
        self.assertEqual(node["promptResult"], "generated")
        self.assertTrue(node["promptResultOutdated"])
        self.assertNotIn("secret", node)

    def test_creates_smart_loop_with_its_safe_defaults(self):
        self.service.create(self.command(request_id="smart-loop-request", definition_ref=LegacyDefinitionRegistry.SMART_LOOP))
        node = self.canvas_repository.load("canvas-1")["nodes"][0]
        self.assertEqual(node["type"], "smart-loop")
        self.assertEqual((node["count"], node["mode"]), (1, "serial"))

    def test_creates_empty_smart_group_with_its_safe_defaults(self):
        result = self.service.create(self.command(
            request_id="smart-group-request", definition_ref=LegacyDefinitionRegistry.SMART_GROUP,
        ))
        node = self.canvas_repository.load("canvas-1")["nodes"][0]
        self.assertTrue(result.created)
        self.assertEqual(result.node.kind, "group")
        self.assertEqual((node["type"], node["title"], node["w"], node["h"], node["items"]), (
            "smart-group", "智能分组", 340, 286, [],
        ))

    def test_creates_empty_smart_minimax_with_safe_defaults(self):
        result = self.service.create(self.command(
            request_id="smart-minimax-request", definition_ref=LegacyDefinitionRegistry.SMART_MINIMAX,
        ))
        node = self.canvas_repository.load("canvas-1")["nodes"][0]
        self.assertTrue(result.created)
        self.assertEqual((node["type"], node["workflow"], node["minimaxEngine"]), (
            "smart-minimax", "MiniMax_H3.json", "comfyui",
        ))
        self.assertFalse(node["running"])

    def test_creates_empty_classic_group_with_its_safe_defaults(self):
        result = self.service.create(self.command(
            request_id="group-request", definition_ref=LegacyDefinitionRegistry.GROUP,
        ))
        node = self.canvas_repository.load("canvas-1")["nodes"][0]
        self.assertTrue(result.created)
        self.assertEqual(result.node.kind, "group")
        self.assertEqual((node["type"], node["title"], node["w"], node["h"], node["items"]), (
            "group", "Group", 300, 220, [],
        ))

    def test_creates_approved_legacy_loop_with_safe_defaults(self):
        self.service.create(self.command(request_id="loop-request", definition_ref=LegacyDefinitionRegistry.LOOP, initial_config={"count": 3}))
        node = self.canvas_repository.load("canvas-1")["nodes"][0]
        self.assertEqual(node["type"], "loop")
        self.assertEqual(node["count"], 3)
        self.assertFalse(node["showPrompt"])

    def test_creates_approved_legacy_output_with_empty_images(self):
        result = self.service.create(self.command(
            request_id="output-request", definition_ref=LegacyDefinitionRegistry.OUTPUT,
        ))
        node = self.canvas_repository.load("canvas-1")["nodes"][0]
        self.assertTrue(result.created)
        self.assertEqual((node["type"], node["images"], node["w"], node["h"]), ("output", [], 460, 180))

    def test_creates_collection_node_through_the_versioned_creation_boundary(self):
        collection = {"id": "collection-1", "project_id": "project-1", "name": "Shots", "schema": {"id": "schema-1", "name": "Shots", "columns": []}, "items": []}
        result = self.service.create(self.command(
            request_id="collection-request", source=NodeCreationSource.QUICK_COLLECTION,
            definition_ref=LegacyDefinitionRegistry.COLLECTION, title="Shots", initial_config={"collection": collection},
        ))
        node = self.canvas_repository.load("canvas-1")["nodes"][0]
        self.assertTrue(result.created)
        self.assertEqual(result.node.kind, "collection")
        self.assertEqual((node["type"], node["title"], node["collection"]["id"]), ("collection", "Shots", "collection-1"))

    def test_unowned_can_be_explicitly_limited_to_local_policy(self):
        self.canvas_repository.save({"id": "unowned", "project": "project-1", "owner": "", "nodes": [], "updated_at": 100})
        strict = LegacyCanvasProjectAuthorizer(self.canvas_repository)
        local = LegacyCanvasProjectAuthorizer(self.canvas_repository, allow_unowned_local=True)
        self.assertFalse(strict.can_edit("user-1", "project-1", "unowned"))
        self.assertTrue(local.can_edit("user-1", "project-1", "unowned"))

    def test_update_and_delete_image_removes_connected_edges_and_audits(self):
        self.service.create(self.command())
        before = self.canvas_repository.load("canvas-1")
        self.canvas_repository.mutate_if_current("canvas-1", expected_updated_at=before["updated_at"], mutation=lambda canvas: canvas.update({
            "connections": [{"from": "created-image-1", "to": "other"}, {"from": "other", "to": "created-image-1"}],
        }))
        revision = self.canvas_repository.load("canvas-1")["updated_at"]
        updated = self.mutations.update(NodeUpdateCommand(
            actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="created-image-1",
            expected_revision=revision, title="Renamed", position=Position(x=44, y=55),
        ))
        self.assertEqual(updated.node.title, "Renamed")
        deleted = self.mutations.delete(NodeDeleteCommand(
            actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="created-image-1",
            expected_revision=updated.canvas_revision,
        ))
        canvas = self.canvas_repository.load("canvas-1")
        self.assertEqual(deleted.canvas_revision, canvas["updated_at"])
        self.assertEqual(canvas["nodes"], [])
        self.assertEqual(canvas["connections"], [])
        events = [json.loads(line) for line in self.audit_path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([event["event"] for event in events], ["canvas.node.created", "canvas.node.updated", "canvas.node.deleted"])

    def test_update_and_delete_smart_image_preserves_its_smart_title_shape(self):
        before = self.canvas_repository.load("canvas-1")
        self.canvas_repository.mutate_if_current("canvas-1", expected_updated_at=before["updated_at"], mutation=lambda canvas: canvas.update({
            "nodes": [{"id": "smart-image-1", "type": "smart-image", "title": "导入图片", "images": [], "x": 20, "y": 30}],
            "connections": [{"from": "smart-image-1", "to": "other"}],
        }))
        revision = self.canvas_repository.load("canvas-1")["updated_at"]
        updated = self.mutations.update(NodeUpdateCommand(
            actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="smart-image-1",
            expected_revision=revision, title="空白图片", position=Position(x=44, y=55),
        ))
        stored = self.canvas_repository.load("canvas-1")["nodes"][0]
        self.assertEqual((updated.node.title, stored["title"], stored["x"], stored["y"]), ("空白图片", "空白图片", 44, 55))
        self.assertNotIn("name", stored)
        self.mutations.delete(NodeDeleteCommand(
            actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="smart-image-1",
            expected_revision=updated.canvas_revision,
        ))
        canvas = self.canvas_repository.load("canvas-1")
        self.assertEqual(canvas["nodes"], [])
        self.assertEqual(canvas["connections"], [])

    def test_update_and_delete_empty_classic_prompt_preserves_its_prompt_shape(self):
        before = self.canvas_repository.load("canvas-1")
        self.canvas_repository.mutate_if_current("canvas-1", expected_updated_at=before["updated_at"], mutation=lambda canvas: canvas.update({
            "nodes": [{"id": "prompt-1", "type": "prompt", "text": "", "x": 20, "y": 30}],
            "connections": [],
        }))
        revision = self.canvas_repository.load("canvas-1")["updated_at"]
        updated = self.mutations.update(NodeUpdateCommand(
            actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="prompt-1",
            expected_revision=revision, position=Position(x=44, y=55),
        ))
        stored = self.canvas_repository.load("canvas-1")["nodes"][0]
        self.assertEqual((stored["type"], stored["text"], stored["x"], stored["y"]), ("prompt", "", 44, 55))
        self.mutations.delete(NodeDeleteCommand(
            actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="prompt-1",
            expected_revision=updated.canvas_revision,
        ))
        canvas = self.canvas_repository.load("canvas-1")
        self.assertEqual(canvas["nodes"], [])
        self.assertEqual(canvas["connections"], [])

    def test_update_and_delete_default_classic_loop_preserves_its_loop_shape(self):
        before = self.canvas_repository.load("canvas-1")
        self.canvas_repository.mutate_if_current("canvas-1", expected_updated_at=before["updated_at"], mutation=lambda canvas: canvas.update({
            "nodes": [{"id": "loop-1", "type": "loop", "count": 3, "mode": "serial", "showPrompt": False, "imageInput": False, "videoInput": False, "loopStart": 1, "imageBatchSize": 1, "videoBatchSize": 1, "variablePrompt": "", "fixedPrompt": "", "x": 20, "y": 30}],
            "connections": [],
        }))
        revision = self.canvas_repository.load("canvas-1")["updated_at"]
        updated = self.mutations.update(NodeUpdateCommand(
            actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="loop-1",
            expected_revision=revision, position=Position(x=44, y=55),
        ))
        stored = self.canvas_repository.load("canvas-1")["nodes"][0]
        self.assertEqual((stored["type"], stored["count"], stored["mode"], stored["x"], stored["y"]), ("loop", 3, "serial", 44, 55))
        self.mutations.delete(NodeDeleteCommand(
            actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="loop-1",
            expected_revision=updated.canvas_revision,
        ))
        canvas = self.canvas_repository.load("canvas-1")
        self.assertEqual(canvas["nodes"], [])
        self.assertEqual(canvas["connections"], [])

    def test_update_and_delete_empty_classic_output_preserves_its_output_shape(self):
        before = self.canvas_repository.load("canvas-1")
        self.canvas_repository.mutate_if_current("canvas-1", expected_updated_at=before["updated_at"], mutation=lambda canvas: canvas.update({
            "nodes": [{"id": "output-1", "type": "output", "images": [], "x": 20, "y": 30}],
            "connections": [],
        }))
        revision = self.canvas_repository.load("canvas-1")["updated_at"]
        updated = self.mutations.update(NodeUpdateCommand(
            actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="output-1",
            expected_revision=revision, position=Position(x=44, y=55),
        ))
        stored = self.canvas_repository.load("canvas-1")["nodes"][0]
        self.assertEqual((stored["type"], stored["images"], stored["x"], stored["y"]), ("output", [], 44, 55))
        self.mutations.delete(NodeDeleteCommand(
            actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="output-1",
            expected_revision=updated.canvas_revision,
        ))
        canvas = self.canvas_repository.load("canvas-1")
        self.assertEqual(canvas["nodes"], [])
        self.assertEqual(canvas["connections"], [])

    def test_update_and_delete_empty_classic_group_preserves_its_group_shape(self):
        before = self.canvas_repository.load("canvas-1")
        self.canvas_repository.mutate_if_current("canvas-1", expected_updated_at=before["updated_at"], mutation=lambda canvas: canvas.update({
            "nodes": [{"id": "group-1", "type": "group", "items": [], "w": 300, "h": 220, "x": 20, "y": 30}],
            "connections": [],
        }))
        revision = self.canvas_repository.load("canvas-1")["updated_at"]
        updated = self.mutations.update(NodeUpdateCommand(
            actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="group-1",
            expected_revision=revision, position=Position(x=44, y=55),
        ))
        stored = self.canvas_repository.load("canvas-1")["nodes"][0]
        self.assertEqual((stored["type"], stored["items"], stored["w"], stored["h"], stored["x"], stored["y"]), ("group", [], 300, 220, 44, 55))
        self.mutations.delete(NodeDeleteCommand(
            actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="group-1",
            expected_revision=updated.canvas_revision,
        ))
        canvas = self.canvas_repository.load("canvas-1")
        self.assertEqual(canvas["nodes"], [])
        self.assertEqual(canvas["connections"], [])

    def test_update_and_delete_empty_smart_group_preserves_its_group_shape(self):
        before = self.canvas_repository.load("canvas-1")
        self.canvas_repository.mutate_if_current("canvas-1", expected_updated_at=before["updated_at"], mutation=lambda canvas: canvas.update({
            "nodes": [{"id": "smart-group-1", "type": "smart-group", "title": "智能分组", "items": [], "w": 300, "h": 220, "x": 20, "y": 30}],
            "connections": [],
        }))
        revision = self.canvas_repository.load("canvas-1")["updated_at"]
        updated = self.mutations.update(NodeUpdateCommand(actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="smart-group-1", expected_revision=revision, position=Position(x=44, y=55)))
        stored = self.canvas_repository.load("canvas-1")["nodes"][0]
        self.assertEqual((stored["type"], stored["title"], stored["items"], stored["x"], stored["y"]), ("smart-group", "智能分组", [], 44, 55))
        self.mutations.delete(NodeDeleteCommand(actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="smart-group-1", expected_revision=updated.canvas_revision))
        self.assertEqual(self.canvas_repository.load("canvas-1")["nodes"], [])

    def test_update_and_delete_default_smart_loop_preserves_its_loop_shape(self):
        before = self.canvas_repository.load("canvas-1")
        self.canvas_repository.mutate_if_current("canvas-1", expected_updated_at=before["updated_at"], mutation=lambda canvas: canvas.update({"nodes": [{"id":"smart-loop-1", "type":"smart-loop", "count":1, "mode":"serial", "showPrompt":False, "imageInput":False, "loopStart":1, "imageBatchSize":1, "variablePrompt":"", "x":20, "y":30}], "connections": []}))
        revision = self.canvas_repository.load("canvas-1")["updated_at"]
        updated = self.mutations.update(NodeUpdateCommand(actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="smart-loop-1", expected_revision=revision, position=Position(x=44, y=55)))
        self.assertEqual((self.canvas_repository.load("canvas-1")["nodes"][0]["type"], self.canvas_repository.load("canvas-1")["nodes"][0]["x"]), ("smart-loop", 44))
        self.mutations.delete(NodeDeleteCommand(actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="smart-loop-1", expected_revision=updated.canvas_revision))
        self.assertEqual(self.canvas_repository.load("canvas-1")["nodes"], [])

    def seed_node(self, node):
        before = self.canvas_repository.load("canvas-1")
        def append(canvas):
            canvas["nodes"] = [*(canvas.get("nodes") or []), node]
        self.canvas_repository.mutate_if_current("canvas-1", expected_updated_at=before["updated_at"], mutation=append)
        return self.canvas_repository.load("canvas-1")["updated_at"]

    def test_update_and_delete_content_bearing_image_is_rejected(self):
        revision = self.seed_node({"id": "rich-image", "type": "image", "name": "导入图片", "url": "/output/a.png", "x": 20, "y": 30})
        with self.assertRaises(NodeMutationUnsupportedError):
            self.mutations.update(NodeUpdateCommand(actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="rich-image", expected_revision=revision, position=Position(x=44, y=55)))
        with self.assertRaises(NodeMutationUnsupportedError):
            self.mutations.delete(NodeDeleteCommand(actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="rich-image", expected_revision=revision))
        canvas = self.canvas_repository.load("canvas-1")
        self.assertEqual(canvas["updated_at"], revision)
        self.assertEqual([node["id"] for node in canvas["nodes"]], ["rich-image"])

    def test_group_member_blank_image_is_rejected(self):
        revision = self.seed_node({"id": "member-image", "type": "image", "name": "Image", "x": 20, "y": 30})
        before = self.canvas_repository.load("canvas-1")
        self.canvas_repository.mutate_if_current("canvas-1", expected_updated_at=before["updated_at"], mutation=lambda canvas: canvas["nodes"].append({"id": "group-1", "type": "group", "title": "Group", "items": ["member-image"], "x": 0, "y": 0}))
        revision = self.canvas_repository.load("canvas-1")["updated_at"]
        with self.assertRaises(NodeMutationUnsupportedError):
            self.mutations.update(NodeUpdateCommand(actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="member-image", expected_revision=revision, position=Position(x=44, y=55)))
        with self.assertRaises(NodeMutationUnsupportedError):
            self.mutations.delete(NodeDeleteCommand(actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="member-image", expected_revision=revision))
        canvas = self.canvas_repository.load("canvas-1")
        self.assertEqual(canvas["updated_at"], revision)
        self.assertEqual({node["id"] for node in canvas["nodes"]}, {"member-image", "group-1"})
        self.assertEqual(next(node for node in canvas["nodes"] if node["id"] == "group-1")["items"], ["member-image"])

    def test_input_referenced_node_delete_is_rejected(self):
        revision = self.seed_node({"id": "referenced-image", "type": "image", "name": "Image", "x": 20, "y": 30})
        before = self.canvas_repository.load("canvas-1")
        self.canvas_repository.mutate_if_current("canvas-1", expected_updated_at=before["updated_at"], mutation=lambda canvas: canvas["nodes"].append({"id": "consumer", "type": "loop", "count": 3, "inputNodeIds": ["referenced-image"], "x": 60, "y": 60}))
        revision = self.canvas_repository.load("canvas-1")["updated_at"]
        with self.assertRaises(NodeMutationUnsupportedError):
            self.mutations.delete(NodeDeleteCommand(actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="referenced-image", expected_revision=revision))
        canvas = self.canvas_repository.load("canvas-1")
        self.assertEqual(canvas["updated_at"], revision)
        self.assertEqual(canvas["nodes"][1]["inputNodeIds"], ["referenced-image"])

    def test_connected_prompt_is_rejected_while_connected_image_removes_its_edges(self):
        revision = self.seed_node({"id": "linked-prompt", "type": "prompt", "text": "", "x": 20, "y": 30})
        before = self.canvas_repository.load("canvas-1")
        self.canvas_repository.mutate_if_current("canvas-1", expected_updated_at=before["updated_at"], mutation=lambda canvas: canvas.update({"connections": [{"id": "edge-1", "from": "linked-prompt", "to": "target", "kind": "input"}]}))
        revision = self.canvas_repository.load("canvas-1")["updated_at"]
        with self.assertRaises(NodeMutationUnsupportedError):
            self.mutations.delete(NodeDeleteCommand(actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="linked-prompt", expected_revision=revision))
        self.assertEqual(len(self.canvas_repository.load("canvas-1")["nodes"]), 1)

        revision = self.seed_node({"id": "linked-image", "type": "image", "name": "Image", "x": 80, "y": 80})
        deleted = self.mutations.delete(NodeDeleteCommand(actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="linked-image", expected_revision=revision))
        canvas = self.canvas_repository.load("canvas-1")
        self.assertEqual([node["id"] for node in canvas["nodes"]], ["linked-prompt"])
        self.assertEqual([edge["id"] for edge in canvas["connections"] if edge.get("from") == "linked-image" or edge.get("to") == "linked-image"], [])
        self.assertGreater(deleted.canvas_revision, revision)

    def test_stale_mutation_is_rejected_without_canvas_change(self):
        revision = self.seed_node({"id": "blank-image", "type": "image", "name": "Image", "x": 20, "y": 30})
        with self.assertRaises(StaleCanvasRevisionError):
            self.mutations.update(NodeUpdateCommand(actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="blank-image", expected_revision=revision - 1, position=Position(x=44, y=55)))
        with self.assertRaises(StaleCanvasRevisionError):
            self.mutations.delete(NodeDeleteCommand(actor_id="user-1", project_id="project-1", canvas_id="canvas-1", node_id="blank-image", expected_revision=revision - 1))
        canvas = self.canvas_repository.load("canvas-1")
        self.assertEqual((canvas["updated_at"], canvas["nodes"][0]["x"]), (revision, 20))
