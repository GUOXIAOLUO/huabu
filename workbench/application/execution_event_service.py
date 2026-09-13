"""Application boundary for normalized durable execution events."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Callable

from workbench.domain.execution import ExecutionEventRecord, ExecutionEventType
from workbench.repositories.execution_event_repository import ExecutionEventNotFoundError, ExecutionEventRepository, ExecutionEventSequenceConflictError


class ExecutionEventServiceError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class ExecutionEventNotFoundServiceError(ExecutionEventServiceError):
    def __init__(self, reference: str):
        super().__init__("not_found", f"execution event resource not found: {reference}")


class ExecutionEventService:
    def __init__(self, repository: ExecutionEventRepository, *, actor_id: str, id_factory: Callable[[], str] | None = None, clock: Callable[[], datetime] | None = None):
        self._repository = repository
        self._actor_id = actor_id
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._clock = clock or (lambda: datetime.now(UTC))

    def append(self, *, run_id: str, sequence: int, event_type: ExecutionEventType, payload: dict[str, object] | None = None, attempt_id: str | None = None, occurred_at: datetime | None = None) -> ExecutionEventRecord:
        event = ExecutionEventRecord(id=self._id_factory(), run_id=run_id, attempt_id=attempt_id, sequence=sequence, event_type=event_type, payload=payload or {}, occurred_at=occurred_at or self._clock())
        try:
            return self._repository.append(event, actor_id=self._actor_id)
        except ExecutionEventNotFoundError as error:
            raise ExecutionEventNotFoundServiceError(str(error)) from error
        except ExecutionEventSequenceConflictError as error:
            raise ExecutionEventServiceError("sequence_conflict", str(error)) from error

    def stream(self, run_id: str, *, after_sequence: int = 0, limit: int = 200) -> list[ExecutionEventRecord]:
        try:
            return self._repository.list(run_id, actor_id=self._actor_id, after_sequence=after_sequence, limit=limit)
        except ExecutionEventNotFoundError as error:
            raise ExecutionEventNotFoundServiceError(str(error)) from error
