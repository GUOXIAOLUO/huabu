"""Versioned Canvas-node API contract, intentionally independent of Legacy routes."""

from collections.abc import Callable
from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from workbench.application.node_creation import NodeCreateCommand, NodeCreationError, NodeCreationService, NodeCreationSource
from workbench.application.node_mutation import NodeDeleteCommand, NodeMutationError, NodeMutationService, NodeUpdateCommand
from workbench.application.graph_mutation import ConnectNodesCommand, CreateNodeAndEdgeFromCreationCommand, GraphMutationError, GraphMutationService
from workbench.application.group_mutation import GroupMembershipCommand, GroupMembershipService, GroupMutationError
from workbench.domain.canvas.models import DefinitionRef, ModelBinding, NodeRecord, Position
from workbench.repositories.canvas_repository import StaleCanvasRevisionError


class NodeCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1, max_length=255)
    project_id: str = Field(min_length=1, max_length=255)
    source: NodeCreationSource
    definition_ref: DefinitionRef
    position: Position
    expected_revision: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=500)
    initial_bindings: list[dict[str, Any]] = Field(default_factory=list)
    initial_config: dict[str, Any] = Field(default_factory=dict)
    requested_model_binding: ModelBinding | None = None
    approval_id: str | None = Field(default=None, max_length=255)


class NodeCreateResponse(BaseModel):
    node: dict[str, Any]
    canvas_revision: int = Field(ge=1)
    created: bool


class NodeUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1, max_length=255)
    expected_revision: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=500)
    position: Position | None = None


class NodeDeletePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1, max_length=255)
    expected_revision: int = Field(ge=1)


class CreateNodeAndEdgePayload(NodeCreatePayload):
    # Connected creation is a graph transaction and must always participate in
    # optimistic concurrency. Standalone NodeCreatePayload intentionally keeps
    # its Legacy-compatible optional revision contract.
    expected_revision: int = Field(ge=1)
    existing_node_id: str = Field(min_length=1, max_length=255)
    edge_id: str = Field(min_length=1, max_length=255)
    direction: str = Field(default="from_existing", pattern="^(from_existing|to_existing)$")


class ConnectNodesPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1, max_length=255)
    expected_revision: int = Field(ge=1)
    edge_id: str = Field(min_length=1, max_length=255)
    from_node_id: str = Field(min_length=1, max_length=255)
    to_node_id: str = Field(min_length=1, max_length=255)
    kind: str = Field(default="flow", pattern="^(flow|input)$")


class GroupMembershipPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1, max_length=255)
    expected_revision: int = Field(ge=1)
    group_id: str = Field(min_length=1, max_length=255)
    member_id: str = Field(min_length=1, max_length=255)
    operation: str = Field(default="add", pattern="^(add|remove)$")


class NodeLookup(Protocol):
    def get(self, *, actor_id: str, project_id: str, canvas_id: str, node_id: str) -> NodeRecord: ...


def _actor_from_header(x_user_id: str) -> str:
    actor_id = str(x_user_id or "").strip()
    if not actor_id:
        raise HTTPException(status_code=401, detail="X-User-ID is required for versioned Canvas-node APIs")
    if len(actor_id) > 255:
        raise HTTPException(status_code=400, detail="X-User-ID is too long")
    return actor_id


