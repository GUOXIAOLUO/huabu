import asyncio
import unittest
from datetime import UTC, datetime

from fastapi import HTTPException

from pydantic import ValidationError

from workbench.api.canvas_nodes import CreateNodeAndEdgePayload, GroupMembershipPayload, NodeCreatePayload, NodeDeletePayload, NodeUpdatePayload, create_canvas_nodes_router
from workbench.application.node_creation import NodeCreationPersistence
from workbench.application.node_mutation import NodeMutationPersistence
from workbench.application.group_mutation import GroupMutationError
from workbench.domain.canvas.models import DefinitionRef, NodeRecord, Position, RendererRef, Size
from workbench.domain.canvas.ports import PortSet
from workbench.domain.canvas.states import NodeState
from workbench.repositories.canvas_repository import StaleCanvasRevisionError


def node_record():
    return NodeRecord(
        id="node-1", project_id="project-1", canvas_id="canvas-1", kind="legacy",
        definition_ref=DefinitionRef(type="legacy", id="image", version="0"),
        renderer=RendererRef(id="legacy", version="1"), state=NodeState.READY,
        title="Image", position=Position(x=1, y=2), size=Size(width=280, height=180),
        ports=PortSet(), created_by="user-1",
        created_at=datetime(2026, 9, 2, tzinfo=UTC), updated_at=datetime(2026, 9, 2, tzinfo=UTC),
    )


class Service:
    def __init__(self):
        self.commands = []

    def create(self, command):
        self.commands.append(command)
        return NodeCreationPersistence(node=node_record(), canvas_revision=2, created=True)


class Lookup:
    def get(self, **kwargs):
        if kwargs["node_id"] != "node-1":
            raise LookupError
        return node_record()


class MutationService:
    def update(self, command):
        return NodeMutationPersistence(node=node_record(), canvas_revision=3)

    def delete(self, command):
        return NodeMutationPersistence(canvas_revision=4)


class GroupService:
    def __init__(self):
        self.commands = []

    def set_membership(self, command):
        self.commands.append(command)
        return type("Persistence", (), {"group": node_record(), "canvas_revision": 5})()


