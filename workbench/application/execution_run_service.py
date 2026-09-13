"""Application boundary for durable execution run lifecycle metadata."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Callable

from workbench.application.execution_input_projection import ExecutionInputProjection
from workbench.domain.execution import ExecutionPolicy, ExecutionRun, ExecutionRunStatus
from workbench.repositories.execution_run_repository import ExecutionRunInvalidTransitionError, ExecutionRunNotFoundError, ExecutionRunRepository, ExecutionRunStaleRevisionError


class ExecutionRunServiceError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class ExecutionRunNotFoundServiceError(ExecutionRunServiceError):
    def __init__(self, run_id: str):
        super().__init__("not_found", f"execution run not found: {run_id}")


class ExecutionRunService:
    def __init__(self, repository: ExecutionRunRepository, *, actor_id: str, id_factory: Callable[[], str] | None = None, clock: Callable[[], datetime] | None = None):
        self._repository = repository
        self._actor_id = actor_id
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._clock = clock or (lambda: datetime.now(UTC))

    def create(self, *, project_id: str, task_id: str, execution_profile_ref: str, policy: ExecutionPolicy, input_projection: ExecutionInputProjection, summary: dict[str, object] | None = None) -> ExecutionRun:
        run = ExecutionRun(id=self._id_factory(), project_id=project_id, task_id=task_id, execution_profile_ref=execution_profile_ref, policy=policy, input_projection=input_projection, created_at=self._clock(), summary=summary or {})
        return self._repository.create(run, actor_id=self._actor_id)

    def get(self, run_id: str) -> ExecutionRun:
        try:
            return self._repository.get(run_id, actor_id=self._actor_id)
        except ExecutionRunNotFoundError as error:
            raise ExecutionRunNotFoundServiceError(run_id) from error

    def list(self, project_id: str) -> list[ExecutionRun]:
        return self._repository.list(project_id, actor_id=self._actor_id)

    def update_status(self, run_id: str, *, status: ExecutionRunStatus, expected_revision: int, started_at: datetime | None = None, finished_at: datetime | None = None, summary: dict[str, object] | None = None) -> ExecutionRun:
        try:
            return self._repository.update_status(run_id, status=status, expected_revision=expected_revision, actor_id=self._actor_id, started_at=started_at, finished_at=finished_at, summary=summary)
        except ExecutionRunNotFoundError as error:
            raise ExecutionRunNotFoundServiceError(run_id) from error
        except ExecutionRunStaleRevisionError as error:
            raise ExecutionRunServiceError("stale_revision", str(error)) from error
        except ExecutionRunInvalidTransitionError as error:
            raise ExecutionRunServiceError("invalid_transition", str(error)) from error
