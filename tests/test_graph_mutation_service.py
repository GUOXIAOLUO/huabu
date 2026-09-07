import unittest
from datetime import UTC, datetime

from workbench.application.graph_mutation import (
    ConnectNodesCommand,
    ConnectNodesPersistence,
    CreateNodeAndEdgeCommand,
    CreateNodeAndEdgeFromCreationCommand,
    GraphMutationError,
    GraphMutationPersistence,
    GraphMutationService,
)
from workbench.application.node_creation import NodeCreateCommand, NodeCreationSource
from workbench.domain.canvas.models import DefinitionRef, EdgeRecord, NodeRecord, Position, RendererRef, Size
from workbench.domain.canvas.ports import PortSet
from workbench.domain.canvas.states import NodeState


def node():
    return NodeRecord(id="new", project_id="project", canvas_id="canvas", kind="group", definition_ref=DefinitionRef(type="legacy", id="group", version="0"), renderer=RendererRef(id="legacy", version="1"), state=NodeState.READY, title="Group", position=Position(x=1, y=2), size=Size(width=300, height=220), ports=PortSet(), created_by="actor", created_at=datetime(2026, 9, 2, tzinfo=UTC), updated_at=datetime(2026, 9, 2, tzinfo=UTC))


def edge():
    return EdgeRecord(id="edge", canvas_id="canvas", **{"from": {"node_id": "new", "port_id": "legacy.out"}, "to": {"node_id": "old", "port_id": "legacy.in"}})


class Auth:
    def __init__(self, allowed=True): self.allowed = allowed
    def can_edit(self, *args): return self.allowed


class Repository:
    def create_node_and_edge(self, command): return GraphMutationPersistence(canvas_revision=2, node=command.node, edge=command.edge)

    def connect_nodes(self, command, edge): return ConnectNodesPersistence(canvas_revision=3, edge=edge)


class Preparer:
    def prepare(self, command): return node(), object(), datetime(2026, 9, 2, tzinfo=UTC)


class Audit:
    def __init__(self): self.events = []
    def append(self, event): self.events.append(event)


