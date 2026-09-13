"""Application boundary for per-item execution attempt lifecycle."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Callable

from workbench.domain.execution import ExecutionAttempt, ExecutionAttemptStatus
from workbench.repositories.execution_attempt_repository import (
    ExecutionAttemptInvalidTransitionError,
    ExecutionAttemptNotFoundError,
    ExecutionAttemptRepository,
    ExecutionAttemptStaleRevisionError,
)


class ExecutionAttemptServiceError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class ExecutionAttemptNotFoundServiceError(ExecutionAttemptServiceError):
    def __init__(self, attempt_id: str):
        super().__init__("not_found", f"execution attempt not found: {attempt_id}")


class ExecutionAttemptService:
    def __init__(self, repository: ExecutionAttemptRepository, *, actor_id: str, id_factory: Callable[[], str] | None = None, clock: Callable[[], datetime] | None = None):
        self._repository = repository
        self._actor_id = actor_id
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._clock = clock or (lambda: datetime.now(UTC))

    def create(self, *, run_id: str, input_id: str, item_index: int, attempt_number: int, retry_count: int = 0, summary: dict[str, object] | None = None) -> ExecutionAttempt:
        attempt = ExecutionAttempt(id=self._id_factory(), run_id=run_id, input_id=input_id, item_index=item_index, attempt_number=attempt_number, created_at=self._clock(), retry_count=retry_count, summary=summary or {})
        return self._repository.create(attempt, actor_id=self._actor_id)

    def get(self, attempt_id: str) -> ExecutionAttempt:
        try:
            return self._repository.get(attempt_id, actor_id=self._actor_id)
        except ExecutionAttemptNotFoundError as error:
            raise ExecutionAttemptNotFoundServiceError(attempt_id) from error

    def list(self, run_id: str) -> list[ExecutionAttempt]:
        return self._repository.list(run_id, actor_id=self._actor_id)

    def update_status(self, attempt_id: str, *, status: ExecutionAttemptStatus, expected_revision: int, retry_count: int | None = None, error: str | None = None, output_refs: tuple[str, ...] | None = None, started_at: datetime | None = None, finished_at: datetime | None = None, summary: dict[str, object] | None = None) -> ExecutionAttempt:
        try:
            return self._repository.update_status(attempt_id, status=status, expected_revision=expected_revision, actor_id=self._actor_id, retry_count=retry_count, error=error, output_refs=output_refs, started_at=started_at, finished_at=finished_at, summary=summary)
        except ExecutionAttemptNotFoundError as error:
            raise ExecutionAttemptNotFoundServiceError(attempt_id) from error
        except ExecutionAttemptStaleRevisionError as error:
            raise ExecutionAttemptServiceError("stale_revision", str(error)) from error
        except ExecutionAttemptInvalidTransitionError as error:
            raise ExecutionAttemptServiceError("invalid_transition", str(error)) from error
