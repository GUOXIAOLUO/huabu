"""Application service for generic Catalog commands and versioned items."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Callable

from workbench.domain.catalog import Catalog, CatalogItem, CatalogItemVersion, CatalogMediaRef, CatalogSchema, validate_item_attributes
from workbench.repositories.catalog_repository import CatalogItemNotFoundError, CatalogNotFoundError, CatalogRepository, CatalogConflictError


class CatalogServiceError(ValueError):
    def __init__(self, code: str, message: str): self.code = code; super().__init__(message)


class CatalogService:
    def __init__(self, repository: CatalogRepository, *, actor_id: str, id_factory: Callable[[], str] | None = None, clock: Callable[[], datetime] | None = None):
        self._repository, self._actor_id = repository, actor_id
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._clock = clock or (lambda: datetime.now(UTC))

    def list(self, *, workspace_id: str, project_id: str | None = None) -> list[Catalog]:
        return self._repository.list(workspace_id=workspace_id, project_id=project_id, actor_id=self._actor_id)

    def get(self, catalog_id: str) -> Catalog:
        try: return self._repository.get(catalog_id, actor_id=self._actor_id)
        except CatalogNotFoundError as error: raise CatalogServiceError("not_found", str(error)) from error

    def create(self, *, workspace_id: str, project_id: str | None, scope: str, name: str, schema: CatalogSchema, metadata: dict[str, Any]) -> Catalog:
        try:
            catalog = Catalog(id=self._id_factory(), workspace_id=workspace_id, project_id=project_id, scope=scope, name=name, catalog_schema=schema, metadata=metadata)
            return self._repository.create(catalog, actor_id=self._actor_id)
        except (ValueError, CatalogConflictError) as error: raise CatalogServiceError("invalid_request", str(error)) from error

    def create_item(self, catalog_id: str, *, title: str, attributes: dict[str, Any], media_refs: tuple[CatalogMediaRef, ...], metadata: dict[str, Any]) -> tuple[Catalog, CatalogItem, CatalogItemVersion]:
        catalog = self.get(catalog_id)
        try: validate_item_attributes(catalog.catalog_schema, attributes)
        except ValueError as error: raise CatalogServiceError("invalid_request", str(error)) from error
        item = CatalogItem(id=self._id_factory(), catalog_id=catalog.id, title=title, metadata=metadata)
        version = CatalogItemVersion(id=self._id_factory(), catalog_id=catalog.id, item_id=item.id, ordinal=1, attributes=attributes, media_refs=media_refs, created_at=self._clock(), metadata={})
        return self._repository.create_item(catalog, item, version, actor_id=self._actor_id)

    def append_version(self, catalog_id: str, item_id: str, *, attributes: dict[str, Any], media_refs: tuple[CatalogMediaRef, ...], metadata: dict[str, Any]) -> CatalogItemVersion:
        catalog = self.get(catalog_id)
        try:
            item = self._repository.get_item(item_id, actor_id=self._actor_id)
            validate_item_attributes(catalog.catalog_schema, attributes)
        except CatalogItemNotFoundError as error: raise CatalogServiceError("not_found", str(error)) from error
        except ValueError as error: raise CatalogServiceError("invalid_request", str(error)) from error
        if item.catalog_id != catalog.id: raise CatalogServiceError("conflict", "catalog item does not belong to catalog")
        version = CatalogItemVersion(id=self._id_factory(), catalog_id=catalog.id, item_id=item.id, ordinal=len(item.version_ids) + 1, attributes=attributes, media_refs=media_refs, created_at=self._clock(), metadata=metadata)
        try:
            return self._repository.append_version(catalog, item, version, actor_id=self._actor_id)
        except CatalogConflictError as error: raise CatalogServiceError("conflict", str(error)) from error

    def list_versions(self, item_id: str) -> list[CatalogItemVersion]:
        try: return self._repository.list_versions(item_id, actor_id=self._actor_id)
        except CatalogItemNotFoundError as error: raise CatalogServiceError("not_found", str(error)) from error

    def get_item(self, item_id: str) -> CatalogItem:
        try: return self._repository.get_item(item_id, actor_id=self._actor_id)
        except CatalogItemNotFoundError as error: raise CatalogServiceError("not_found", str(error)) from error

    def list_items(self, catalog_id: str) -> list[CatalogItem]:
        try: return self._repository.list_items(catalog_id, actor_id=self._actor_id)
        except (CatalogNotFoundError, CatalogItemNotFoundError) as error: raise CatalogServiceError("not_found", str(error)) from error
