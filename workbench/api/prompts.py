"""Versioned canonical Prompt API."""

from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from workbench.application.prompt_service import PromptService, PromptServiceError
from workbench.application.prompt_registry import PromptRegistration, PromptRegistry, PromptSource
from workbench.domain.prompt import PromptDefinition, PromptVersion


class PromptCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1, max_length=100_000)
    description: str = Field(default="", max_length=5_000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PromptVersionCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(min_length=1, max_length=100_000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class _PromptServiceFactory(Protocol):
    def __call__(self, actor_id: str) -> PromptService: ...
        
class _PromptRegistryFactory(Protocol):
    def __call__(self, actor_id: str) -> PromptRegistry: ...

def _actor(value: str) -> str:
    actor = value.strip()
    if not actor or len(actor) > 255: raise HTTPException(status_code=401, detail="X-User-ID is required")
    return actor


def _error(error: PromptServiceError) -> HTTPException:
    return HTTPException(status_code=404 if error.code in {"not_found", "version_not_found"} else 400, detail={"code": error.code, "message": str(error)})


def create_canonical_prompts_router(*, service_factory: _PromptServiceFactory, registry_factory: _PromptRegistryFactory | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/v1/prompts", tags=["prompts"])

    @router.get("", response_model=list[PromptRegistration])
    async def discover_prompts(
        project_id: str = Query(min_length=1, max_length=255),
        q: str = Query(default="", max_length=500),
        source: PromptSource | None = Query(default=None),
        x_user_id: str = Header(default=""),
    ):
        actor_id = _actor(x_user_id)
        service = service_factory(actor_id)
        registry = registry_factory(actor_id) if registry_factory else PromptRegistry(service.repository, actor_id=actor_id)
        try:
            return registry.discover(project_id, query=q, source=source)
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error

    @router.post("", response_model=PromptDefinition, status_code=status.HTTP_201_CREATED)
    async def create_prompt(payload: PromptCreatePayload, x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).create(project_id=payload.project_id, name=payload.name, content=payload.content, description=payload.description, metadata=payload.metadata)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except PromptServiceError as error: raise _error(error) from error

    @router.get("/{prompt_id}", response_model=PromptDefinition)
    async def get_prompt(prompt_id: str, x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).get(prompt_id)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except PromptServiceError as error: raise _error(error) from error

    @router.get("/{prompt_id}/versions/{version}", response_model=PromptVersion)
    async def resolve_prompt(prompt_id: str, version: int, x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).resolve(prompt_id, version)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except PromptServiceError as error: raise _error(error) from error

    @router.post("/{prompt_id}/versions", response_model=PromptVersion, status_code=status.HTTP_201_CREATED)
    async def create_prompt_version(prompt_id: str, payload: PromptVersionCreatePayload, x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).create_version(prompt_id, content=payload.content, metadata=payload.metadata)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except PromptServiceError as error: raise _error(error) from error

    return router