class CanvasNodesApiTests(unittest.TestCase):
    def setUp(self):
        self.service = Service()
        self.router = create_canvas_nodes_router(
            service_for_actor=lambda actor: self.service,
            mutation_service_for_actor=lambda actor: MutationService(),
            graph_service_for_actor=lambda actor: GraphService(),
            group_service_for_actor=lambda actor: GroupService(),
            node_lookup=Lookup(),
        )
        self.create_endpoint = next(route.endpoint for route in self.router.routes if route.path.endswith("/nodes"))
        self.get_endpoint = next(route.endpoint for route in self.router.routes if route.path.endswith("{node_id}"))

    def payload(self):
        return NodeCreatePayload(
            request_id="request-1", project_id="project-1", source="legacy",
            definition_ref={"type": "legacy", "id": "image", "version": "0"}, position={"x": 20, "y": 30},
            expected_revision=1,
        )

    def test_create_requires_explicit_actor_and_returns_revisioned_record(self):
        with self.assertRaises(HTTPException) as missing_actor:
            asyncio.run(self.create_endpoint("canvas-1", self.payload(), x_user_id=""))
        self.assertEqual(missing_actor.exception.status_code, 401)

        response = asyncio.run(self.create_endpoint("canvas-1", self.payload(), x_user_id="user-1"))
        self.assertEqual(response.canvas_revision, 2)
        self.assertTrue(response.created)
        self.assertEqual(response.node["schema_version"], "workbench.node/1")
        self.assertEqual(self.service.commands[0].actor_id, "user-1")

    def test_connected_create_payload_requires_an_expected_revision(self):
        for revision in (None, 0, -1):
            with self.assertRaises(ValidationError):
                CreateNodeAndEdgePayload(
                    request_id="request-1", project_id="project-1", source="legacy",
                    definition_ref={"type": "legacy", "id": "image", "version": "0"}, position={"x": 20, "y": 30},
                    expected_revision=revision, existing_node_id="origin", edge_id="edge-1",
                )

    def test_get_requires_actor_and_project_scope_parameter(self):
        response = asyncio.run(self.get_endpoint("canvas-1", "node-1", project_id="project-1", x_user_id="user-1"))
        self.assertEqual(response["node"]["id"], "node-1")
        with self.assertRaises(HTTPException) as missing:
            asyncio.run(self.get_endpoint("canvas-1", "node-1", project_id="project-1", x_user_id=""))
        self.assertEqual(missing.exception.status_code, 401)

    def test_create_maps_stale_repository_conflict_to_409(self):
        class StaleService:
            def create(self, command):
                raise StaleCanvasRevisionError({"id": command.canvas_id, "updated_at": 2})

        router = create_canvas_nodes_router(
            service_for_actor=lambda actor: StaleService(),
            mutation_service_for_actor=lambda actor: MutationService(),
            graph_service_for_actor=lambda actor: GraphService(),
            group_service_for_actor=lambda actor: GroupService(),
            node_lookup=Lookup(),
        )
        endpoint = next(route.endpoint for route in router.routes if route.path.endswith("/nodes"))
        with self.assertRaises(HTTPException) as raised:
            asyncio.run(endpoint("canvas-1", self.payload(), x_user_id="user-1"))
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(raised.exception.detail["code"], "stale_revision")

    def test_update_and_delete_require_actor_and_return_new_revision(self):
        update = next(route.endpoint for route in self.router.routes if route.methods == {"PUT"})
        delete = next(route.endpoint for route in self.router.routes if route.methods == {"DELETE"})
        updated = asyncio.run(update("canvas-1", "node-1", NodeUpdatePayload(
            project_id="project-1", expected_revision=2, title="Renamed",
        ), x_user_id="user-1"))
        deleted = asyncio.run(delete("canvas-1", "node-1", NodeDeletePayload(
            project_id="project-1", expected_revision=3,
        ), x_user_id="user-1"))
        self.assertEqual(updated["canvas_revision"], 3)
        self.assertEqual(deleted, {"deleted": True, "canvas_revision": 4})
        with self.assertRaises(HTTPException) as missing:
            asyncio.run(delete("canvas-1", "node-1", NodeDeletePayload(
                project_id="project-1", expected_revision=3,
            ), x_user_id=""))
        self.assertEqual(missing.exception.status_code, 401)

    def test_update_payload_rejects_fields_outside_title_and_position(self):
        with self.assertRaises(ValidationError):
            NodeUpdatePayload(project_id="project-1", expected_revision=1, config={"provider": "x"})

    def test_group_membership_endpoint_delegates_and_returns_revision(self):
        endpoint = next(route.endpoint for route in self.router.routes if route.path.endswith("/graph/group-membership"))
        response = asyncio.run(endpoint("canvas-1", GroupMembershipPayload(
            project_id="project-1", expected_revision=1, group_id="group-1", member_id="member-1", operation="add",
        ), x_user_id="user-1"))
        self.assertEqual(response["canvas_revision"], 5)
        self.assertEqual(response["group"]["id"], "node-1")
        with self.assertRaises(HTTPException) as missing:
            asyncio.run(endpoint("canvas-1", GroupMembershipPayload(
                project_id="project-1", expected_revision=1, group_id="group-1", member_id="member-1",
            ), x_user_id=""))
        self.assertEqual(missing.exception.status_code, 401)

    def test_group_membership_payload_rejects_invalid_operation(self):
        with self.assertRaises(ValidationError):
            GroupMembershipPayload(project_id="project-1", expected_revision=1, group_id="g", member_id="m", operation="flip")
        with self.assertRaises(ValidationError):
            GroupMembershipPayload(project_id="project-1", expected_revision=0, group_id="g", member_id="m", operation="add")

    def test_group_membership_endpoint_maps_service_errors(self):
        class ForbiddenGroupService:
            def set_membership(self, command):
                raise GroupMutationError("forbidden", "actor is not permitted to edit this Canvas")

        class InvalidGroupService:
            def set_membership(self, command):
                raise GroupMutationError("invalid_graph", "member node not found")

        router = create_canvas_nodes_router(
            service_for_actor=lambda actor: Service(),
            mutation_service_for_actor=lambda actor: MutationService(),
            graph_service_for_actor=lambda actor: GraphService(),
            group_service_for_actor=lambda actor: ForbiddenGroupService(),
            node_lookup=Lookup(),
        )
        endpoint = next(route.endpoint for route in router.routes if route.path.endswith("/graph/group-membership"))
        with self.assertRaises(HTTPException) as forbidden:
            asyncio.run(endpoint("canvas-1", GroupMembershipPayload(
                project_id="project-1", expected_revision=1, group_id="g", member_id="m",
            ), x_user_id="user-1"))
        self.assertEqual(forbidden.exception.status_code, 403)

        invalid_router = create_canvas_nodes_router(
            service_for_actor=lambda actor: Service(),
            mutation_service_for_actor=lambda actor: MutationService(),
            graph_service_for_actor=lambda actor: GraphService(),
            group_service_for_actor=lambda actor: InvalidGroupService(),
            node_lookup=Lookup(),
        )
        invalid_endpoint = next(route.endpoint for route in invalid_router.routes if route.path.endswith("/graph/group-membership"))
        with self.assertRaises(HTTPException) as invalid:
            asyncio.run(invalid_endpoint("canvas-1", GroupMembershipPayload(
                project_id="project-1", expected_revision=1, group_id="g", member_id="ghost",
            ), x_user_id="user-1"))
        self.assertEqual(invalid.exception.status_code, 422)
