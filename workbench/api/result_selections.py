"""Versioned HTTP API for per-result user preference metadata."""

from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from workbench.application.result_selection_service import ResultSelectionNotFoundServiceError, ResultSelectionService, ResultSelectionServiceError
from workbench.domain.execution import RESULT_SELECTION_MAX_COMMENT_LENGTH, RESULT_SELECTION_MAX_RATING, RESULT_SELECTION_MIN_RATING, ResultSelection


class ResultSelectionCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    attempt_id: str = Field(min_length=1, max_length=255)
    output_name: str = Field(min_length=1, max_length=255)
    ordinal: int = Field(ge=0)
    selected: bool = False
    favorite: bool = False
    rating: int | None = Field(default=None, ge=RESULT_SELECTION_MIN_RATING, le=RESULT_SELECTION_MAX_RATING)
    comment: str = Field(default="", max_length=RESULT_SELECTION_MAX_COMMENT_LENGTH)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResultSelectionUpdatePayload(BaseModel):
    """A restatement of the whole preference, not a partial patch.

    Sending the full preference keeps a cleared rating unambiguous: `rating:
    null` means "no rating", which a partial patch could not express.
    """

    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=1)
    selected: bool
    favorite: bool
    rating: int | None = Field(default=None, ge=RESULT_SELECTION_MIN_RATING, le=RESULT_SELECTION_MAX_RATING)
    comment: str = Field(default="", max_length=RESULT_SELECTION_MAX_COMMENT_LENGTH)
    metadata: dict[str, Any] = Field(default_factory=dict)


class _ServiceFactory(Protocol):
    def __call__(self, actor_id: str) -> ResultSelectionService: ...


def _actor(value: str) -> str:
    actor = value.strip()
    if not actor or len(actor) > 255:
        raise HTTPException(status_code=401, detail="X-User-ID is required")
    return actor


def _error(error: ResultSelectionServiceError) -> HTTPException:
    if isinstance(error, ResultSelectionNotFoundServiceError): code = 404
    elif error.code in {"stale_revision", "conflict"}: code = 409
    else: code = 400
    return HTTPException(status_code=code, detail={"code": error.code, "message": str(error)})


def create_result_selections_router(*, service_factory: _ServiceFactory) -> APIRouter:
    router = APIRouter(prefix="/api/v1/execution-runs/{run_id}/selections", tags=["result-selections"])

    @router.post("", response_model=ResultSelection, status_code=status.HTTP_201_CREATED)
    async def create_selection(run_id: str, payload: ResultSelectionCreatePayload, x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).create(run_id=run_id, **payload.model_dump())
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ResultSelectionServiceError as error: raise _error(error) from error

    @router.get("", response_model=list[ResultSelection])
    async def list_selections(run_id: str, x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).list_for_run(run_id)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ResultSelectionServiceError as error: raise _error(error) from error

    @router.get("/{selection_id}", response_model=ResultSelection)
    async def get_selection(run_id: str, selection_id: str, x_user_id: str = Header(default="")):
        try:
            selection = service_factory(_actor(x_user_id)).get(selection_id)
            if selection.run_id != run_id: raise ResultSelectionNotFoundServiceError(selection_id)
            return selection
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ResultSelectionServiceError as error: raise _error(error) from error

    @router.put("/{selection_id}", response_model=ResultSelection)
    async def update_selection(run_id: str, selection_id: str, payload: ResultSelectionUpdatePayload, x_user_id: str = Header(default="")):
        try:
            service = service_factory(_actor(x_user_id))
            current = service.get(selection_id)
            if current.run_id != run_id: raise ResultSelectionNotFoundServiceError(selection_id)
            return service.update(selection_id, **payload.model_dump())
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ResultSelectionServiceError as error: raise _error(error) from error

    return router
