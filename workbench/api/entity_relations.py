"""Canonical API for generic EntityRelations outside the Canvas graph."""

from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from workbench.application.entity_relation_service import EntityRelationService
from workbench.domain.entity import EntityRelation, EntityRelationEndpoint
from workbench.repositories.entity_relation_repository import EntityRelationRepositoryError, EntityRelationNotFoundError


class EntityRelationCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1, max_length=255)
    relation_type: str = Field(min_length=1, max_length=255)
    from_endpoint: EntityRelationEndpoint = Field(alias="from")
    to_endpoint: EntityRelationEndpoint = Field(alias="to")
    revision: int = Field(default=1, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class _EntityRelationServiceFactory(Protocol):
    def __call__(self, actor_id: str) -> EntityRelationService: ...


def _actor(x_user_id: str) -> str:
    actor_id = x_user_id.strip()
    if not actor_id or len(actor_id) > 255:
        raise HTTPException(status_code=401, detail="X-User-ID is required")
    return actor_id


def _error(error: EntityRelationRepositoryError) -> HTTPException:
    code = 404 if isinstance(error, EntityRelationNotFoundError) else 409
    return HTTPException(status_code=code, detail=str(error))


def create_entity_relations_router(*, service_factory: _EntityRelationServiceFactory) -> APIRouter:
    router = APIRouter(prefix="/api/v1/entity-relations", tags=["entity-relations"])

    @router.post("", response_model=EntityRelation, status_code=status.HTTP_201_CREATED)
    async def create_relation(payload: EntityRelationCreatePayload, x_user_id: str = Header(default="")):
        try:
            return service_factory(_actor(x_user_id)).create(**payload.model_dump())
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except EntityRelationRepositoryError as error:
            raise _error(error) from error

    @router.get("", response_model=list[EntityRelation])
    async def query_relations(
        project_id: str = Query(min_length=1, max_length=255),
        relation_type: str | None = Query(default=None, min_length=1, max_length=255),
        resource_type: str | None = Query(default=None, min_length=1, max_length=255),
        resource_id: str | None = Query(default=None, min_length=1, max_length=255),
        x_user_id: str = Header(default=""),
    ):
        try:
            return service_factory(_actor(x_user_id)).query(
                project_id, relation_type=relation_type,
                resource_type=resource_type, resource_id=resource_id,
            )
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error

    @router.get("/{relation_id}", response_model=EntityRelation)
    async def get_relation(relation_id: str, x_user_id: str = Header(default="")):
        try:
            return service_factory(_actor(x_user_id)).get(relation_id)
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except EntityRelationRepositoryError as error:
            raise _error(error) from error

    return router
