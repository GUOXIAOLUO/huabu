"""Versioned HTTP API for putting produced results into a Collection."""

from typing import Protocol

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from workbench.application.result_collection_service import ResultCollectionNotFoundServiceError, ResultCollectionService, ResultCollectionServiceError
from workbench.domain.collection import Collection


class ResultCollectionAddPayload(BaseModel):
    """One request to populate a Collection from a run's selected results.

    The expected revision is required rather than defaulted: appending to a
    Collection is a write to a shared aggregate, so a caller that does not know
    the current revision must go and look.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1, max_length=255)
    expected_revision: int = Field(ge=1)
    column_key: str = Field(default="result", min_length=1, max_length=255)


class _ServiceFactory(Protocol):
    def __call__(self, actor_id: str) -> ResultCollectionService: ...


def _actor(value: str) -> str:
    actor = value.strip()
    if not actor or len(actor) > 255:
        raise HTTPException(status_code=401, detail="X-User-ID is required")
    return actor


def _error(error: ResultCollectionServiceError) -> HTTPException:
    if isinstance(error, ResultCollectionNotFoundServiceError):
        code = 404
    elif error.code == "stale_revision":
        code = 409
    else:
        code = 400
    return HTTPException(status_code=code, detail={"code": error.code, "message": str(error)})


def create_result_collections_router(*, service_factory: _ServiceFactory) -> APIRouter:
    router = APIRouter(prefix="/api/v1/collections/{collection_id}", tags=["result-collections"])

    @router.post("/results", response_model=Collection)
    async def add_selected_results(collection_id: str, payload: ResultCollectionAddPayload, x_user_id: str = Header(default="")):
        try:
            return service_factory(_actor(x_user_id)).add_selected(
                collection_id=collection_id, run_id=payload.run_id,
                expected_revision=payload.expected_revision, column_key=payload.column_key,
            )
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except ResultCollectionServiceError as error:
            raise _error(error) from error

    return router
