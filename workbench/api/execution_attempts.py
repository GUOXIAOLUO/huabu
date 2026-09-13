"""Versioned HTTP API for per-item ExecutionAttempt metadata."""

from datetime import datetime
from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from workbench.application.execution_attempt_service import ExecutionAttemptNotFoundServiceError, ExecutionAttemptService, ExecutionAttemptServiceError
from workbench.application.execution_service import ExecutionService, ExecutionServiceError
from workbench.domain.execution import ExecutionAttempt, ExecutionAttemptStatus


class ExecutionAttemptCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    input_id: str = Field(min_length=1, max_length=255)
    item_index: int = Field(ge=0)
    attempt_number: int = Field(ge=1)
    retry_count: int = Field(default=0, ge=0)
    summary: dict[str, Any] = Field(default_factory=dict)


class ExecutionAttemptStatusPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=1)
    status: ExecutionAttemptStatus
    retry_count: int | None = Field(default=None, ge=0)
    error: str | None = None
    output_refs: tuple[str, ...] | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    summary: dict[str, Any] | None = None


class _ServiceFactory(Protocol):
    def __call__(self, actor_id: str) -> ExecutionAttemptService: ...


class _ExecutionServiceFactory(Protocol):
    def __call__(self, actor_id: str) -> ExecutionService: ...


def _actor(value: str) -> str:
    actor = value.strip()
    if not actor or len(actor) > 255:
        raise HTTPException(status_code=401, detail="X-User-ID is required")
    return actor


def _error(error: ExecutionAttemptServiceError | ExecutionServiceError) -> HTTPException:
    if isinstance(error, ExecutionAttemptNotFoundServiceError): code = 404
    elif error.code in {"stale_revision", "retry_stale", "retry_conflict"}: code = 409
    else: code = 400
    return HTTPException(status_code=code, detail={"code": error.code, "message": str(error)})


def create_execution_attempts_router(*, service_factory: _ServiceFactory, execution_service_factory: _ExecutionServiceFactory | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/v1/execution-runs/{run_id}/attempts", tags=["execution-attempts"])

    @router.post("", response_model=ExecutionAttempt, status_code=status.HTTP_201_CREATED)
    async def create_attempt(run_id: str, payload: ExecutionAttemptCreatePayload, x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).create(run_id=run_id, **payload.model_dump())
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ExecutionAttemptServiceError as error: raise _error(error) from error

    @router.get("", response_model=list[ExecutionAttempt])
    async def list_attempts(run_id: str, x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).list(run_id)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ExecutionAttemptServiceError as error: raise _error(error) from error

    @router.get("/{attempt_id}", response_model=ExecutionAttempt)
    async def get_attempt(run_id: str, attempt_id: str, x_user_id: str = Header(default="")):
        try:
            attempt = service_factory(_actor(x_user_id)).get(attempt_id)
            if attempt.run_id != run_id: raise ExecutionAttemptNotFoundServiceError(attempt_id)
            return attempt
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ExecutionAttemptServiceError as error: raise _error(error) from error

    @router.patch("/{attempt_id}/status", response_model=ExecutionAttempt)
    async def update_attempt_status(run_id: str, attempt_id: str, payload: ExecutionAttemptStatusPayload, x_user_id: str = Header(default="")):
        try:
            service = service_factory(_actor(x_user_id))
            current = service.get(attempt_id)
            if current.run_id != run_id: raise ExecutionAttemptNotFoundServiceError(attempt_id)
            return service.update_status(attempt_id, **payload.model_dump())
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ExecutionAttemptServiceError as error: raise _error(error) from error

    @router.post("/{attempt_id}/cancel", response_model=ExecutionAttempt)
    async def cancel_attempt(run_id: str, attempt_id: str, x_user_id: str = Header(default="")):
        if execution_service_factory is None:
            raise HTTPException(status_code=503, detail="execution controls are not configured")
        try:
            current = service_factory(_actor(x_user_id)).get(attempt_id)
            if current.run_id != run_id: raise ExecutionAttemptNotFoundServiceError(attempt_id)
            return await execution_service_factory(_actor(x_user_id)).cancel_attempt(current)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except (ExecutionAttemptServiceError, ExecutionServiceError) as error: raise _error(error) from error

    @router.post("/{attempt_id}/retry", response_model=ExecutionAttempt, status_code=status.HTTP_201_CREATED)
    async def retry_attempt(run_id: str, attempt_id: str, x_user_id: str = Header(default="")):
        if execution_service_factory is None:
            raise HTTPException(status_code=503, detail="execution controls are not configured")
        try:
            current = service_factory(_actor(x_user_id)).get(attempt_id)
            if current.run_id != run_id: raise ExecutionAttemptNotFoundServiceError(attempt_id)
            return execution_service_factory(_actor(x_user_id)).retry_failed_attempt(attempt_id)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except (ExecutionAttemptServiceError, ExecutionServiceError) as error: raise _error(error) from error

    return router
