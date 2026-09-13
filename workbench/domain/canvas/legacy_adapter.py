"""Lossless read/write adapter between Legacy Canvas dictionaries and domain records."""

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from .models import EdgeRecord, NodeRecord, Position, RendererRef, Size
from .canonical_adapter import is_canonical_payload, record_from_payload
from .input_bindings import InputBindingAdapter
from .ports import InputPort, OutputPort, PortSet
from .states import NodeState


def _legacy_timestamp(value: Any) -> datetime:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000, tz=UTC)
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.fromtimestamp(0, tz=UTC)


def _legacy_kind(node_type: str) -> str:
    if node_type in {"image", "smart-image"}:
        return "asset"
    if node_type == "output":
        return "artifact"
    if node_type == "collection":
        return "collection"
    if node_type in {"group", "promptGroup", "smart-group"}:
        return "group"
    return "legacy"


def _legacy_state(node: dict[str, Any]) -> NodeState:
    raw_state = node.get("state") or node.get("status")
    try:
        return NodeState(raw_state) if raw_state else NodeState.READY
    except ValueError:
        return NodeState.READY


class LegacyCanvasAdapter:
    """Creates a validated view without changing the Legacy persistence shape."""

    LEGACY_EXTENSION_KEY = "legacy"
    DEFAULT_PORTS = PortSet(
        inputs=[InputPort(id="legacy.in", accepts=["legacy.any"], multiple=True)],
        outputs=[OutputPort(id="legacy.out", produces=["legacy.any"], multiple=True)],
    )

    @classmethod
    def node_to_record(cls, node: dict[str, Any], *, canvas: dict[str, Any]) -> NodeRecord:
        # A canonical node shares this one node list but is not a Legacy shape:
        # it is read back as the record it was stored as, not guessed at.
        if is_canonical_payload(node):
            return record_from_payload(node)
        payload = deepcopy(node)
        node_type = str(node.get("type") or "unknown")
        created_at = _legacy_timestamp(canvas.get("created_at"))
        updated_at = _legacy_timestamp(canvas.get("updated_at") or canvas.get("created_at"))
        width = float(node.get("w") or node.get("width") or 280)
        height = float(node.get("h") or node.get("height") or 180)
        return NodeRecord(
            id=str(node.get("id") or "legacy-node"),
            project_id=str(canvas.get("project") or "legacy-project"),
            canvas_id=str(canvas.get("id") or "legacy-canvas"),
            kind=_legacy_kind(node_type),
            definition_ref={"type": "legacy", "id": node_type, "version": "0"},
            renderer=RendererRef(id="legacy", version="1"),
            state=_legacy_state(node),
            title=str(node.get("title") or node.get("name") or node_type),
            position=Position(x=float(node.get("x") or 0), y=float(node.get("y") or 0)),
            size=Size(width=width, height=height),
            ports=cls.DEFAULT_PORTS.model_copy(deep=True),
            input_bindings=InputBindingAdapter.from_payloads(node.get("input_bindings", [])),
            created_by=str(canvas.get("owner") or "legacy-user"),
            created_at=created_at,
            updated_at=updated_at,
            revision=max(1, int(canvas.get("updated_at") or 1)),
            extensions={cls.LEGACY_EXTENSION_KEY: {"canvas_kind": canvas.get("kind"), "payload": payload}},
        )

    @classmethod
    def record_to_node(cls, record: NodeRecord) -> dict[str, Any]:
        legacy = record.extensions.get(cls.LEGACY_EXTENSION_KEY)
        payload = legacy.get("payload") if isinstance(legacy, dict) else None
        if not isinstance(payload, dict):
            raise ValueError("NodeRecord does not contain a lossless legacy payload")
        return deepcopy(payload)

    @classmethod
    def connection_to_record(cls, connection: dict[str, Any], *, canvas: dict[str, Any]) -> EdgeRecord:
        payload = deepcopy(connection)
        return EdgeRecord(
            id=str(connection.get("id") or f"legacy:{connection.get('from', '')}:{connection.get('to', '')}"),
            canvas_id=str(canvas.get("id") or "legacy-canvas"),
            **{
                "from": {"node_id": str(connection.get("from") or "legacy-source"), "port_id": "legacy.out"},
                "to": {"node_id": str(connection.get("to") or "legacy-target"), "port_id": "legacy.in"},
            },
            metadata={"legacy": {"payload": payload}},
            revision=max(1, int(canvas.get("updated_at") or 1)),
        )

    @classmethod
    def record_to_connection(cls, record: EdgeRecord) -> dict[str, Any]:
        legacy = record.metadata.get("legacy")
        payload = legacy.get("payload") if isinstance(legacy, dict) else None
        if not isinstance(payload, dict):
            raise ValueError("EdgeRecord does not contain a lossless legacy payload")
        return deepcopy(payload)

    @classmethod
    def canvas_to_records(cls, canvas: dict[str, Any]) -> tuple[list[NodeRecord], list[EdgeRecord]]:
        nodes = [cls.node_to_record(node, canvas=canvas) for node in canvas.get("nodes", [])]
        edges = [cls.connection_to_record(edge, canvas=canvas) for edge in canvas.get("connections", [])]
        return nodes, edges
