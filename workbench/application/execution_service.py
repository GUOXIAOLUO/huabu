"""Application-level cancellation and bounded retry orchestration."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Callable

from workbench.application.execution_event_service import ExecutionEventService
from workbench.domain.execution import ExecutionAttempt, ExecutionEvent, ExecutionHandle, ExecutionInput, ExecutionRequest, ExecutionResult, ExecutionRun, Executor
from workbench.repositories.execution_attempt_repository import ExecutionAttemptInvalidTransitionError, ExecutionAttemptRepository, ExecutionAttemptRetryConflictError, ExecutionAttemptStaleRevisionError
from workbench.repositories.execution_run_repository import ExecutionRunInvalidTransitionError, ExecutionRunNotFoundError, ExecutionRunRepository, ExecutionRunStaleRevisionError


class ExecutionServiceError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class ExecutionServiceNotFoundError(ExecutionServiceError):
    def __init__(self, run_id: str):
        super().__init__("not_found", f"execution run not found: {run_id}")


class ExecutionControlRegistry(dict[str, tuple[Executor, ExecutionHandle]]):
    """Process-local active controls shared by request-scoped services."""


class ExecutionService:
    """Coordinate cancellation/retry without selecting or replacing executors."""

    def __init__(self, run_repository: ExecutionRunRepository, attempt_repository: ExecutionAttemptRepository, *, actor_id: str, event_service: ExecutionEventService | None = None, control_registry: ExecutionControlRegistry | None = None, id_factory: Callable[[], str] | None = None, clock: Callable[[], datetime] | None = None):
        self._runs = run_repository
        self._attempts = attempt_repository
        self._actor_id = actor_id
        self._events = event_service
        self._active_controls = control_registry if control_registry is not None else ExecutionControlRegistry()
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._clock = clock or (lambda: datetime.now(UTC))

    async def execute(self, run_id: str, *, executor: Executor) -> ExecutionResult:
        """Run one generic Task through a resolved Executor and persist its lifecycle."""
        try:
            run = self._runs.get(run_id, actor_id=self._actor_id)
        except ExecutionRunNotFoundError as error:
            raise ExecutionServiceNotFoundError(run_id) from error
        if not run.input_projection.valid:
            raise ExecutionServiceError("invalid_input_projection", "execution input projection is not executable")
        if run.status not in {"prepared", "queued"}:
            raise ExecutionServiceError("execution_not_startable", f"execution run is {run.status}")
        if self._attempts.list(run_id, actor_id=self._actor_id):
            raise ExecutionServiceError("execution_already_started", "execution run already has attempts")
        inputs = tuple(
            ExecutionInput(name=item.input_id, value=item.value)
            for item in run.input_projection.inputs
        )
        config = {
            "task_id": run.task_id,
            "parameters": dict(run.input_projection.parameters),
        }
        request = ExecutionRequest(
            execution_id=self._id_factory(),
            idempotency_key=self._id_factory(),
            inputs=inputs,
            config=config,
            model_availability_ref=run.input_projection.model_availability_ref,
            execution_profile_ref=run.execution_profile_ref,
        )
        attempt = ExecutionAttempt(
            id=request.execution_id,
            run_id=run.id,
            input_id=inputs[0].name if inputs else run.task_id,
            item_index=0,
            attempt_number=1,
            created_at=self._clock(),
        )
        self._attempts.create(attempt, actor_id=self._actor_id)
        self._runs.update_status(
            run.id,
            status="running",
            expected_revision=run.revision,
            actor_id=self._actor_id,
            started_at=self._clock(),
        )
        handle: ExecutionHandle | None = None
        try:
            prepared = await executor.prepare(request)
            if prepared.executor_ref != executor.executor_ref or prepared.execution_id != request.execution_id:
                raise ExecutionServiceError("executor_contract_mismatch", "executor returned an invalid preparation")
            handle = await executor.start(prepared)
            if handle.executor_ref != executor.executor_ref or handle.execution_id != request.execution_id:
                raise ExecutionServiceError("executor_contract_mismatch", "executor returned an invalid handle")
            self._active_controls[attempt.id] = (executor, handle)
            current_attempt = self._attempts.get(attempt.id, actor_id=self._actor_id)
            if current_attempt.status == "cancelled":
                await executor.cancel(handle)
                result = await executor.result(handle)
                await self._normalize_run(run.id)
                return result
            self._attempts.update_status(
                attempt.id,
                status="running",
                expected_revision=current_attempt.revision,
                actor_id=self._actor_id,
                started_at=self._clock(),
            )
            async for event in executor.stream(handle):
                if event.execution_id != request.execution_id:
                    raise ExecutionServiceError("executor_contract_mismatch", "executor emitted an event for another execution")
                self._append_event(run.id, attempt.id, event)
            result = await executor.result(handle)
            if result.execution_id != request.execution_id:
                raise ExecutionServiceError("executor_contract_mismatch", "executor returned a result for another execution")
            current_attempt = self._attempts.get(attempt.id, actor_id=self._actor_id)
            if current_attempt.status not in {"succeeded", "failed", "cancelled"}:
                self._attempts.update_status(
                    attempt.id,
                    status=result.status,
                    expected_revision=current_attempt.revision,
                    actor_id=self._actor_id,
                    error=result.error,
                    finished_at=self._clock(),
                    summary={"output_count": len(result.outputs), "executor_ref": executor.executor_ref},
                )
            await self._normalize_run(run.id)
            return result
        except Exception as error:
            current_attempt = self._attempts.get(attempt.id, actor_id=self._actor_id)
            if current_attempt.status == "prepared":
                current_attempt = self._attempts.update_status(
                    attempt.id,
                    status="running",
                    expected_revision=current_attempt.revision,
                    actor_id=self._actor_id,
                    started_at=self._clock(),
                )
            if current_attempt.status == "running":
                self._attempts.update_status(
                    attempt.id,
                    status="failed",
                    expected_revision=current_attempt.revision,
                    actor_id=self._actor_id,
                    error=str(error),
                    finished_at=self._clock(),
                    summary={"executor_ref": executor.executor_ref},
                )
            await self._normalize_run(run.id)
            if isinstance(error, ExecutionServiceError):
                raise
            raise ExecutionServiceError("execution_failed", str(error)) from error
        finally:
            self._active_controls.pop(attempt.id, None)
            if handle is not None:
                await executor.cleanup(handle)

    async def execute_run(self, run_id: str, *, executor: Executor) -> ExecutionResult:
        """Named alias for callers that distinguish a run from a Task definition."""
        return await self.execute(run_id, executor=executor)

    def _append_event(self, run_id: str, attempt_id: str, event: ExecutionEvent) -> None:
        if self._events is None:
            return
        payload: dict[str, object] = {"executor_sequence": event.sequence}
        if event.message is not None:
            payload["message"] = event.message
        if event.outputs:
            payload["output_names"] = [output.name for output in event.outputs]
        self._events.append(
            run_id=run_id,
            attempt_id=attempt_id,
            sequence=event.sequence + 1,
            event_type=event.kind,
            payload=payload,
        )

    async def _normalize_run(self, run_id: str, *, empty_status: str | None = None) -> ExecutionRun:
        run = self._runs.get(run_id, actor_id=self._actor_id)
        if run.status not in {"prepared", "queued", "running"}:
            return run
        attempts = self._attempts.list(run_id, actor_id=self._actor_id)
        if not attempts:
            if empty_status is None:
                return run
            return self._runs.update_status(run_id, status=empty_status, expected_revision=run.revision, actor_id=self._actor_id, finished_at=self._clock())
        if not all(item.status in {"succeeded", "failed", "cancelled"} for item in attempts):
            return run
        latest_by_item: dict[int, ExecutionAttempt] = {}
        for item in attempts:
            latest = latest_by_item.get(item.item_index)
            if latest is None or (item.attempt_number, item.id) > (latest.attempt_number, latest.id):
                latest_by_item[item.item_index] = item
        latest_attempts = list(latest_by_item.values())
        if any(item.status == "cancelled" for item in latest_attempts):
            terminal_status = "cancelled"
        elif any(item.status == "failed" for item in latest_attempts):
            terminal_status = "failed"
        else:
            terminal_status = "succeeded"
        try:
            return self._runs.update_status(run_id, status=terminal_status, expected_revision=run.revision, actor_id=self._actor_id, finished_at=self._clock())
        except ExecutionRunStaleRevisionError as error:
            raise ExecutionServiceError("stale_revision", str(error)) from error
        except ExecutionRunInvalidTransitionError as error:
            raise ExecutionServiceError("invalid_transition", str(error)) from error

    async def normalize_run(self, run_id: str) -> ExecutionRun:
        """Expose terminal normalization to application adapters that own status writes."""
        return await self._normalize_run(run_id)

    def _mark_cancelled(self, attempt: ExecutionAttempt, *, status: str) -> ExecutionAttempt:
        try:
            return self._attempts.update_status(attempt.id, status=status, expected_revision=attempt.revision, actor_id=self._actor_id, finished_at=self._clock())
        except ExecutionAttemptStaleRevisionError as error:
            raise ExecutionServiceError("stale_revision", str(error)) from error
        except ExecutionAttemptInvalidTransitionError as error:
            raise ExecutionServiceError("invalid_transition", str(error)) from error

    async def cancel_attempt(self, attempt: ExecutionAttempt, *, executor: Executor | None = None, handle: ExecutionHandle | None = None) -> ExecutionAttempt:
        """Cancel one attempt, preserving an explicit unsupported result."""
        current = self._attempts.get(attempt.id, actor_id=self._actor_id)
        if current.status in {"succeeded", "failed", "cancelled"}:
            await self._normalize_run(current.run_id)
            return current
        if current.status == "prepared":
            updated = self._mark_cancelled(current, status="cancelled")
            await self._normalize_run(current.run_id)
            return updated
        if executor is None or handle is None:
            active_control = self._active_controls.get(attempt.id)
            if active_control is not None:
                executor, handle = active_control
        if executor is None or handle is None:
            raise ExecutionServiceError("executor_handle_required", "running attempt cancellation requires its executor and handle")
        if str(executor.executor_ref) != str(handle.executor_ref):
            raise ExecutionServiceError("executor_mismatch", "executor does not own the supplied execution handle")
        if str(handle.execution_id) != str(current.id):
            raise ExecutionServiceError("cancel_mismatch", "executor cancellation handle targets another execution")
        result = await executor.cancel(handle)
        if not result.accepted and result.status == "unknown":
            raise ExecutionServiceError("cancel_unsupported", "executor did not accept cancellation")
        if result.execution_id != handle.execution_id:
            raise ExecutionServiceError("cancel_mismatch", "executor cancellation result has a different execution id")
        terminal_status = result.status if result.status in {"cancelled", "succeeded", "failed"} else None
        if terminal_status is None:
            raise ExecutionServiceError("cancel_unknown", "executor returned no terminal cancellation status")
        updated = self._mark_cancelled(current, status=terminal_status)
        await self._normalize_run(current.run_id)
        return updated

    async def cancel_run(self, run_id: str, *, controls: Mapping[str, tuple[Executor, ExecutionHandle]] | None = None) -> ExecutionRun:
        """Cancel all active attempts and normalize the run when cancellation completes."""
        controls = {**self._active_controls, **(controls or {})}
        try:
            self._runs.get(run_id, actor_id=self._actor_id)
        except ExecutionRunNotFoundError as error:
            raise ExecutionServiceNotFoundError(run_id) from error
        attempts = self._attempts.list(run_id, actor_id=self._actor_id)
        for attempt in attempts:
            if attempt.status in {"prepared", "running"}:
                executor_handle = controls.get(attempt.id)
                executor = executor_handle[0] if executor_handle else None
                handle = executor_handle[1] if executor_handle else None
                await self.cancel_attempt(attempt, executor=executor, handle=handle)
        return await self._normalize_run(run_id, empty_status="cancelled")

    def retry_failed_attempt(self, attempt_id: str) -> ExecutionAttempt:
        """Create exactly one next attempt when policy permits a failed attempt.

        The retry limit is an item-level budget, so the bound is evaluated
        against the item's recorded attempt history rather than the retried
        record alone; retrying the same older failed attempt again cannot create
        an unbounded number of new attempts.
        """
        current = self._attempts.get(attempt_id, actor_id=self._actor_id)
        run = self._runs.get(current.run_id, actor_id=self._actor_id)
        if current.status != "failed":
            raise ExecutionServiceError("retry_requires_failed", "only failed attempts can be retried")
        if run.status in {"succeeded", "cancelled"}:
            raise ExecutionServiceError("retry_run_terminal", "terminal execution runs cannot create retry attempts")
        history = self._attempts.list(current.run_id, actor_id=self._actor_id)
        item_history = [item for item in history if item.item_index == current.item_index]
        latest = max(item_history, key=lambda item: (item.attempt_number, item.id), default=current)
        if latest.id != current.id:
            raise ExecutionServiceError("retry_requires_latest", "only the latest failed attempt can be retried")
        retries_performed = max(
            max((item.attempt_number for item in item_history), default=current.attempt_number) - 1,
            max((item.retry_count for item in item_history), default=current.retry_count),
        )
        if retries_performed >= run.policy.retry:
            raise ExecutionServiceError("retry_limit_reached", f"retry limit reached for item {current.item_index}")
        next_number = max((item.attempt_number for item in item_history), default=current.attempt_number) + 1
        retry = ExecutionAttempt(id=self._id_factory(), run_id=current.run_id, input_id=current.input_id, item_index=current.item_index, attempt_number=next_number, created_at=self._clock(), retry_count=retries_performed + 1)
        try:
            return self._attempts.create_retry(retry, source_attempt_id=current.id, expected_source_revision=current.revision, expected_run_revision=run.revision, actor_id=self._actor_id)
        except ExecutionAttemptStaleRevisionError as error:
            raise ExecutionServiceError("retry_stale", str(error)) from error
        except ExecutionAttemptRetryConflictError as error:
            raise ExecutionServiceError("retry_conflict", str(error)) from error
