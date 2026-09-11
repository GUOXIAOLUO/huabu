"""Canonical Project transport API backed by ProjectService."""

from datetime import datetime
from typing import Any, Protocol

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from workbench.application.project_service import ProjectArchiveResult, ProjectNotFoundError, ProjectService, ProjectServiceError


class CanonicalProjectCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="新项目", max_length=60)


class CanonicalProjectUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=60)
    order: int | None = None


class CanonicalProjectResponse(BaseModel):
    id: str
    name: str
    workspace_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    revision: int = Field(ge=1)
    metadata: dict[str, Any]


class _ProjectServiceFactory(Protocol):
    def __call__(self, *, with_canvas_reassigner: bool = False) -> ProjectService: ...


def _response(project) -> CanonicalProjectResponse:
    return CanonicalProjectResponse(
        id=project.id,
        name=project.name,
        workspace_id=project.workspace_id,
        created_by=project.created_by,
        created_at=project.created_at,
        updated_at=project.updated_at,
        revision=project.revision,
        metadata=project.metadata,
    )


def _service_error(error: ProjectServiceError) -> HTTPException:
    status_code = 404 if isinstance(error, ProjectNotFoundError) else 400
    return HTTPException(status_code=status_code, detail={"code": error.code, "message": str(error)})


def create_canonical_projects_router(*, project_service_factory: _ProjectServiceFactory) -> APIRouter:
    """Build the versioned Project transport around the application service."""
    router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

    @router.get("", response_model=list[CanonicalProjectResponse])
    async def list_canonical_projects():
        return [_response(project) for project in project_service_factory().list_after_ensuring_default()]

    @router.get("/{project_id}", response_model=CanonicalProjectResponse)
    async def get_canonical_project(project_id: str):
        try:
            return _response(project_service_factory().get(project_id))
        except ProjectServiceError as error:
            raise _service_error(error) from error

    @router.post("", response_model=CanonicalProjectResponse, status_code=201)
    async def create_canonical_project(payload: CanonicalProjectCreatePayload):
        try:
            return _response(project_service_factory().create(payload.name))
        except ProjectServiceError as error:
            raise _service_error(error) from error

    @router.put("/{project_id}", response_model=CanonicalProjectResponse)
    async def update_canonical_project(project_id: str, payload: CanonicalProjectUpdatePayload):
        try:
            return _response(project_service_factory().update(project_id, name=payload.name, order=payload.order))
        except ProjectServiceError as error:
            raise _service_error(error) from error

    @router.delete("/{project_id}")
    async def archive_canonical_project(project_id: str):
        try:
            result: ProjectArchiveResult = project_service_factory(with_canvas_reassigner=True).archive(project_id)
        except ProjectServiceError as error:
            raise _service_error(error) from error
        return {"ok": True, "project_id": result.project_id, "moved_canvas_count": result.moved_canvas_count}

    return router
