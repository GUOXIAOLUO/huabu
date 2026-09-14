"""Canonical Entity and EntityVersion API."""

from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from workbench.domain.entity import EntityRecord, EntityState, EntityVersion, EntityVersionLineage, EntityVersionPayload
from workbench.application.entity_service import EntityService
from workbench.repositories.entity_repository import EntityNotFoundError, EntityRepositoryError


class EntityCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1, max_length=255)
    entity_type: str = Field(min_length=1, max_length=255)
    definition_id: str = Field(min_length=1, max_length=255)
    properties: dict[str, Any] = Field(default_factory=dict)
    state: EntityState = "draft"
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntityVersionCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payload: EntityVersionPayload
    lineage: EntityVersionLineage | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class _EntityServiceFactory(Protocol):
    def __call__(self, actor_id: str) -> EntityService: ...


def _actor(x_user_id: str) -> str:
    actor_id = x_user_id.strip()
    if not actor_id or len(actor_id) > 255:
        raise HTTPException(status_code=401, detail="X-User-ID is required")
    return actor_id


def _error(error: EntityRepositoryError) -> HTTPException:
    if isinstance(error, EntityNotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    return HTTPException(status_code=409, detail=str(error))


def create_entities_router(*, service_factory: _EntityServiceFactory) -> APIRouter:
    router = APIRouter(prefix="/api/v1/entities", tags=["entities"])

    @router.get("", response_model=list[EntityRecord])
    async def list_entities(project_id: str = Query(min_length=1, max_length=255), x_user_id: str = Header(default="")):
        try:
            return service_factory(_actor(x_user_id)).list(project_id)
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error

    @router.get("/{entity_id}", response_model=EntityRecord)
    async def get_entity(entity_id: str, x_user_id: str = Header(default="")):
        try:
            return service_factory(_actor(x_user_id)).get(entity_id)
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except EntityRepositoryError as error:
            raise _error(error) from error

    @router.post("", response_model=EntityRecord, status_code=status.HTTP_201_CREATED)
    async def create_entity(payload: EntityCreatePayload, x_user_id: str = Header(default="")):
        try:
            return service_factory(_actor(x_user_id)).create(**payload.model_dump())
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except EntityRepositoryError as error:
            raise _error(error) from error

    @router.post("/{entity_id}/versions", response_model=EntityVersion, status_code=status.HTTP_201_CREATED)
    async def append_version(entity_id: str, payload: EntityVersionCreatePayload, x_user_id: str = Header(default="")):
        try:
            return service_factory(_actor(x_user_id)).append_version(entity_id=entity_id, **payload.model_dump())
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except EntityRepositoryError as error:
            raise _error(error) from error

    @router.get("/{entity_id}/versions", response_model=list[EntityVersion])
    async def list_versions(entity_id: str, x_user_id: str = Header(default="")):
        try:
            return service_factory(_actor(x_user_id)).list_versions(entity_id)
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except EntityRepositoryError as error:
            raise _error(error) from error

    @router.get("/{entity_id}/versions/{version_id}", response_model=EntityVersion)
    async def get_version(entity_id: str, version_id: str, x_user_id: str = Header(default="")):
        try:
            return service_factory(_actor(x_user_id)).get_version(entity_id, version_id)
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except EntityRepositoryError as error:
            raise _error(error) from error

    return router
