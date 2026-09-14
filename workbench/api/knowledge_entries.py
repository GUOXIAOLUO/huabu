"""Canonical KnowledgeEntry persistence/query API."""

from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from workbench.application.knowledge_entry_service import KnowledgeEntryService, KnowledgeEntryServiceError
from workbench.domain.knowledge import KnowledgeEntry, KnowledgeSourceScope


class KnowledgeEntryCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1, max_length=255)
    content: str | None = Field(default=None, max_length=100_000)
    structured_payload: dict[str, Any] | None = None
    source_refs: tuple[str, ...] = Field(min_length=1)
    tags: tuple[str, ...] = ()
    scope: KnowledgeSourceScope = "project"
    metadata: dict[str, Any] = Field(default_factory=dict)


class _KnowledgeEntryServiceFactory(Protocol):
    def __call__(self, actor_id: str) -> KnowledgeEntryService: ...


def _actor(value: str) -> str:
    actor = value.strip()
    if not actor or len(actor) > 255:
        raise HTTPException(status_code=401, detail="X-User-ID is required")
    return actor


def _error(error: KnowledgeEntryServiceError) -> HTTPException:
    code = 404 if error.code == "not_found" else 409 if error.code == "conflict" else 400
    return HTTPException(status_code=code, detail={"code": error.code, "message": str(error)})


def create_knowledge_entries_router(*, service_factory: _KnowledgeEntryServiceFactory) -> APIRouter:
    router = APIRouter(prefix="/api/v1/knowledge-entries", tags=["knowledge"])

    @router.get("", response_model=list[KnowledgeEntry])
    async def list_entries(
        project_id: str = Query(min_length=1, max_length=255), query: str | None = Query(default=None, max_length=500),
        tag: str | None = Query(default=None, max_length=255), scope: KnowledgeSourceScope | None = None,
        x_user_id: str = Header(default=""),
    ):
        try:
            return service_factory(_actor(x_user_id)).list(project_id=project_id, query=query, tag=tag, scope=scope)
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error

    @router.get("/search", response_model=list[KnowledgeEntry])
    async def search_entries(
        project_id: str = Query(min_length=1, max_length=255), query: str | None = Query(default=None, max_length=500),
        tag: str | None = Query(default=None, max_length=255), source_ref: str | None = Query(default=None, max_length=255),
        scope: KnowledgeSourceScope | None = None, x_user_id: str = Header(default=""),
    ):
        try:
            return service_factory(_actor(x_user_id)).search(
                project_id=project_id, query=query, tag=tag, scope=scope, source_ref=source_ref,
            )
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error

    @router.get("/{entry_id}", response_model=KnowledgeEntry)
    async def get_entry(entry_id: str, x_user_id: str = Header(default="")):
        try:
            return service_factory(_actor(x_user_id)).get(entry_id)
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except KnowledgeEntryServiceError as error:
            raise _error(error) from error

    @router.post("", response_model=KnowledgeEntry, status_code=status.HTTP_201_CREATED)
    async def create_entry(payload: KnowledgeEntryCreatePayload, x_user_id: str = Header(default="")):
        try:
            return service_factory(_actor(x_user_id)).create(**payload.model_dump())
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except KnowledgeEntryServiceError as error:
            raise _error(error) from error

    return router
