"""Authorized application boundary for Entity and EntityVersion writes/reads."""

import uuid
from datetime import UTC, datetime
from typing import Callable

from workbench.domain.entity import (
    EntityRecord,
    EntityVersion,
    EntityVersionLineage,
    EntityVersionPayload,
)
from workbench.repositories.entity_repository import (
    EntityNotFoundError,
    SqliteEntityRepository,
)


class EntityService:
    def __init__(
        self,
        repository: SqliteEntityRepository,
        *,
        actor_id: str,
        id_factory: Callable[[], str] | None = None,
        clock: Callable[[], datetime] | None = None,
    ):
        self._repository = repository
        self._actor_id = actor_id
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._clock = clock or (lambda: datetime.now(UTC))

    def list(self, project_id: str) -> list[EntityRecord]:
        return self._repository.list(project_id, actor_id=self._actor_id)

    def get(self, entity_id: str) -> EntityRecord:
        return self._repository.get(entity_id, actor_id=self._actor_id)

    def create(
        self,
        *,
        project_id: str,
        entity_type: str,
        definition_id: str,
        properties: dict,
        state: str = "draft",
        metadata: dict | None = None,
    ) -> EntityRecord:
        entity = EntityRecord(
            id=self._id_factory(),
            entity_type=entity_type,
            definition_id=definition_id,
            project_id=project_id,
            properties=properties,
            state=state,
            metadata=metadata or {},
        )
        return self._repository.create(entity, actor_id=self._actor_id)

    def create_with_version(
        self,
        *,
        project_id: str,
        entity_type: str,
        definition_id: str,
        payload: EntityVersionPayload,
        lineage: EntityVersionLineage | None = None,
        metadata: dict | None = None,
    ) -> tuple[EntityRecord, EntityVersion]:
        entity = EntityRecord(
            id=self._id_factory(),
            entity_type=entity_type,
            definition_id=definition_id,
            project_id=project_id,
            properties=payload.properties,
            state=payload.state,
            metadata=payload.metadata,
        )
        version = EntityVersion(
            id=self._id_factory(),
            entity_id=entity.id,
            project_id=project_id,
            ordinal=1,
            payload=payload,
            author_id=self._actor_id,
            created_at=self._clock(),
            lineage=lineage or EntityVersionLineage(),
            metadata=metadata or {},
        )
        return self._repository.create_with_version(entity, version, actor_id=self._actor_id)

    def append_version(
        self,
        *,
        entity_id: str,
        payload: EntityVersionPayload,
        lineage: EntityVersionLineage | None = None,
        metadata: dict | None = None,
    ) -> EntityVersion:
        entity = self.get(entity_id)
        versions = self._repository.list_versions(entity_id, actor_id=self._actor_id)
        parent = entity.current_version_id
        if lineage is None:
            lineage = EntityVersionLineage(parent_version_id=parent)
        elif lineage.parent_version_id is None and parent is not None:
            lineage = EntityVersionLineage(
                parent_version_id=parent,
                source_refs=lineage.source_refs,
                metadata=lineage.metadata,
            )
        version = EntityVersion(
            id=self._id_factory(),
            entity_id=entity.id,
            project_id=entity.project_id,
            ordinal=len(versions) + 1,
            payload=payload,
            author_id=self._actor_id,
            created_at=self._clock(),
            lineage=lineage,
            metadata=metadata or {},
        )
        return self._repository.append_version(version, actor_id=self._actor_id)

    def list_versions(self, entity_id: str) -> list[EntityVersion]:
        return self._repository.list_versions(entity_id, actor_id=self._actor_id)

    def get_version(self, entity_id: str, version_id: str) -> EntityVersion:
        return self._repository.get_version(entity_id, version_id, actor_id=self._actor_id)
