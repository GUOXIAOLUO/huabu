"""Controlled project context assembly over canonical read services."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Callable, Iterable, Protocol
import uuid

from workbench.application.entity_service import EntityService
from workbench.application.knowledge_entry_service import KnowledgeEntryService
from workbench.domain.knowledge import (
    KnowledgeSnapshot,
    ProjectKnowledgeContext,
    ProjectKnowledgeContextPolicy,
    ProjectKnowledgeContextResource,
    ProjectKnowledgeContextSnapshotRef,
)


class ProjectResourceReader(Protocol):
    def __call__(self, project_id: str) -> Iterable[ProjectKnowledgeContextResource]: ...


class ProjectKnowledgeContextService:
    """The sole composition boundary for Skill/Agent project context reads."""

    def __init__(
        self,
        *,
        entity_service: EntityService,
        knowledge_service: KnowledgeEntryService,
        resource_readers: Iterable[ProjectResourceReader] = (),
        id_factory: Callable[[], str] | None = None,
        clock: Callable[[], datetime] | None = None,
    ):
        self._entities = entity_service
        self._knowledge = knowledge_service
        self._resource_readers = tuple(resource_readers)
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._clock = clock or (lambda: datetime.now(UTC))

    def build(
        self, *, project_id: str, policy: ProjectKnowledgeContextPolicy | None = None,
    ) -> ProjectKnowledgeContext:
        selected_policy = policy or ProjectKnowledgeContextPolicy()
        entities = tuple(self._entities.list(project_id))[:selected_policy.max_entities] if selected_policy.include_entities else ()
        knowledge_by_id = {}
        for scope in selected_policy.knowledge_scopes:
            for entry in self._knowledge.search(project_id=project_id, scope=scope):
                knowledge_by_id.setdefault(entry.id, entry)
        knowledge = tuple(knowledge_by_id.values())[:selected_policy.max_knowledge]
        resources = ()
        if selected_policy.include_resources:
            collected = []
            for reader in self._resource_readers:
                collected.extend(
                    resource for resource in reader(project_id)
                    if resource.scope in selected_policy.resource_scopes
                )
            resources = tuple(collected)[:selected_policy.max_resources]
        refs = tuple(self._entity_ref(entity) for entity in entities)
        refs += tuple(self._knowledge_ref(entry) for entry in knowledge)
        refs += tuple(self._resource_ref(resource) for resource in resources)
        return ProjectKnowledgeContext(
            project_id=project_id, policy=selected_policy, generated_at=self._clock(),
            entities=entities, knowledge=knowledge, resources=resources,
            snapshot_refs=refs,
            metadata={"source": "project_knowledge_context"},
        )

    def snapshot(
        self, *, project_id: str, policy: ProjectKnowledgeContextPolicy | None = None,
    ) -> KnowledgeSnapshot:
        context = self.build(project_id=project_id, policy=policy)
        captured_at = self._clock()
        payload = context.model_dump(mode="python")
        payload["schema_version"] = "workbench.knowledge-snapshot/1"
        return KnowledgeSnapshot(
            **payload, snapshot_id=self._id_factory(), captured_at=captured_at,
        )

    @staticmethod
    def _entity_ref(entity) -> ProjectKnowledgeContextSnapshotRef:
        return ProjectKnowledgeContextSnapshotRef(
            kind="entity", ref_id=entity.id, version_id=entity.current_version_id,
            scope="project", provenance=entity.version_ids,
        )

    @staticmethod
    def _knowledge_ref(entry) -> ProjectKnowledgeContextSnapshotRef:
        return ProjectKnowledgeContextSnapshotRef(
            kind="knowledge", ref_id=entry.id, scope=entry.scope,
            provenance=entry.source_refs,
        )

    @staticmethod
    def _resource_ref(resource) -> ProjectKnowledgeContextSnapshotRef:
        return ProjectKnowledgeContextSnapshotRef(
            kind="resource", ref_id=resource.resource_id, version_id=resource.version_id,
            scope=resource.scope, provenance=resource.provenance,
        )
