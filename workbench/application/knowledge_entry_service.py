"""Authorized application boundary for KnowledgeEntry persistence and queries."""

import uuid
from typing import Callable

from workbench.domain.knowledge import KnowledgeEntry, KnowledgeSourceScope
from workbench.repositories.knowledge_entry_repository import (
    KnowledgeEntryConflictError,
    KnowledgeEntryNotFoundError,
    SqliteKnowledgeEntryRepository,
)


class KnowledgeEntryServiceError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class KnowledgeEntryService:
    def __init__(self, repository: SqliteKnowledgeEntryRepository, *, actor_id: str, id_factory: Callable[[], str] | None = None):
        self._repository = repository
        self._actor_id = actor_id
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)

    def create(
        self, *, project_id: str, content: str | None, structured_payload: dict | None,
        source_refs: tuple[str, ...], tags: tuple[str, ...], scope: KnowledgeSourceScope,
        metadata: dict,
    ) -> KnowledgeEntry:
        try:
            entry = KnowledgeEntry(
                id=self._id_factory(), project_id=project_id, content=content,
                structured_payload=structured_payload, source_refs=source_refs,
                tags=tags, scope=scope, metadata=metadata,
            )
            return self._repository.create(entry, actor_id=self._actor_id)
        except (ValueError, KnowledgeEntryConflictError) as error:
            raise KnowledgeEntryServiceError("invalid_request", str(error)) from error

    def get(self, entry_id: str) -> KnowledgeEntry:
        try:
            return self._repository.get(entry_id, actor_id=self._actor_id)
        except KnowledgeEntryNotFoundError as error:
            raise KnowledgeEntryServiceError("not_found", str(error)) from error

    def list(self, *, project_id: str, query: str | None = None, tag: str | None = None, scope: str | None = None) -> list[KnowledgeEntry]:
        return self.search(project_id=project_id, query=query, tag=tag, scope=scope)

    def search(
        self, *, project_id: str, query: str | None = None, tag: str | None = None,
        scope: str | None = None, source_ref: str | None = None,
    ) -> list[KnowledgeEntry]:
        """Single authorized retrieval boundary for Skills and Agent callers."""
        return self._repository.search(
            project_id, actor_id=self._actor_id, query=query, tag=tag,
            scope=scope, source_ref=source_ref,
        )
