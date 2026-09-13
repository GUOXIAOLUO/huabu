"""Versioned HTTP API for durable ExecutionRun metadata."""

from datetime import datetime
from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from workbench.application.execution_run_service import ExecutionRunNotFoundServiceError, ExecutionRunService, ExecutionRunServiceError
from workbench.application.execution_service import ExecutionService, ExecutionServiceError, ExecutionServiceNotFoundError
from workbench.application.execution_input_projection import ExecutionInputProjection
from workbench.domain.execution import ExecutionPolicy, ExecutionRun, ExecutionRunStatus


class ExecutionRunCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: str = Field(min_length=1, max_length=255)
    task_id: str = Field(min_length=1, max_length=255)
    execution_profile_ref: str = Field(min_length=1, max_length=255)
    policy: ExecutionPolicy
    input_projection: ExecutionInputProjection
    summary: dict[str, Any] = Field(default_factory=dict)


class ExecutionRunStatusPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=1)
    status: ExecutionRunStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None
    summary: dict[str, Any] | None = None


class _ServiceFactory(Protocol):
    def __call__(self, actor_id: str) -> ExecutionRunService: ...


class _ExecutionServiceFactory(Protocol):
    def __call__(self, actor_id: str) -> ExecutionService: ...


def _actor(value: str) -> str:
    actor = value.strip()
    if not actor or len(actor) > 255:
        raise HTTPException(status_code=401, detail="X-User-ID is required")
    return actor


def _error(error: ExecutionRunServiceError) -> HTTPException:
    if isinstance(error, ExecutionRunNotFoundServiceError): code = 404
    elif error.code == "stale_revision": code = 409
    else: code = 400
    return HTTPException(status_code=code, detail={"code": error.code, "message": str(error)})


def create_execution_runs_router(*, service_factory: _ServiceFactory, execution_service_factory: _ExecutionServiceFactory | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/v1/execution-runs", tags=["execution-runs"])

    @router.get("", response_model=list[ExecutionRun])
    async def list_runs(project_id: str = Query(min_length=1, max_length=255), x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).list(project_id)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error

    @router.get("/{run_id}", response_model=ExecutionRun)
    async def get_run(run_id: str, x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).get(run_id)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ExecutionRunServiceError as error: raise _error(error) from error

    @router.post("", response_model=ExecutionRun, status_code=status.HTTP_201_CREATED)
    async def create_run(payload: ExecutionRunCreatePayload, x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).create(**payload.model_dump())
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ExecutionRunServiceError as error: raise _error(error) from error

    @router.patch("/{run_id}/status", response_model=ExecutionRun)
    async def update_run_status(run_id: str, payload: ExecutionRunStatusPayload, x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).update_status(run_id, **payload.model_dump())
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ExecutionRunServiceError as error: raise _error(error) from error

    @router.post("/{run_id}/cancel", response_model=ExecutionRun)
    async def cancel_run(run_id: str, x_user_id: str = Header(default="")):
        if execution_service_factory is None:
            raise HTTPException(status_code=503, detail="execution controls are not configured")
        try:
            return await execution_service_factory(_actor(x_user_id)).cancel_run(run_id)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ExecutionServiceNotFoundError as error: raise HTTPException(status_code=404, detail={"code": error.code, "message": str(error)}) from error
        except ExecutionServiceError as error:
            code = 409 if error.code == "stale_revision" else 400
            raise HTTPException(status_code=code, detail={"code": error.code, "message": str(error)}) from error

    return router
