"""Authorized application boundary for Artifact and ArtifactVersion writes/reads."""

import uuid
from datetime import UTC, datetime
from typing import Callable

from workbench.domain.artifact import Artifact, ArtifactVersion, ArtifactVersionContentRef, ArtifactVersionLineage, ArtifactType
from workbench.repositories.artifact_repository import SqliteArtifactRepository


class ArtifactService:
    def __init__(self, repository: SqliteArtifactRepository, *, actor_id: str, id_factory: Callable[[], str] | None = None, clock: Callable[[], datetime] | None = None):
        self._repository, self._actor_id = repository, actor_id
        self._id_factory, self._clock = id_factory or (lambda: uuid.uuid4().hex), clock or (lambda: datetime.now(UTC))

    def create(self, *, project_id: str, type: ArtifactType, title: str, metadata=None) -> Artifact:
        return self._repository.create_artifact(Artifact(id=self._id_factory(), project_id=project_id, type=type, title=title, metadata=metadata or {}), actor_id=self._actor_id)

    def get(self, artifact_id: str) -> Artifact: return self._repository.get_artifact(artifact_id, actor_id=self._actor_id)

    def list(self, project_id: str) -> list[Artifact]:
        return self._repository.list_artifacts(project_id, actor_id=self._actor_id)

    def append_version(self, *, artifact_id: str, content_ref: ArtifactVersionContentRef, lineage: ArtifactVersionLineage, metadata=None) -> ArtifactVersion:
        artifact = self.get(artifact_id)
        version = ArtifactVersion(id=self._id_factory(), artifact_id=artifact.id, project_id=artifact.project_id, ordinal=len(artifact.version_ids) + 1, content_ref=content_ref, lineage=lineage, created_at=self._clock(), metadata=metadata or {})
        return self._repository.append_version(version, actor_id=self._actor_id)

    def create_with_version(self, *, project_id: str, type: ArtifactType, title: str,
                            content_ref: ArtifactVersionContentRef,
                            lineage: ArtifactVersionLineage, metadata=None,
                            version_metadata=None) -> tuple[Artifact, ArtifactVersion]:
        artifact = Artifact(id=self._id_factory(), project_id=project_id, type=type,
                            title=title, metadata=metadata or {})
        version = ArtifactVersion(
            id=self._id_factory(), artifact_id=artifact.id, project_id=project_id,
            ordinal=1, content_ref=content_ref, lineage=lineage,
            created_at=self._clock(), metadata=version_metadata or {},
        )
        return self._repository.create_artifact_with_version(
            artifact, version, actor_id=self._actor_id,
        )

    def list_versions(self, artifact_id: str) -> list[ArtifactVersion]: return self._repository.list_versions(artifact_id, actor_id=self._actor_id)
