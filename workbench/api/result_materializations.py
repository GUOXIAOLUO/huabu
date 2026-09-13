"""Versioned HTTP API for putting a produced result onto a Canvas as a node."""

from typing import Protocol

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from workbench.application.result_materialization_service import (
    ResultMaterializationNotFoundServiceError,
    ResultMaterializationService,
    ResultMaterializationServiceError,
)
from workbench.domain.canvas.models import Position
from workbench.repositories.canvas_repository import StaleCanvasRevisionError


class ResultMaterializationPayload(BaseModel):
    """One request to materialize one result as one Canvas node.

    Every part of the result's address is required: naming an attempt without an
    output, or an output without its occurrence, would put a node on the Canvas
    that points at a different result than the caller meant.
    """

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1, max_length=255)
    project_id: str = Field(min_length=1, max_length=255)
    run_id: str = Field(min_length=1, max_length=255)
    attempt_id: str = Field(min_length=1, max_length=255)
    output_name: str = Field(min_length=1, max_length=255)
    ordinal: int = Field(ge=0)
    position: Position
    expected_revision: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=500)


class _ServiceFactory(Protocol):
    def __call__(self, actor_id: str) -> ResultMaterializationService: ...


def _actor(value: str) -> str:
    actor = value.strip()
    if not actor or len(actor) > 255:
        raise HTTPException(status_code=401, detail="X-User-ID is required")
    return actor


def _error(error: ResultMaterializationServiceError) -> HTTPException:
    if isinstance(error, ResultMaterializationNotFoundServiceError):
        code = 404
    elif error.code in {"stale_revision", "result_not_selected"}:
        code = 409
    elif error.code == "forbidden":
        code = 403
    elif error.code == "invalid_request":
        code = 422
    else:
        code = 400
    return HTTPException(status_code=code, detail={"code": error.code, "message": str(error)})


def create_result_materializations_router(*, service_factory: _ServiceFactory) -> APIRouter:
    router = APIRouter(prefix="/api/v1/canvases/{canvas_id}", tags=["result-materializations"])

    @router.post("/result-nodes", status_code=201)
    async def materialize_result(canvas_id: str, payload: ResultMaterializationPayload, x_user_id: str = Header(default="")):
        try:
            result = service_factory(_actor(x_user_id)).materialize(
                request_id=payload.request_id, project_id=payload.project_id, canvas_id=canvas_id,
                run_id=payload.run_id, attempt_id=payload.attempt_id, output_name=payload.output_name,
                ordinal=payload.ordinal, position=payload.position,
                expected_revision=payload.expected_revision, title=payload.title,
            )
        except StaleCanvasRevisionError as error:
            raise HTTPException(status_code=409, detail={
                "code": "stale_revision",
                "message": "the Canvas revision is no longer current",
                "canvas": error.current,
            }) from error
        except ResultMaterializationServiceError as error:
            raise _error(error) from error
        return {
            "node": result.node.model_dump(mode="json"),
            "canvas_revision": result.canvas_revision,
            "created": result.created,
        }

    return router
