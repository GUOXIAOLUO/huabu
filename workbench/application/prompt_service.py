"""Application boundary for versioned Prompt creation and resolution."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Callable

from workbench.domain.prompt import PromptDefinition, PromptVersion
from workbench.repositories.prompt_repository import PromptNotFoundError, PromptRepository, PromptVersionNotFoundError


class PromptServiceError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class PromptService:
    def __init__(self, repository: PromptRepository, *, actor_id: str, id_factory: Callable[[], str] | None = None, clock: Callable[[], datetime] | None = None):
        self._repository = repository
        self._actor_id = actor_id
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._clock = clock or (lambda: datetime.now(UTC))

    def create(self, *, project_id: str, name: str, content: str, description: str = "", metadata: dict[str, Any] | None = None) -> PromptDefinition:
        definition = PromptDefinition(id=self._id_factory(), project_id=project_id, name=name, description=description, metadata=metadata or {})
        version = PromptVersion(prompt_id=definition.id, version=1, content=content, created_by=self._actor_id, created_at=self._clock())
        return self._repository.create(definition, version, actor_id=self._actor_id)

    def get(self, prompt_id: str) -> PromptDefinition:
        try: return self._repository.get(prompt_id, actor_id=self._actor_id)
        except PromptNotFoundError as error: raise PromptServiceError("not_found", str(error)) from error

    @property
    def repository(self) -> PromptRepository:
        return self._repository

    def resolve(self, prompt_id: str, version: int) -> PromptVersion:
        try: return self._repository.resolve(prompt_id, version, actor_id=self._actor_id)
        except PromptVersionNotFoundError as error: raise PromptServiceError("version_not_found", str(error)) from error

    def create_version(self, prompt_id: str, *, content: str, metadata: dict[str, Any] | None = None) -> PromptVersion:
        try: return self._repository.create_version(prompt_id, content, metadata or {}, actor_id=self._actor_id)
        except PromptNotFoundError as error: raise PromptServiceError("not_found", str(error)) from error
