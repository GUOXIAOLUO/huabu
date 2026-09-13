"""Versioned polling API for normalized durable execution events."""

from datetime import datetime
from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from workbench.application.execution_event_service import ExecutionEventNotFoundServiceError, ExecutionEventService, ExecutionEventServiceError
from workbench.domain.execution import ExecutionEventRecord, ExecutionEventType


class ExecutionEventAppendPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sequence: int = Field(ge=1)
    event_type: ExecutionEventType
    payload: dict[str, Any] = Field(default_factory=dict)
    attempt_id: str | None = None
    occurred_at: datetime | None = None


class _ServiceFactory(Protocol):
    def __call__(self, actor_id: str) -> ExecutionEventService: ...


def _actor(value: str) -> str:
    actor = value.strip()
    if not actor or len(actor) > 255:
        raise HTTPException(status_code=401, detail="X-User-ID is required")
    return actor


def create_execution_events_router(*, service_factory: _ServiceFactory) -> APIRouter:
    router = APIRouter(prefix="/api/v1/execution-runs/{run_id}/events", tags=["execution-events"])

    def handle(error: ExecutionEventServiceError) -> HTTPException:
        if isinstance(error, ExecutionEventNotFoundServiceError):
            code = 404
        elif error.code == "sequence_conflict":
            code = 409
        else:
            code = 400
        return HTTPException(status_code=code, detail={"code": error.code, "message": str(error)})

    @router.post("", response_model=ExecutionEventRecord, status_code=status.HTTP_201_CREATED)
    async def append_event(run_id: str, payload: ExecutionEventAppendPayload, x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).append(run_id=run_id, **payload.model_dump())
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ExecutionEventServiceError as error: raise handle(error) from error

    @router.get("", response_model=list[ExecutionEventRecord])
    async def stream_events(run_id: str, after_sequence: int = Query(default=0, ge=0), limit: int = Query(default=200, ge=1, le=1000), x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).stream(run_id, after_sequence=after_sequence, limit=limit)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ExecutionEventServiceError as error: raise handle(error) from error

    return router
