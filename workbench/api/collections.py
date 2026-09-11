"""Versioned canonical Collection API."""

from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from workbench.application.collection_service import CollectionNotFoundServiceError, CollectionService, CollectionServiceError
from workbench.domain.collection import Collection, CollectionItem, CollectionSchema


class CanonicalCollectionCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=255)
    collection_schema: CollectionSchema = Field(alias="schema")
    items: list[CollectionItem] = Field(default_factory=list)
    default_view: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CanonicalCollectionUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    collection_schema: CollectionSchema | None = Field(default=None, alias="schema")
    items: list[CollectionItem] | None = None
    default_view: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class _CollectionServiceFactory(Protocol):
    def __call__(self, actor_id: str) -> CollectionService: ...


def _actor(x_user_id: str) -> str:
    actor_id = x_user_id.strip()
    if not actor_id or len(actor_id) > 255:
        raise HTTPException(status_code=401, detail="X-User-ID is required")
    return actor_id


def _error(error: CollectionServiceError) -> HTTPException:
    if isinstance(error, CollectionNotFoundServiceError):
        code = 404
    elif error.code == "stale_revision":
        code = 409
    elif error.code == "forbidden":
        code = 403
    else:
        code = 400
    return HTTPException(status_code=code, detail={"code": error.code, "message": str(error)})


def create_canonical_collections_router(*, service_factory: _CollectionServiceFactory) -> APIRouter:
    router = APIRouter(prefix="/api/v1/collections", tags=["collections"])

    @router.get("", response_model=list[Collection])
    async def list_collections(project_id: str = Query(min_length=1, max_length=255), x_user_id: str = Header(default="")):
        try:
            return service_factory(_actor(x_user_id)).list(project_id)
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error

    @router.get("/{collection_id}", response_model=Collection)
    async def get_collection(collection_id: str, x_user_id: str = Header(default="")):
        try:
            return service_factory(_actor(x_user_id)).get(collection_id)
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except CollectionServiceError as error:
            raise _error(error) from error

    @router.post("", response_model=Collection, status_code=status.HTTP_201_CREATED)
    async def create_collection(payload: CanonicalCollectionCreatePayload, x_user_id: str = Header(default="")):
        try:
            return service_factory(_actor(x_user_id)).create(project_id=payload.project_id, name=payload.name, schema=payload.collection_schema, items=payload.items, default_view=payload.default_view, metadata=payload.metadata)
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except CollectionServiceError as error:
            raise _error(error) from error

    @router.put("/{collection_id}", response_model=Collection)
    async def update_collection(collection_id: str, payload: CanonicalCollectionUpdatePayload, x_user_id: str = Header(default="")):
        try:
            return service_factory(_actor(x_user_id)).update(collection_id, expected_revision=payload.expected_revision, name=payload.name, schema=payload.collection_schema, items=payload.items, default_view=payload.default_view, metadata=payload.metadata)
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except CollectionServiceError as error:
            raise _error(error) from error

    @router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_collection(collection_id: str, x_user_id: str = Header(default="")):
        try:
            service_factory(_actor(x_user_id)).delete(collection_id)
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except CollectionServiceError as error:
            raise _error(error) from error
        return None

    return router
