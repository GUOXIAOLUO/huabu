"""Versioned Artifact and ArtifactVersion API."""

from datetime import datetime
from typing import Any
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from workbench.application.artifact_service import ArtifactService
from workbench.domain.artifact import Artifact, ArtifactVersion, ArtifactVersionContentRef, ArtifactVersionLineage, ArtifactType
from workbench.repositories.artifact_repository import ArtifactRepositoryError, ArtifactNotFoundError

class ArtifactCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: str = Field(min_length=1, max_length=255)
    type: ArtifactType
    title: str = Field(min_length=1, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ArtifactVersionCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content_ref: ArtifactVersionContentRef
    lineage: ArtifactVersionLineage
    metadata: dict[str, Any] = Field(default_factory=dict)

def create_artifacts_router(*, service_factory) -> APIRouter:
    router = APIRouter(prefix="/api/v1/artifacts", tags=["artifacts"])
    def actor(value: str) -> str:
        if not value.strip(): raise HTTPException(status_code=401, detail="X-User-ID is required")
        return value.strip()
    @router.post("", response_model=Artifact, status_code=201)
    async def create_artifact(payload: ArtifactCreatePayload, x_user_id: str = Header(default="")):
        try: return service_factory(actor(x_user_id)).create(**payload.model_dump())
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
    @router.get("", response_model=list[Artifact])
    async def list_artifacts(project_id: str, x_user_id: str = Header(default="")):
        try:
            return service_factory(actor(x_user_id)).list(project_id)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
    @router.get("/{artifact_id}", response_model=Artifact)
    async def get_artifact(artifact_id: str, x_user_id: str = Header(default="")):
        try: return service_factory(actor(x_user_id)).get(artifact_id)
        except ArtifactNotFoundError as error: raise HTTPException(status_code=404, detail=str(error)) from error
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
    @router.post("/{artifact_id}/versions", response_model=ArtifactVersion, status_code=201)
    async def append_version(artifact_id: str, payload: ArtifactVersionCreatePayload, x_user_id: str = Header(default="")):
        try: return service_factory(actor(x_user_id)).append_version(artifact_id=artifact_id, **payload.model_dump())
        except ArtifactNotFoundError as error: raise HTTPException(status_code=404, detail=str(error)) from error
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ArtifactRepositoryError as error: raise HTTPException(status_code=409, detail=str(error)) from error
    @router.get("/{artifact_id}/versions", response_model=list[ArtifactVersion])
    async def list_versions(artifact_id: str, x_user_id: str = Header(default="")):
        try: return service_factory(actor(x_user_id)).list_versions(artifact_id)
        except ArtifactNotFoundError as error: raise HTTPException(status_code=404, detail=str(error)) from error
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
    return router