class GraphMutationServiceTests(unittest.TestCase):
    def command(self, **changes):
        values = dict(actor_id="actor", project_id="project", canvas_id="canvas", expected_revision=1, node=node(), edge=edge())
        values.update(changes)
        return CreateNodeAndEdgeCommand(**values)

    def test_authorized_graph_transaction_requires_new_node_edge_reference(self):
        audit = Audit()
        result = GraphMutationService(authorizer=Auth(), repository=Repository(), audit_sink=audit).create_node_and_edge(self.command())
        self.assertEqual(result.canvas_revision, 2)
        self.assertEqual(audit.events[0].edge_id, "edge")
        disconnected = EdgeRecord(id="bad", canvas_id="canvas", **{"from": {"node_id": "old", "port_id": "out"}, "to": {"node_id": "other", "port_id": "in"}})
        with self.assertRaisesRegex(GraphMutationError, "reference"):
            GraphMutationService(authorizer=Auth(), repository=Repository(), audit_sink=Audit()).create_node_and_edge(self.command(edge=disconnected))

    def test_rejects_unauthorized_graph_mutation(self):
        with self.assertRaisesRegex(GraphMutationError, "not permitted"):
            GraphMutationService(authorizer=Auth(False), repository=Repository(), audit_sink=Audit()).create_node_and_edge(self.command())

    def test_rejects_zero_or_negative_graph_revision_before_persistence(self):
        service = GraphMutationService(authorizer=Auth(), repository=Repository(), audit_sink=Audit())
        for revision in (0, -1):
            with self.subTest(revision=revision), self.assertRaisesRegex(GraphMutationError, "expected_revision must be positive"):
                service.create_node_and_edge(self.command(expected_revision=revision))

    def test_constructs_edge_from_shared_node_creation_command(self):
        creation = NodeCreateCommand(request_id="request", actor_id="actor", project_id="project", canvas_id="canvas", source=NodeCreationSource.CONTEXT_MENU, definition_ref=DefinitionRef(type="legacy", id="group", version="0"), position=Position(x=1, y=2), expected_revision=1)
        result = GraphMutationService(authorizer=Auth(), repository=Repository(), audit_sink=Audit()).create_from_node_command(
            CreateNodeAndEdgeFromCreationCommand(creation=creation, edge_id="edge", existing_node_id="old"), node_preparer=Preparer(),
        )
        self.assertEqual(result.edge.to.node_id, "new")

    def test_constructs_reverse_edge_with_the_same_legacy_port_contract(self):
        creation = NodeCreateCommand(request_id="request", actor_id="actor", project_id="project", canvas_id="canvas", source=NodeCreationSource.CONTEXT_MENU, definition_ref=DefinitionRef(type="legacy", id="group", version="0"), position=Position(x=1, y=2), expected_revision=1)
        result = GraphMutationService(authorizer=Auth(), repository=Repository(), audit_sink=Audit()).create_from_node_command(
            CreateNodeAndEdgeFromCreationCommand(creation=creation, edge_id="edge", existing_node_id="old", direction="to_existing"), node_preparer=Preparer(),
        )
        self.assertEqual(result.edge.from_.node_id, "new")
        self.assertEqual(result.edge.from_.port_id, "legacy.out")
        self.assertEqual(result.edge.to.node_id, "old")
        self.assertEqual(result.edge.to.port_id, "legacy.in")

    def test_connected_creation_requires_revision_before_preparing_a_node(self):
        creation = NodeCreateCommand(request_id="request", actor_id="actor", project_id="project", canvas_id="canvas", source=NodeCreationSource.CONTEXT_MENU, definition_ref=DefinitionRef(type="legacy", id="group", version="0"), position=Position(x=1, y=2))

        class NeverPrepare:
            def prepare(self, command):
                self.fail("a missing graph revision must not prepare a node")

        with self.assertRaisesRegex(GraphMutationError, "expected_revision is required"):
            GraphMutationService(authorizer=Auth(), repository=Repository(), audit_sink=Audit()).create_from_node_command(
                CreateNodeAndEdgeFromCreationCommand(creation=creation, edge_id="edge", existing_node_id="old"), node_preparer=NeverPrepare(),
            )

    def connect_command(self, **changes):
        values = dict(actor_id="actor", project_id="project", canvas_id="canvas", expected_revision=5, edge_id="edge-1", from_node_id="a", to_node_id="b")
        values.update(changes)
        return ConnectNodesCommand(**values)

    def test_authorized_connect_builds_the_legacy_edge_and_audits(self):
        audit = Audit()
        result = GraphMutationService(authorizer=Auth(), repository=Repository(), audit_sink=audit).connect_nodes(self.connect_command())
        self.assertEqual(result.canvas_revision, 3)
        self.assertEqual((result.edge.id, result.edge.from_.node_id, result.edge.to.node_id, result.edge.from_.port_id, result.edge.to.port_id), (
            "edge-1", "a", "b", "legacy.out", "legacy.in",
        ))
        self.assertEqual((audit.events[0].edge_id, audit.events[0].from_node_id, audit.events[0].to_node_id), (
            "edge-1", "a", "b",
        ))

    def test_connect_rejects_self_edges_before_persistence(self):
        service = GraphMutationService(authorizer=Auth(), repository=Repository(), audit_sink=Audit())
        with self.assertRaisesRegex(GraphMutationError, "cannot connect a node to itself"):
            service.connect_nodes(self.connect_command(from_node_id="a", to_node_id="a"))

    def test_connect_rejects_invalid_revisions_and_kinds_before_persistence(self):
        service = GraphMutationService(authorizer=Auth(), repository=Repository(), audit_sink=Audit())
        for revision in (0, -1):
            with self.subTest(revision=revision), self.assertRaisesRegex(GraphMutationError, "expected_revision must be positive"):
                service.connect_nodes(self.connect_command(expected_revision=revision))
        with self.assertRaisesRegex(GraphMutationError, "edge_kind"):
            service.connect_nodes(self.connect_command(edge_kind="dashed"))
        with self.assertRaisesRegex(GraphMutationError, "required"):
            service.connect_nodes(self.connect_command(edge_id=" "))

    def test_connect_rejects_unauthorized_mutation(self):
        with self.assertRaisesRegex(GraphMutationError, "not permitted"):
            GraphMutationService(authorizer=Auth(False), repository=Repository(), audit_sink=Audit()).connect_nodes(self.connect_command())
