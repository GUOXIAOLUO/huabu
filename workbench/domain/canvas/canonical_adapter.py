"""Lossless read/write adapter for canonical nodes carried by the Legacy JSON store.

The Legacy store is one list of nodes per Canvas, so a canonical node is stored
in that same list under a marker ``type`` Legacy consumers already see but never
produce. Two things follow from sharing the list, and both are handled here
rather than at the writer:

- The canonical record is stored whole, so reading it back is validation rather
  than guesswork.
- ``x``/``y``/``w``/``h`` are repeated alongside it, so a consumer that only
  understands Legacy geometry can still place the node. They are copies of the
  record's own position and size, never a second source of truth.
"""

from copy import deepcopy
from typing import Any

from .models import (
    CANONICAL_NODE_REQUEST_METADATA_KEY,
    CANONICAL_RESULT_NODE_TYPE,
    NodeRecord,
)


def is_canonical_payload(node: dict[str, Any]) -> bool:
    return str(node.get("type") or "") == CANONICAL_RESULT_NODE_TYPE


def record_from_payload(node: dict[str, Any]) -> NodeRecord:
    """Rebuild the stored canonical record, dropping what only the store needs."""
    payload = deepcopy(node)
    for key in ("type", "x", "y", "w", "h", CANONICAL_NODE_REQUEST_METADATA_KEY):
        payload.pop(key, None)
    return NodeRecord.model_validate(payload)


def payload_from_record(record: NodeRecord, *, request_id: str) -> dict[str, Any]:
    """Store one canonical record plus the Legacy-visible geometry and marker."""
    payload = record.model_dump(mode="json")
    payload["type"] = CANONICAL_RESULT_NODE_TYPE
    payload["x"] = record.position.x
    payload["y"] = record.position.y
    payload["w"] = record.size.width
    payload["h"] = record.size.height
    payload[CANONICAL_NODE_REQUEST_METADATA_KEY] = request_id
    return payload
