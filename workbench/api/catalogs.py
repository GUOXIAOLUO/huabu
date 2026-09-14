"""Versioned generic Catalog API."""

from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from workbench.application.catalog_service import CatalogService, CatalogServiceError
from workbench.domain.catalog import Catalog, CatalogItemVersion, CatalogMediaRef, CatalogSchema


class CatalogCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_id: str = Field(min_length=1, max_length=255)
    project_id: str | None = Field(default=None, max_length=255)
    scope: str
    name: str = Field(min_length=1, max_length=500)
    catalog_schema: CatalogSchema = Field(alias="schema")
    metadata: dict[str, Any] = Field(default_factory=dict)


class CatalogItemPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=500)
    attributes: dict[str, Any] = Field(default_factory=dict)
    media_refs: tuple[CatalogMediaRef, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)


class CatalogItemVersionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    attributes: dict[str, Any] = Field(default_factory=dict)
    media_refs: tuple[CatalogMediaRef, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)


class _CatalogServiceFactory(Protocol):
    def __call__(self, actor_id: str) -> CatalogService: ...


def _actor(value: str) -> str:
    actor = value.strip()
    if not actor or len(actor) > 255: raise HTTPException(status_code=401, detail="X-User-ID is required")
    return actor


def _error(error: CatalogServiceError) -> HTTPException:
    code = 404 if error.code == "not_found" else 409 if error.code == "conflict" else 400
    return HTTPException(status_code=code, detail={"code": error.code, "message": str(error)})


def create_catalogs_router(*, service_factory: _CatalogServiceFactory) -> APIRouter:
    router = APIRouter(prefix="/api/v1/catalogs", tags=["catalogs"])

    @router.get("", response_model=list[Catalog])
    async def list_catalogs(workspace_id: str = Query(min_length=1, max_length=255), project_id: str | None = Query(default=None, max_length=255), x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).list(workspace_id=workspace_id, project_id=project_id)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error

    @router.get("/{catalog_id}", response_model=Catalog)
    async def get_catalog(catalog_id: str, x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).get(catalog_id)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except CatalogServiceError as error: raise _error(error) from error

    @router.post("", response_model=Catalog, status_code=status.HTTP_201_CREATED)
    async def create_catalog(payload: CatalogCreatePayload, x_user_id: str = Header(default="")):
        try:
            return service_factory(_actor(x_user_id)).create(
                workspace_id=payload.workspace_id, project_id=payload.project_id,
                scope=payload.scope, name=payload.name, schema=payload.catalog_schema,
                metadata=payload.metadata,
            )
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except CatalogServiceError as error: raise _error(error) from error

    @router.post("/{catalog_id}/items", response_model=dict, status_code=status.HTTP_201_CREATED)
    async def create_item(catalog_id: str, payload: CatalogItemPayload, x_user_id: str = Header(default="")):
        try:
            catalog, item, version = service_factory(_actor(x_user_id)).create_item(catalog_id, **payload.model_dump())
            return {"catalog": catalog, "item": item, "version": version}
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except CatalogServiceError as error: raise _error(error) from error

    @router.get("/{catalog_id}/items", response_model=list)
    async def list_items(catalog_id: str, x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).list_items(catalog_id)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except CatalogServiceError as error: raise _error(error) from error

    @router.post("/{catalog_id}/items/{item_id}/versions", response_model=CatalogItemVersion, status_code=status.HTTP_201_CREATED)
    async def append_version(catalog_id: str, item_id: str, payload: CatalogItemVersionPayload, x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).append_version(catalog_id, item_id, **payload.model_dump())
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except CatalogServiceError as error: raise _error(error) from error

    @router.get("/items/{item_id}/versions", response_model=list[CatalogItemVersion])
    async def list_versions(item_id: str, x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).list_versions(item_id)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except CatalogServiceError as error: raise _error(error) from error

    return router
