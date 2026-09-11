"""Application service for Collection commands and queries."""

from __future__ import annotations

import uuid
from typing import Any, Callable

from workbench.domain.collection import Collection, CollectionItem, CollectionSchema
from workbench.repositories.collection_repository import (
    CollectionNotFoundError,
    CollectionRepository,
    CollectionStaleRevisionError,
)


class CollectionServiceError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class CollectionNotFoundServiceError(CollectionServiceError):
    def __init__(self, collection_id: str):
        super().__init__("not_found", f"collection not found: {collection_id}")


class CollectionService:
    def __init__(self, repository: CollectionRepository, *, actor_id: str, id_factory: Callable[[], str] | None = None):
        self._repository = repository
        self._actor_id = actor_id
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)

    def list(self, project_id: str) -> list[Collection]:
        return self._repository.list(project_id, actor_id=self._actor_id)

    def get(self, collection_id: str) -> Collection:
        try:
            return self._repository.get(collection_id, actor_id=self._actor_id)
        except CollectionNotFoundError as error:
            raise CollectionNotFoundServiceError(collection_id) from error

    def create(self, *, project_id: str, name: str, schema: CollectionSchema, items: list[CollectionItem], default_view: dict[str, Any], metadata: dict[str, Any]) -> Collection:
        collection = Collection(id=self._id_factory(), project_id=project_id, name=name, schema=schema, items=items, default_view=default_view, metadata=metadata)
        return self._repository.create(collection, actor_id=self._actor_id)

    def update(self, collection_id: str, *, expected_revision: int, name: str | None = None, schema: CollectionSchema | None = None, items: list[CollectionItem] | None = None, default_view: dict[str, Any] | None = None, metadata: dict[str, Any] | None = None) -> Collection:
        current = self.get(collection_id)
        updated = current.model_copy(update={key: value for key, value in {
            "name": name, "collection_schema": schema, "items": items, "default_view": default_view, "metadata": metadata,
        }.items() if value is not None})
        try:
            return self._repository.replace(updated, expected_revision=expected_revision, actor_id=self._actor_id)
        except CollectionNotFoundError as error:
            raise CollectionNotFoundServiceError(collection_id) from error
        except CollectionStaleRevisionError as error:
            raise CollectionServiceError("stale_revision", str(error)) from error

    def delete(self, collection_id: str) -> None:
        try:
            self._repository.delete(collection_id, actor_id=self._actor_id)
        except CollectionNotFoundError as error:
            raise CollectionNotFoundServiceError(collection_id) from error
