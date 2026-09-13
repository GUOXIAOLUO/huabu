"""Application boundary for per-result user preference metadata."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Callable

from workbench.domain.execution import ResultSelection
from workbench.repositories.result_selection_repository import (
    ResultSelectionConflictError,
    ResultSelectionNotFoundError,
    ResultSelectionRepository,
    ResultSelectionStaleRevisionError,
)


class ResultSelectionServiceError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class ResultSelectionNotFoundServiceError(ResultSelectionServiceError):
    def __init__(self, selection_id: str):
        super().__init__("not_found", f"result selection not found: {selection_id}")


class ResultSelectionService:
    def __init__(self, repository: ResultSelectionRepository, *, actor_id: str, id_factory: Callable[[], str] | None = None, clock: Callable[[], datetime] | None = None):
        self._repository = repository
        self._actor_id = actor_id
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._clock = clock or (lambda: datetime.now(UTC))

    def create(self, *, run_id: str, attempt_id: str, output_name: str, ordinal: int, selected: bool = False, favorite: bool = False, rating: int | None = None, comment: str = "", metadata: dict[str, object] | None = None) -> ResultSelection:
        selection = ResultSelection(
            id=self._id_factory(), run_id=run_id, attempt_id=attempt_id, output_name=output_name,
            ordinal=ordinal, selected=selected, favorite=favorite, rating=rating, comment=comment,
            created_at=self._clock(), metadata=metadata or {},
        )
        try:
            return self._repository.create(selection, actor_id=self._actor_id)
        except ResultSelectionConflictError as error:
            raise ResultSelectionServiceError("conflict", str(error)) from error

    def get(self, selection_id: str) -> ResultSelection:
        try:
            return self._repository.get(selection_id, actor_id=self._actor_id)
        except ResultSelectionNotFoundError as error:
            raise ResultSelectionNotFoundServiceError(selection_id) from error

    def list_for_run(self, run_id: str) -> list[ResultSelection]:
        try:
            return self._repository.list_for_run(run_id, actor_id=self._actor_id)
        except ResultSelectionNotFoundError as error:
            raise ResultSelectionNotFoundServiceError(run_id) from error

    def update(self, selection_id: str, *, expected_revision: int, selected: bool, favorite: bool, rating: int | None, comment: str, metadata: dict[str, object] | None = None) -> ResultSelection:
        try:
            return self._repository.update(selection_id, expected_revision=expected_revision, actor_id=self._actor_id, selected=selected, favorite=favorite, rating=rating, comment=comment, metadata=metadata or {})
        except ResultSelectionNotFoundError as error:
            raise ResultSelectionNotFoundServiceError(selection_id) from error
        except ResultSelectionStaleRevisionError as error:
            raise ResultSelectionServiceError("stale_revision", str(error)) from error
