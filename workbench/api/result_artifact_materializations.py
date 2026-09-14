"""API for explicitly promoting one selected execution result to an Artifact."""

from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from workbench.application.result_artifact_materialization import ResultArtifactMaterializationError
from workbench.domain.artifact import ArtifactType, ArtifactVersionContentRef


class ResultArtifactMaterializationPayload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    project_id: str = Field(min_length=1, max_length=255)
    attempt_id: str = Field(min_length=1, max_length=255)
    output_name: str = Field(min_length=1, max_length=255)
    ordinal: int = Field(ge=0)
    title: str = Field(min_length=1, max_length=500)
    type: ArtifactType
    content_ref: ArtifactVersionContentRef
    input_refs: tuple[str, ...] = ()
    prompt_version_ref: str | None = None
    model_ref: str | None = None
    skill_version_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class _ServiceFactory(Protocol):
    def __call__(self, actor_id: str): ...


def create_result_artifact_materializations_router(*, service_factory: _ServiceFactory) -> APIRouter:
    router = APIRouter(prefix='/api/v1/execution-runs/{run_id}', tags=['result-artifact-materializations'])

    @router.post('/artifacts', response_model=dict, status_code=status.HTTP_201_CREATED)
    async def materialize(run_id: str, payload: ResultArtifactMaterializationPayload, x_user_id: str = Header(default='')):
        actor = x_user_id.strip()
        if not actor:
            raise HTTPException(status_code=401, detail='X-User-ID is required')
        try:
            artifact, version = service_factory(actor).materialize(run_id=run_id, **payload.model_dump())
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except ResultArtifactMaterializationError as error:
            code = 403 if error.code == 'cross_project' else 404 if error.code == 'not_found' else 409 if error.code == 'result_not_selected' else 422
            raise HTTPException(status_code=code, detail={'code': error.code, 'message': str(error)}) from error
        return {'artifact': artifact, 'version': version}

    return router
