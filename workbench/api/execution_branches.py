"""Versioned HTTP API for execution branch lineage."""

from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_core import PydanticCustomError

from workbench.application.execution_branch_service import ExecutionBranchNotFoundServiceError, ExecutionBranchService, ExecutionBranchServiceError
from workbench.domain.execution import ExecutionBranch, ExecutionPolicy


class ExecutionBranchCreatePayload(BaseModel):
    """One regeneration request.

    Only the policy may be overridden; the input snapshot is always the source
    run's, which is what makes this a regeneration rather than a new run.
    """

    model_config = ConfigDict(extra="forbid")
    policy_override: ExecutionPolicy | None = None
    source_attempt_id: str | None = Field(default=None, min_length=1, max_length=255)
    source_output_name: str | None = Field(default=None, min_length=1, max_length=255)
    source_ordinal: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_result_parts(self):
        named = [self.source_attempt_id, self.source_output_name, self.source_ordinal]
        if any(part is not None for part in named) and not all(part is not None for part in named):
            # A custom error rather than a bare ValueError: pydantic keeps a
            # raised exception in the error context, and a live exception object
            # there makes the 422 body impossible to serialize.
            raise PydanticCustomError("partial_result", "a regeneration that names a result must name its attempt, output and ordinal")
        return self


class _ServiceFactory(Protocol):
    def __call__(self, actor_id: str) -> ExecutionBranchService: ...


def _actor(value: str) -> str:
    actor = value.strip()
    if not actor or len(actor) > 255:
        raise HTTPException(status_code=401, detail="X-User-ID is required")
    return actor


def _error(error: ExecutionBranchServiceError) -> HTTPException:
    if isinstance(error, ExecutionBranchNotFoundServiceError): code = 404
    elif error.code in {"stale_revision", "conflict"}: code = 409
    else: code = 400
    return HTTPException(status_code=code, detail={"code": error.code, "message": str(error)})


def create_execution_branches_router(*, service_factory: _ServiceFactory) -> APIRouter:
    router = APIRouter(prefix="/api/v1/execution-runs/{run_id}", tags=["execution-branches"])

    @router.post("/branches", response_model=ExecutionBranch, status_code=status.HTTP_201_CREATED)
    async def create_branch(run_id: str, payload: ExecutionBranchCreatePayload, x_user_id: str = Header(default="")):
        try:
            return service_factory(_actor(x_user_id)).regenerate(
                source_run_id=run_id, policy_override=payload.policy_override,
                source_attempt_id=payload.source_attempt_id, source_output_name=payload.source_output_name,
                source_ordinal=payload.source_ordinal, metadata=payload.metadata,
            )
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ExecutionBranchServiceError as error: raise _error(error) from error

    @router.get("/branches", response_model=list[ExecutionBranch])
    async def list_branches(run_id: str, x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).list_children(run_id)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ExecutionBranchServiceError as error: raise _error(error) from error

    @router.get("/branches/{branch_id}", response_model=ExecutionBranch)
    async def get_branch(run_id: str, branch_id: str, x_user_id: str = Header(default="")):
        try:
            branch = service_factory(_actor(x_user_id)).get(branch_id)
            if branch.source_run_id != run_id: raise ExecutionBranchNotFoundServiceError(branch_id)
            return branch
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ExecutionBranchServiceError as error: raise _error(error) from error

    @router.get("/lineage", response_model=list[ExecutionBranch])
    async def get_lineage(run_id: str, x_user_id: str = Header(default="")):
        try: return service_factory(_actor(x_user_id)).list_lineage(run_id)
        except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from error
        except ExecutionBranchServiceError as error: raise _error(error) from error

    return router
