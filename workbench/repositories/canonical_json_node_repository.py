"""Canonical node persistence over the existing one-file-per-Canvas JSON store.

The only Canvas store is the Legacy JSON one, so the canonical execution-result
node is written into the same node list, under the same lock, with the same
idempotency convention as the Legacy writer. It is a separate class because it
answers a different question: the Legacy writer refuses anything that is not an
approved Legacy shape, and this one refuses anything that is not the approved
canonical shape. Neither is allowed to widen the other.
"""

from typing import Any

from workbench.application.node_creation import NodeCreationPersistence
from workbench.domain.canvas.canonical_adapter import payload_from_record, record_from_payload
from workbench.domain.canvas.models import CANONICAL_NODE_REQUEST_METADATA_KEY, DefinitionRef, NodeRecord

from .legacy_json_canvas_repository import LegacyJsonCanvasRepository


class CanonicalJsonNodeCreationRepository:
    """Persist the canonical execution-result node with durable idempotency."""

    APPROVED_DEFINITION = DefinitionRef(type="workbench", id="execution-result", version="1")
    REQUEST_METADATA_KEY = CANONICAL_NODE_REQUEST_METADATA_KEY

    def __init__(self, repository: LegacyJsonCanvasRepository):
        self._repository = repository

    def create_node(self, node: NodeRecord, *, expected_revision: int | None, request_id: str) -> NodeCreationPersistence:
        if node.definition_ref != self.APPROVED_DEFINITION:
            raise ValueError("this canonical node repository only supports the execution-result definition")

        result: NodeCreationPersistence | None = None

        def find_existing(canvas: dict[str, Any]) -> bool:
            nonlocal result
            for existing in canvas.get("nodes") or []:
                if isinstance(existing, dict) and existing.get(self.REQUEST_METADATA_KEY) == request_id:
                    result = NodeCreationPersistence(
                        node=record_from_payload(existing),
                        canvas_revision=int(canvas.get("updated_at") or 1),
                        created=False,
                    )
                    return True
            return False

        def append(canvas: dict[str, Any]) -> None:
            canvas.setdefault("nodes", []).append(payload_from_record(node, request_id=request_id))

        saved = self._repository.mutate_if_current(
            node.canvas_id,
            expected_updated_at=expected_revision,
            already_applied=find_existing,
            mutation=append,
        )
        if result is not None:
            return result
        return NodeCreationPersistence(
            node=node,
            canvas_revision=int(saved.get("updated_at") or 1),
            created=True,
        )