def create_canvas_nodes_router(
    *,
    service_for_actor: Callable[[str], NodeCreationService],
    mutation_service_for_actor: Callable[[str], NodeMutationService],
    graph_service_for_actor: Callable[[str], GraphMutationService],
    group_service_for_actor: Callable[[str], GroupMembershipService],
    node_lookup: NodeLookup,
) -> APIRouter:
    """Build a router only after the host provides real authorization adapters."""
    router = APIRouter(prefix="/api/v1/canvases", tags=["canvas-nodes"])

    @router.post("/{canvas_id}/nodes", response_model=NodeCreateResponse, status_code=201)
    async def create_node(canvas_id: str, payload: NodeCreatePayload, x_user_id: str = Header(default="")):
        actor_id = _actor_from_header(x_user_id)
        service = service_for_actor(actor_id)
        try:
            result = service.create(
                NodeCreateCommand(
                    request_id=payload.request_id,
                    actor_id=actor_id,
                    project_id=payload.project_id,
                    canvas_id=canvas_id,
                    source=payload.source,
                    definition_ref=payload.definition_ref,
                    position=payload.position,
                    expected_revision=payload.expected_revision,
                    title=payload.title,
                    initial_bindings=tuple(payload.initial_bindings),
                    initial_config=payload.initial_config,
                    requested_model_binding=payload.requested_model_binding,
                    approval_id=payload.approval_id,
                )
            )
        except NodeCreationError as error:
            status_code = 403 if error.code == "forbidden" else 409 if error.code == "stale_revision" else 422
            raise HTTPException(status_code=status_code, detail={"code": error.code, "message": str(error)})
        except StaleCanvasRevisionError as error:
            raise HTTPException(status_code=409, detail={
                "code": "stale_revision",
                "message": "the Canvas revision is no longer current",
                "canvas": error.current,
            })
        return NodeCreateResponse(
            node=result.node.model_dump(mode="json"),
            canvas_revision=result.canvas_revision,
            created=result.created,
        )

    @router.get("/{canvas_id}/nodes/{node_id}")
    async def get_node(canvas_id: str, node_id: str, project_id: str, x_user_id: str = Header(default="")):
        actor_id = _actor_from_header(x_user_id)
        try:
            node = node_lookup.get(actor_id=actor_id, project_id=project_id, canvas_id=canvas_id, node_id=node_id)
        except LookupError:
            raise HTTPException(status_code=404, detail="node not found")
        return {"node": node.model_dump(mode="json")}

    @router.put("/{canvas_id}/nodes/{node_id}")
    async def update_node(canvas_id: str, node_id: str, payload: NodeUpdatePayload, x_user_id: str = Header(default="")):
        actor_id = _actor_from_header(x_user_id)
        try:
            result = mutation_service_for_actor(actor_id).update(NodeUpdateCommand(
                actor_id=actor_id, project_id=payload.project_id, canvas_id=canvas_id, node_id=node_id,
                expected_revision=payload.expected_revision, title=payload.title, position=payload.position,
            ))
        except NodeMutationError as error:
            raise _mutation_http_error(error)
        except LookupError:
            raise HTTPException(status_code=404, detail="node not found")
        except StaleCanvasRevisionError as error:
            raise HTTPException(status_code=409, detail={
                "code": "stale_revision", "message": "the Canvas revision is no longer current", "canvas": error.current,
            })
        return {"node": result.node.model_dump(mode="json"), "canvas_revision": result.canvas_revision}

    @router.delete("/{canvas_id}/nodes/{node_id}")
    async def delete_node(canvas_id: str, node_id: str, payload: NodeDeletePayload, x_user_id: str = Header(default="")):
        actor_id = _actor_from_header(x_user_id)
        try:
            result = mutation_service_for_actor(actor_id).delete(NodeDeleteCommand(
                actor_id=actor_id, project_id=payload.project_id, canvas_id=canvas_id, node_id=node_id,
                expected_revision=payload.expected_revision,
            ))
        except NodeMutationError as error:
            raise _mutation_http_error(error)
        except LookupError:
            raise HTTPException(status_code=404, detail="node not found")
        except StaleCanvasRevisionError as error:
            raise HTTPException(status_code=409, detail={
                "code": "stale_revision", "message": "the Canvas revision is no longer current", "canvas": error.current,
            })
        return {"deleted": True, "canvas_revision": result.canvas_revision}

    @router.post("/{canvas_id}/graph/create-node-and-edge", status_code=201)
    async def create_node_and_edge(canvas_id: str, payload: CreateNodeAndEdgePayload, x_user_id: str = Header(default="")):
        actor_id = _actor_from_header(x_user_id)
        creation = NodeCreateCommand(
            request_id=payload.request_id, actor_id=actor_id, project_id=payload.project_id, canvas_id=canvas_id,
            source=payload.source, definition_ref=payload.definition_ref, position=payload.position,
            expected_revision=payload.expected_revision, title=payload.title, initial_bindings=tuple(payload.initial_bindings),
            initial_config=payload.initial_config, requested_model_binding=payload.requested_model_binding, approval_id=payload.approval_id,
        )
        try:
            result = graph_service_for_actor(actor_id).create_from_node_command(
                CreateNodeAndEdgeFromCreationCommand(creation=creation, edge_id=payload.edge_id,
                    existing_node_id=payload.existing_node_id, direction=payload.direction),
                node_preparer=service_for_actor(actor_id),
            )
        except GraphMutationError as error:
            status_code = 403 if error.code == "forbidden" else 422
            raise HTTPException(status_code=status_code, detail={"code": error.code, "message": str(error)})
        except StaleCanvasRevisionError as error:
            raise HTTPException(status_code=409, detail={"code": "stale_revision", "canvas": error.current})
        return {"node": result.node.model_dump(mode="json"), "edge": result.edge.model_dump(mode="json", by_alias=True), "canvas_revision": result.canvas_revision}

    @router.post("/{canvas_id}/graph/connect-nodes", status_code=201)
    async def connect_nodes(canvas_id: str, payload: ConnectNodesPayload, x_user_id: str = Header(default="")):
        actor_id = _actor_from_header(x_user_id)
        try:
            result = graph_service_for_actor(actor_id).connect_nodes(ConnectNodesCommand(
                actor_id=actor_id, project_id=payload.project_id, canvas_id=canvas_id,
                expected_revision=payload.expected_revision, edge_id=payload.edge_id,
                from_node_id=payload.from_node_id, to_node_id=payload.to_node_id, edge_kind=payload.kind,
            ))
        except GraphMutationError as error:
            status_code = 403 if error.code == "forbidden" else 422
            raise HTTPException(status_code=status_code, detail={"code": error.code, "message": str(error)})
        except StaleCanvasRevisionError as error:
            raise HTTPException(status_code=409, detail={"code": "stale_revision", "canvas": error.current})
        return {"edge": result.edge.model_dump(mode="json", by_alias=True), "canvas_revision": result.canvas_revision}

    @router.post("/{canvas_id}/graph/group-membership")
    async def set_group_membership(canvas_id: str, payload: GroupMembershipPayload, x_user_id: str = Header(default="")):
        actor_id = _actor_from_header(x_user_id)
        try:
            result = group_service_for_actor(actor_id).set_membership(GroupMembershipCommand(
                actor_id=actor_id, project_id=payload.project_id, canvas_id=canvas_id,
                expected_revision=payload.expected_revision, group_id=payload.group_id,
                member_id=payload.member_id, operation=payload.operation,
            ))
        except GroupMutationError as error:
            status_code = 403 if error.code == "forbidden" else 422
            raise HTTPException(status_code=status_code, detail={"code": error.code, "message": str(error)})
        except StaleCanvasRevisionError as error:
            raise HTTPException(status_code=409, detail={"code": "stale_revision", "canvas": error.current})
        return {"group": result.group.model_dump(mode="json"), "canvas_revision": result.canvas_revision}

    return router


def _mutation_http_error(error: NodeMutationError) -> HTTPException:
    status_code = 403 if error.code == "forbidden" else 422
    return HTTPException(status_code=status_code, detail={"code": error.code, "message": str(error)})
