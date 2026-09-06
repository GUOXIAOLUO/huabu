"""Canonical Canvas transport API with explicit logical revision.

R4-05 seam: while the legacy ``/api/canvases`` endpoints remain the
compatibility transport, this router exposes the canonical SQLite semantics
directly — GET carries the logical ``revision``, PUT requires
``expected_revision`` compare-and-swap, and stale writes return structured
conflict information. The API serves only while SQLite authority is active;
anything else is an explicit 503, never a silent legacy fallback.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Protocol

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from workbench.application.authorization import AuthorizationError
from workbench.repositories.sqlite_project_canvas_repository import (
    LOCAL_WORKSPACE_ACTOR_ID,
    CanonicalNotFoundError,
    CanonicalRepositoryError,
    CanonicalStaleRevisionError,
    SqliteProjectCanvasRepository,
)


class CanonicalCanvasPutPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payload: dict[str, Any]
    expected_revision: int = Field(ge=1)


class _RepositoryFactory(Protocol):
    def __call__(self) -> SqliteProjectCanvasRepository: ...


def _require_canonical_authority(decision) -> None:
    if not decision.use_sqlite:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "canonical_canvas_api_requires_sqlite_authority",
                "authority_state": decision.authority_state,
                "reason": decision.reason,
            },
        )


def create_canonical_canvases_router(
    *,
    canonical_repository_factory: _RepositoryFactory,
    authority_decision_factory: Callable[[], Any],
) -> APIRouter:
    """Compose the canonical transport; dependencies are injected for testability."""
    router = APIRouter(prefix="/api/v1/canvases", tags=["canvas"])

    def _serialize(record) -> dict[str, Any]:
        return {
            "canvas_id": record.id,
            "project_id": record.project_id,
            "title": record.title,
            "revision": record.revision,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
            "deleted": record.deleted_at is not None,
        }

    @router.get("/{canvas_id}")
    async def get_canonical_canvas(canvas_id: str):
        _require_canonical_authority(authority_decision_factory())
        repository = canonical_repository_factory()
        try:
            record = repository.load_canvas_record(canvas_id)
            payload = repository.load_canvas_payload(canvas_id)
        except CanonicalNotFoundError:
            raise HTTPException(status_code=404, detail={"error": "canvas_not_found", "canvas_id": canvas_id})
        return {"canvas": payload, **_serialize(record)}

    @router.put("/{canvas_id}")
    async def put_canonical_canvas(canvas_id: str, body: CanonicalCanvasPutPayload):
        _require_canonical_authority(authority_decision_factory())
        repository = canonical_repository_factory()
        # payload.updated_at is display/compat metadata: the canonical transport
        # keeps it fresh server-side so the logical revision stays the only CAS.
        body.payload["updated_at"] = int(datetime.now(tz=UTC).timestamp() * 1000)
        try:
            record, payload = repository.replace_canvas_payload(
                actor_id=LOCAL_WORKSPACE_ACTOR_ID,
                canvas_id=canvas_id,
                expected_revision=body.expected_revision,
                payload=body.payload,
            )
        except CanonicalNotFoundError:
            raise HTTPException(status_code=404, detail={"error": "canvas_not_found", "canvas_id": canvas_id})
        except AuthorizationError:
            raise HTTPException(status_code=403, detail={"error": "forbidden", "canvas_id": canvas_id})
        except CanonicalStaleRevisionError as error:
            try:
                current = repository.load_canvas_record(canvas_id)
                current_payload = repository.load_canvas_payload(canvas_id)
                current_updated_at = current.updated_at.isoformat() if current.updated_at else None
            except CanonicalNotFoundError:
                current_payload = None
                current_updated_at = None
            # The current payload rides along so conflict-merging clients keep
            # their characterized recovery semantics.
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "stale_revision",
                    "message": "画布已被其他写入方更新，已拒绝基于过期修订的覆盖。",
                    "canvas_id": canvas_id,
                    "expected_revision": body.expected_revision,
                    "current_revision": error.current_revision,
                    "current_updated_at": current_updated_at,
                    "canvas": current_payload,
                },
            )
        except CanonicalRepositoryError as error:
            raise HTTPException(status_code=422, detail={"error": "canonical_canvas_error", "message": str(error)})
        return {"canvas": payload, **_serialize(record)}

    return router
