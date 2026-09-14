"""API for explicitly saving one selected execution result as an Asset."""

from typing import Any, Protocol
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from workbench.domain.asset import Asset, AssetType, AssetVersionContent
from workbench.application.result_asset_materialization import ResultAssetMaterializationError


class ResultAssetMaterializationPayload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    project_id: str = Field(min_length=1, max_length=255)
    attempt_id: str = Field(min_length=1, max_length=255)
    output_name: str = Field(min_length=1, max_length=255)
    ordinal: int = Field(ge=0)
    title: str = Field(min_length=1, max_length=500)
    type: AssetType
    content: AssetVersionContent
    metadata: dict[str, Any] = Field(default_factory=dict)


class _ServiceFactory(Protocol):
    def __call__(self, actor_id: str): ...


def create_result_asset_materializations_router(*, service_factory: _ServiceFactory) -> APIRouter:
    router = APIRouter(prefix='/api/v1/execution-runs/{run_id}', tags=['result-asset-materializations'])

    @router.post('/assets', response_model=dict, status_code=status.HTTP_201_CREATED)
    async def materialize(run_id: str, payload: ResultAssetMaterializationPayload, x_user_id: str = Header(default='')):
        actor = x_user_id.strip()
        if not actor: raise HTTPException(status_code=401, detail='X-User-ID is required')
        try:
            asset, version = service_factory(actor).materialize(run_id=run_id, **payload.model_dump())
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ResultAssetMaterializationError as error:
            code = 403 if error.code == 'cross_project' else 404 if error.code == 'not_found' else 409 if error.code == 'result_not_selected' else 422
            raise HTTPException(status_code=code, detail={'code': error.code, 'message': str(error)}) from error
        return {'asset': asset, 'version': version, 'ref': version.ref()}

    return router
