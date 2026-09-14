"""Authorized application queries and creation boundary for EntityRelations."""

import uuid
from typing import Callable

from workbench.domain.entity import EntityRelation, EntityRelationEndpoint
from workbench.repositories.entity_relation_repository import SqliteEntityRelationRepository


class EntityRelationService:
    def __init__(self, repository: SqliteEntityRelationRepository, *, actor_id: str, id_factory: Callable[[], str] | None = None):
        self._repository = repository
        self._actor_id = actor_id
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)

    def create(
        self,
        *,
        project_id: str,
        relation_type: str,
        from_endpoint: EntityRelationEndpoint,
        to_endpoint: EntityRelationEndpoint,
        revision: int = 1,
        metadata: dict | None = None,
    ) -> EntityRelation:
        relation = EntityRelation(
            id=self._id_factory(), project_id=project_id, relation_type=relation_type,
            from_endpoint=from_endpoint, to_endpoint=to_endpoint,
            revision=revision, metadata=metadata or {},
        )
        return self._repository.create(relation, actor_id=self._actor_id)

    def get(self, relation_id: str) -> EntityRelation:
        return self._repository.get(relation_id, actor_id=self._actor_id)

    def list(self, project_id: str) -> list[EntityRelation]:
        return self._repository.list(project_id, actor_id=self._actor_id)

    def query(self, project_id: str, *, relation_type: str | None = None, resource_type: str | None = None, resource_id: str | None = None) -> list[EntityRelation]:
        return self._repository.query(
            project_id, actor_id=self._actor_id, relation_type=relation_type,
            resource_type=resource_type, resource_id=resource_id,
        )
