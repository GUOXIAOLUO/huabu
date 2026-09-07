"""Atomic, industry-neutral graph mutations for migrated Canvas actions."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Callable, Protocol

from workbench.application.node_creation import ProjectAuthorizer
from workbench.application.node_creation import NodeCreateCommand
from workbench.domain.canvas.models import EdgeRecord, NodeRecord


class GraphMutationError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class CreateNodeAndEdgeCommand:
    actor_id: str
    project_id: str
    canvas_id: str
    expected_revision: int
    node: NodeRecord
    edge: EdgeRecord


@dataclass(frozen=True)
class CreateNodeAndEdgeFromCreationCommand:
    creation: NodeCreateCommand
    edge_id: str
    existing_node_id: str
    direction: str = "from_existing"


@dataclass(frozen=True)
class ConnectNodesCommand:
    """Connect two existing Canvas nodes with one durable edge.

    The application boundary owns request validity, authorization, and
    optimistic concurrency; endpoint existence, duplicate edges, and the
    retained adapter edge shapes stay behind the repository port.
    """

    actor_id: str
    project_id: str
    canvas_id: str
    expected_revision: int
    edge_id: str
    from_node_id: str
    to_node_id: str
    edge_kind: str = "flow"


@dataclass(frozen=True)
class GraphMutationPersistence:
    canvas_revision: int
    node: NodeRecord
    edge: EdgeRecord


@dataclass(frozen=True)
class ConnectNodesPersistence:
    canvas_revision: int
    edge: EdgeRecord


@dataclass(frozen=True)
class NodeAndEdgeCreatedAuditEvent:
    actor_id: str
    project_id: str
    canvas_id: str
    node_id: str
    edge_id: str
    occurred_at: datetime


@dataclass(frozen=True)
class NodesConnectedAuditEvent:
    actor_id: str
    project_id: str
    canvas_id: str
    edge_id: str
    from_node_id: str
    to_node_id: str
    occurred_at: datetime


class AtomicGraphMutationRepository(Protocol):
    def create_node_and_edge(self, command: CreateNodeAndEdgeCommand) -> GraphMutationPersistence: ...

    def connect_nodes(self, command: ConnectNodesCommand, edge: EdgeRecord) -> ConnectNodesPersistence: ...


class NodePreparer(Protocol):
    def prepare(self, command: NodeCreateCommand) -> tuple[NodeRecord, object, datetime]: ...


class AuditSink(Protocol):
    def append(self, event: NodeAndEdgeCreatedAuditEvent) -> None: ...


class GraphMutationService:
    """Authorizes a graph transaction before infrastructure mutates persistence."""

    def __init__(self, *, authorizer: ProjectAuthorizer, repository: AtomicGraphMutationRepository, audit_sink: AuditSink, clock: Callable[[], datetime] | None = None):
        self._authorizer = authorizer
        self._repository = repository
        self._audit_sink = audit_sink
        self._clock = clock or (lambda: datetime.now(UTC))

    def create_node_and_edge(self, command: CreateNodeAndEdgeCommand) -> GraphMutationPersistence:
        if not all(str(value or "").strip() for value in (command.actor_id, command.project_id, command.canvas_id)):
            raise GraphMutationError("invalid_request", "actor_id, project_id, and canvas_id are required")
        if command.expected_revision < 1:
            raise GraphMutationError("invalid_request", "expected_revision must be positive")
        if command.node.canvas_id != command.canvas_id or command.edge.canvas_id != command.canvas_id:
            raise GraphMutationError("invalid_graph", "node and edge must belong to the target Canvas")
        if command.edge.from_.node_id != command.node.id and command.edge.to.node_id != command.node.id:
            raise GraphMutationError("invalid_graph", "the new edge must reference the new node")
        if not self._authorizer.can_edit(command.actor_id, command.project_id, command.canvas_id):
            raise GraphMutationError("forbidden", "actor is not permitted to edit this Canvas")
        persisted = self._repository.create_node_and_edge(command)
        self._audit_sink.append(NodeAndEdgeCreatedAuditEvent(
            actor_id=command.actor_id, project_id=command.project_id, canvas_id=command.canvas_id,
            node_id=persisted.node.id, edge_id=persisted.edge.id, occurred_at=self._clock(),
        ))
        return persisted

    def create_from_node_command(self, command: CreateNodeAndEdgeFromCreationCommand, *, node_preparer: NodePreparer) -> GraphMutationPersistence:
        if command.creation.expected_revision is None:
            raise GraphMutationError("invalid_request", "expected_revision is required for connected creation")
        node, _, _ = node_preparer.prepare(command.creation)
        if not command.edge_id or not command.existing_node_id:
            raise GraphMutationError("invalid_request", "edge_id and existing_node_id are required")
        if command.direction not in {"from_existing", "to_existing"}:
            raise GraphMutationError("invalid_request", "direction is invalid")
        source, target = (command.existing_node_id, node.id) if command.direction == "from_existing" else (node.id, command.existing_node_id)
        edge = EdgeRecord(id=command.edge_id, canvas_id=node.canvas_id, **{
            "from": {"node_id": source, "port_id": "legacy.out"},
            "to": {"node_id": target, "port_id": "legacy.in"},
        })
        return self.create_node_and_edge(CreateNodeAndEdgeCommand(
            actor_id=command.creation.actor_id, project_id=command.creation.project_id, canvas_id=command.creation.canvas_id,
            expected_revision=command.creation.expected_revision, node=node, edge=edge,
        ))

    def connect_nodes(self, command: ConnectNodesCommand) -> ConnectNodesPersistence:
        if not all(str(value or "").strip() for value in (
            command.actor_id, command.project_id, command.canvas_id,
            command.edge_id, command.from_node_id, command.to_node_id,
        )):
            raise GraphMutationError("invalid_request", "actor_id, project_id, canvas_id, edge_id, from_node_id, and to_node_id are required")
        if command.expected_revision < 1:
            raise GraphMutationError("invalid_request", "expected_revision must be positive")
        if command.from_node_id == command.to_node_id:
            raise GraphMutationError("invalid_graph", "an edge cannot connect a node to itself")
        if command.edge_kind not in {"flow", "input"}:
            raise GraphMutationError("invalid_request", "edge_kind must be flow or input")
        if not self._authorizer.can_edit(command.actor_id, command.project_id, command.canvas_id):
            raise GraphMutationError("forbidden", "actor is not permitted to edit this Canvas")
        edge = EdgeRecord(id=command.edge_id, canvas_id=command.canvas_id, **{
            "from": {"node_id": command.from_node_id, "port_id": "legacy.out"},
            "to": {"node_id": command.to_node_id, "port_id": "legacy.in"},
        })
        persisted = self._repository.connect_nodes(command, edge)
        self._audit_sink.append(NodesConnectedAuditEvent(
            actor_id=command.actor_id, project_id=command.project_id, canvas_id=command.canvas_id,
            edge_id=persisted.edge.id, from_node_id=command.from_node_id, to_node_id=command.to_node_id,
            occurred_at=self._clock(),
        ))
        return persisted
