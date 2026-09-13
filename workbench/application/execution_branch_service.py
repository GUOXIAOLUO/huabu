"""Application boundary for regenerating a run with lineage.

A regeneration is one operation that creates two things together: the new run
and the record of where it came from. They are created together because the
card's guarantee is that every regeneration has lineage — a new run without a
branch record would be an unattributable run.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Callable

from workbench.application.execution_run_service import ExecutionRunService, ExecutionRunServiceError
from workbench.domain.execution import ExecutionBranch, ExecutionPolicy
from workbench.repositories.execution_branch_repository import (
    ExecutionBranchConflictError,
    ExecutionBranchNotFoundError,
    ExecutionBranchRepository,
)


class ExecutionBranchServiceError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class ExecutionBranchNotFoundServiceError(ExecutionBranchServiceError):
    def __init__(self, target: str):
        super().__init__("not_found", f"execution branch not found: {target}")


class ExecutionBranchService:
    def __init__(self, repository: ExecutionBranchRepository, run_service: ExecutionRunService, *, actor_id: str, id_factory: Callable[[], str] | None = None, clock: Callable[[], datetime] | None = None):
        self._repository = repository
        self._run_service = run_service
        self._actor_id = actor_id
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._clock = clock or (lambda: datetime.now(UTC))

    def regenerate(self, *, source_run_id: str, policy_override: ExecutionPolicy | None = None, source_attempt_id: str | None = None, source_output_name: str | None = None, source_ordinal: int | None = None, metadata: dict[str, object] | None = None) -> ExecutionBranch:
        try:
            source = self._run_service.get(source_run_id)
        except ExecutionRunServiceError as error:
            raise self._translate(error, source_run_id) from error

        # The new run reuses the source's frozen input snapshot; only the policy
        # may be overridden. Nothing about the source run is modified.
        try:
            branch_run = self._run_service.create(
                project_id=source.project_id, task_id=source.task_id,
                execution_profile_ref=source.execution_profile_ref,
                policy=policy_override or source.policy,
                input_projection=source.input_projection,
                summary={"regenerated_from": source_run_id},
            )
        except ExecutionRunServiceError as error:
            raise ExecutionBranchServiceError(error.code, str(error)) from error

        try:
            return self._repository.create(ExecutionBranch(
                id=self._id_factory(), project_id=source.project_id, run_id=branch_run.id,
                source_run_id=source_run_id, source_attempt_id=source_attempt_id,
                source_output_name=source_output_name, source_ordinal=source_ordinal,
                policy_override=policy_override, created_at=self._clock(), metadata=metadata or {},
            ), actor_id=self._actor_id)
        except ExecutionBranchConflictError as error:
            raise ExecutionBranchServiceError("conflict", str(error)) from error

    def get(self, branch_id: str) -> ExecutionBranch:
        return self._guarded(lambda: self._repository.get(branch_id, actor_id=self._actor_id), branch_id)

    def get_for_run(self, run_id: str) -> ExecutionBranch:
        return self._guarded(lambda: self._repository.get_for_run(run_id, actor_id=self._actor_id), run_id)

    def list_children(self, source_run_id: str) -> list[ExecutionBranch]:
        try:
            return self._repository.list_children(source_run_id, actor_id=self._actor_id)
        except ExecutionBranchNotFoundError as error:
            raise ExecutionBranchNotFoundServiceError(source_run_id) from error

    def list_lineage(self, run_id: str) -> list[ExecutionBranch]:
        try:
            return self._repository.list_lineage(run_id, actor_id=self._actor_id)
        except ExecutionBranchNotFoundError as error:
            raise ExecutionBranchNotFoundServiceError(run_id) from error

    def _guarded(self, call, target: str) -> ExecutionBranch:
        try:
            return call()
        except ExecutionBranchNotFoundError as error:
            raise ExecutionBranchNotFoundServiceError(target) from error

    @staticmethod
    def _translate(error: ExecutionRunServiceError, target: str) -> ExecutionBranchServiceError:
        """Keep an unknown source run a 404 rather than collapsing it into a 400."""
        if error.code == "not_found":
            return ExecutionBranchNotFoundServiceError(target)
        return ExecutionBranchServiceError(error.code, str(error))
